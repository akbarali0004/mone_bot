# scheduler.py
"""
Avtomatik xabarlar - kunlik statistika
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, date
from aiogram import Bot

from database import db
from utils import format_daily_statistics
import config

scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)

async def send_daily_statistics(bot: Bot):
    """Har kuni soat 00:00 da kunlik statistika yuborish"""
    
    # Kechagi sana
    yesterday = date.today() - timedelta(days=1)
    
    # Har bir filial uchun
    filials = db.get_all_filials()
    
    for filial_id, filial_name in filials:
        # Guruh chat_id ni olish
        group_chat_id = db.get_group_chat_id(filial_id)
        
        if not group_chat_id:
            print(f"⚠️ Filial {filial_name} uchun guruh topilmadi!")
            continue
        
        # Statistika ma'lumotlarini olish
        role_stats, user_stats = db.get_daily_statistics(filial_id, yesterday)
        
        if not user_stats:
            # Bu filialda ishchilar yo'q
            continue
        
        # Statistika xabarini yaratish
        stats_message = format_daily_statistics(
            filial_name, 
            role_stats, 
            user_stats, 
            yesterday
        )
        
        # Guruhga yuborish
        try:
            await bot.send_message(
                chat_id=group_chat_id,
                text=stats_message
            )
            print(f"✅ {filial_name} uchun statistika yuborildi")
        except Exception as e:
            print(f"❌ {filial_name} ga statistika yuborishda xatolik: {e}")

def setup_scheduler(bot: Bot):
    """Schedulerni sozlash"""
    
    # Har kuni soat 00:00 da
    scheduler.add_job(
        send_daily_statistics,
        trigger=CronTrigger(hour=0, minute=0),
        args=[bot],
        id='daily_statistics',
        name='Kunlik statistika yuborish',
        replace_existing=True
    )
    
    # Test uchun - har 10 daqiqada (ISHLATISHDAN OLDIN O'CHIRIB QO'YISH KERAK!)
    # scheduler.add_job(
    #     send_daily_statistics,
    #     trigger=CronTrigger(minute='*/10'),
    #     args=[bot],
    #     id='test_statistics',
    #     name='Test statistika',
    #     replace_existing=True
    # )
    
    print("✅ Scheduler sozlandi:")
    print("   - Kunlik statistika: Har kuni 00:00")
    
    scheduler.start()
    print("✅ Scheduler ishga tushdi!")

async def stop_scheduler():
    """Schedulerni to'xtatish"""
    try:
        if scheduler.running:
            await scheduler.shutdown(wait=True)
            print("🛑 Scheduler to'xtatildi!")
    except Exception as e:
        print(f"❌ Scheduler to'xtatishda xatolik: {e}")
