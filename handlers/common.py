# handlers/common.py
"""
Umumiy handlerlar - start, login
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import db
import config
from keyboards import admin_main_menu, user_main_menu, phone_ask

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Start komandasi - login"""
    await state.clear()
    
    telegram_id = message.from_user.id
    
    # Avval telegram_id orqali tekshirish
    user = db.get_user_by_telegram_id(telegram_id)
    
    if user:
        # User allaqachon tizimda
        # is_admin = user[8]
        is_admin = config.ADMIN == user[1]
        
        if is_admin:
            await message.answer(
                f"Assalomu alaykum, {user[2]}!\n\n"
                "🔑 Admin paneliga xush kelibsiz.",
                reply_markup=admin_main_menu()
            )
        else:
            await message.answer(
                f"Assalomu alaykum, {user[2]}!\n\n"
                f"🏪 Filial: {user[5]}\n"
                f"🎭 Rol: {user[7]}\n\n"
                """Vazifalaringizni ko'rish uchun menyudan <b>"📋 Vazifalar ro'yxati"</b> ni tanlang.""",
                reply_markup=user_main_menu()
            )
    else:
        # Yangi user - telefon so'rash
        await message.answer(
            "Assalomu alaykum! 👋\n\n"
            'Tizimga kirish uchun telefon raqamingizni yuboring yoki, <b>"📞 Kontakt yuborish"</b> tugmasini bosing.\n\n'
            "📝 Format: 998XXXXXXXXX (+ belgisisiz)\n"
            "📌 Misol: 998901234567", reply_markup=phone_ask
        )


@router.message(F.text.regexp(r'^998\d{9}$'))
async def process_phone_login(message: Message):
    """Telefon orqali login"""
    phone = int(message.text)
    telegram_id = message.from_user.id
    
    # Telefon orqali userni topish
    user = db.get_user_by_phone(phone)
    
    if user:
        # User mavjud - telegram_id ni yangilash
        db.update_user_telegram_id(phone, telegram_id)
        
        is_admin = user[8]
        
        if is_admin:
            await message.answer(
                f"✅ Muvaffaqiyatli kirdingiz!\n\n"
                f"👤 {user[2]}\n"
                f"🔑 Admin",
                reply_markup=admin_main_menu()
            )
        else:
            await message.answer(
                f"✅ Muvaffaqiyatli kirdingiz!\n\n"
                f"👤 {user[2]}\n"
                f"🏪 Filial: {user[5]}\n"
                f"🎭 Rol: {user[7]}",
                reply_markup=user_main_menu()
            )
    else:
        await message.answer(
            "❌ Bu telefon raqami tizimda ro'yxatdan o'tmagan.\n\n"
            "Iltimos, admin bilan bog'laning yoki to'g'ri raqam kiriting."
        )


@router.message(F.text=="/admin_panel")
async def process_phone_login(message: Message):
    telegram_id = message.from_user.id
    
    # Telegram orqali userni topish
    user = db.get_user_by_telegram_id(telegram_id)
    
    if user:
        is_admin = user[8]
        
        if is_admin:
            await message.answer(
                f"✅ Muvaffaqiyatli kirdingiz!\n\n"
                f"👤 {user[2]}\n"
                f"🔑 Admin",
                reply_markup=admin_main_menu()
            )
        else:
            await message.answer("❌ <b>Sizda admin huquqlari mavjud emas!</b>")
    else:
        await message.answer(
            "❌ Siz hali tizimda ro'yxatdan o'tmagansiz.\n\n"
            "Iltimos, admin bilan bog'laning."
        )


@router.message(F.contact)
async def get_contact(message:Message):
    """Telefon orqali login"""
    phone = int(message.contact.phone_number)
    telegram_id = message.from_user.id
    
    # Telefon orqali userni topish
    user = db.get_user_by_phone(phone)
    
    if user:
        # User mavjud - telegram_id ni yangilash
        db.update_user_telegram_id(phone, telegram_id)
        
        is_admin = user[8]
        
        if is_admin:
            await message.answer(
                f"✅ Muvaffaqiyatli kirdingiz!\n\n"
                f"👤 {user[2]}\n"
                f"🔑 Admin",
                reply_markup=admin_main_menu()
            )
        else:
            await message.answer(
                f"✅ Muvaffaqiyatli kirdingiz!\n\n"
                f"👤 {user[2]}\n"
                f"🏪 Filial: {user[5]}\n"
                f"🎭 Rol: {user[7]}",
                reply_markup=user_main_menu()
            )
    else:
        await message.answer(
            "❌ Bu telefon raqami tizimda ro'yxatdan o'tmagan.\n\n"
            "Iltimos, admin bilan bog'laning yoki to'g'ri raqam kiriting."
        ) 