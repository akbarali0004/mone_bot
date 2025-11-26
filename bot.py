#!/usr/bin/env python3
# bot.py
"""
Workly Bot - Asosiy fayl
Vazifalarni boshqarish va nazorat qilish tizimi
"""

import asyncio
import logging
from logging.handlers import RotatingFileHandler
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
from database import db
from scheduler import setup_scheduler, stop_scheduler

# Handlerlarni import qilish
from handlers import router

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # logging.FileHandler('bot.log', encoding='utf-8'),
        RotatingFileHandler("bot.log", maxBytes=10_000_000, backupCount=5, encoding="utf-8" )
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Asosiy funksiya"""
    
    # Bot tokenini tekshirish
    if not config.BOT_TOKEN or len(config.BOT_TOKEN) < 25:
        logger.error("❌ BOT_TOKEN ni config.py da o'zgartiring!")
        return
    
    # Bot va Dispatcher yaratish
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # Bot obyektini user handlerga uzatish (guruhga yuborish uchun)
    # user.set_bot(bot)
    
    # Routerlarni ro'yxatdan o'tkazish
    dp.include_router(router)
    
    # Database ni tekshirish
    logger.info("📊 Database tekshirilmoqda...")
    filials = db.get_all_filials()
    roles = db.get_all_roles()
    logger.info(f"   ✅ Filiallar: {len(filials)} ta")
    logger.info(f"   ✅ Rollar: {len(roles)} ta")
    
    # Schedulerni ishga tushirish
    logger.info("⏰ Scheduler sozlanmoqda...")
    setup_scheduler(bot)
    
    # Bot ma'lumotlarini olish
    bot_info = await bot.get_me()
    logger.info(f"🤖 Bot ishga tushdi: @{bot_info.username}")
    logger.info(f"📝 Bot ID: {bot_info.id}")
    logger.info(f"👤 Bot nomi: {bot_info.first_name}")
    logger.info("=" * 50)
    logger.info("✅ Bot ishlayapti! To'xtatish uchun Ctrl+C bosing")
    logger.info("=" * 50)
    
    try:
        # Botni ishga tushirish
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    finally:
        # Tozalash
        logger.info("🛑 Bot to'xtatilmoqda...")
        await stop_scheduler()
        await bot.session.close()
        logger.info("✅ Bot to'xtatildi!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Keyboard interrupt - bot to'xtatildi!")
    except Exception as e:
        logger.error(f"❌ Xatolik: {e}", exc_info=True)