# handlers/user.py
"""
User panel handlerlari
"""

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import date

from database import db
import config
from keyboards import user_main_menu, user_tasks_keyboard, task_action_keyboard, back_to_tasks_keyboard
from utils import format_user_tasks_message, format_task_completion_caption

router = Router()

# FSM States
class TaskCompletionStates(StatesGroup):
    waiting_for_media = State()

# Global bot obyekti (bot.py dan uzatiladi)
# bot_instance = None

# def set_bot(bot: Bot):
    # """Bot obyektini o'rnatish"""
    # global bot_instance
    # bot_instance = bot

# Middleware - faqat oddiy userlarga ruxsat
@router.message.middleware()
@router.callback_query.middleware()
async def user_only_middleware(handler, event, data):
    """Faqat ro'yxatdan o'tgan userlar uchun"""
    user_id = event.from_user.id
    user = db.get_user_by_telegram_id(user_id)
    
    if user and not user[8]:  # is_admin emas
        return await handler(event, data)
    else:
        if isinstance(event, Message):
            await event.answer("⛔️ Siz tizimda ro'yxatdan o'tmagansiz!")
        return

# ===== VAZIFALAR RO'YXATI =====

@router.message(F.text == "📋 Vazifalar ro'yxati")
async def show_tasks(message: Message):
    """Bugungi vazifalarni ko'rsatish"""
    user_id = message.from_user.id
    user = db.get_user_by_telegram_id(user_id)
    
    if not user:
        await message.answer("<b>❌ Xatolik yuz berdi.</b> /start ni bosib qaytadan kiriting.")
        return
    
    today = date.today()
    tasks = db.get_user_tasks(user[0], today)
    
    if not tasks:
        await message.answer(
            "✅ Bugun sizga vazifa tayinlanmagan!",
            reply_markup=user_main_menu()
        )
        return
    
    # Vazifalar xabarini yaratish
    tasks_message = format_user_tasks_message(user, tasks, today)
    
    await message.answer(
        tasks_message,
        reply_markup=user_tasks_keyboard(tasks)
    )

@router.callback_query(F.data == "refresh_tasks")
async def refresh_tasks(callback: CallbackQuery):
    """Vazifalarni yangilash"""
    user_id = callback.from_user.id
    user = db.get_user_by_telegram_id(user_id)
    
    today = date.today()
    tasks = db.get_user_tasks(user[0], today)
    
    if not tasks:
        await callback.message.edit_text(
            "✅ Bugun sizga vazifa tayinlanmagan!",
            reply_markup=None
        )
        await callback.answer("Yangilandi!")
        return
    
    tasks_message = format_user_tasks_message(user, tasks, today)
    new_btn = user_tasks_keyboard(tasks)
    if callback.message.reply_markup != new_btn:
        try:
            await callback.message.edit_reply_markup(reply_markup=new_btn)
        except:
            pass
    await callback.answer("✅ Yangilandi!")

# ===== VAZIFA TANLASH =====

@router.callback_query(F.data.startswith("task_"))
async def select_task(callback: CallbackQuery):
    """Vazifani tanlash"""
    task_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    user = db.get_user_by_telegram_id(user_id)
    
    # Vazifa ma'lumotlarini olish
    task = db.get_task(task_id)
    if not task:
        await callback.answer("<b>❌ Vazifa topilmadi!</b>", show_alert=True)
        return
    
    # Bajarilganligini tekshirish
    today = date.today()
    tasks = db.get_user_tasks(user[0], today)
    completed = False
    
    for t_id, t_text, t_type, t_completed in tasks:
        if t_id == task_id:
            completed = t_completed
            break
    
    task_id, task_text, task_type, role_name, filial_name = task
    
    status = "✅ Bajarilgan" if completed else "❗ Bajarilmagan"
    
    await callback.message.edit_text(
        f"<b>📝 VAZIFA MA'LUMOTLARI</b>\n\n"
        f"🎭 Rol: {role_name}\n"
        f"🏪 Filial: {filial_name}\n"
        f"📋 Vazifa: {task_text}\n\n"
        f"📊 Holat: {status}\n\n"
        f"{'✅ Bu vazifa allaqachon bajarilgan.' if completed else '📎 Bajarilgan ishni tasdiqlovchi fayl yuboring.'}",
        reply_markup=task_action_keyboard(task_id, completed)
    )
    await callback.answer()

@router.callback_query(F.data == "already_completed")
async def already_completed(callback: CallbackQuery):
    """Allaqachon bajarilgan"""
    await callback.answer("✅ Bu vazifa allaqachon bajarilgan!", show_alert=True)

@router.callback_query(F.data == "back_to_tasks")
async def back_to_tasks(callback: CallbackQuery):
    """Vazifalar ro'yxatiga qaytish"""
    user_id = callback.from_user.id
    user = db.get_user_by_telegram_id(user_id)
    
    today = date.today()
    tasks = db.get_user_tasks(user[0], today)
    
    tasks_message = format_user_tasks_message(user, tasks, today)
    
    await callback.message.edit_text(
        tasks_message,
        reply_markup=user_tasks_keyboard(tasks)
    )
    await callback.answer()

# ===== VAZIFANI BAJARISH =====

@router.callback_query(F.data.startswith("complete_"))
async def start_task_completion(callback: CallbackQuery, state: FSMContext):
    """Vazifani bajarish jarayonini boshlash"""
    task_id = int(callback.data.split("_")[1])
    
    await state.update_data(task_id=task_id)
    await state.set_state(TaskCompletionStates.waiting_for_media)
    
    await callback.message.edit_text(
        "<b>📎 VAZIFANI BAJARISH</b>\n\n"
        "Iltimos, bajarilgan ishni tasdiqlovchi\n"
        "fayl yuboring:\n\n"
        "✅ Video\n"
        "✅ Rasm\n"
        "✅ Audio/Voice\n"
        "✅ Hujjat\n"
        "✅ Matn xabari\n\n"
        "📌 Har qanday formatdagi fayl qabul qilinadi."
    )
    await callback.answer()

@router.message(TaskCompletionStates.waiting_for_media)
async def process_task_completion(message: Message, state: FSMContext, bot:Bot):
    """Yuborilgan faylni qabul qilish va guruhga yuborish"""
    
    # if not bot_instance:
    #     await message.answer("❌ Bot xatolik yuz berdi. /start ni bosib qaytadan urinib ko'ring.")
    #     await state.clear()
    #     return
    
    data = await state.get_data()
    task_id = data['task_id']
    
    user_id = message.from_user.id
    user = db.get_user_by_telegram_id(user_id)
    
    if not user:
        await message.answer("❌ Xatolik yuz berdi.")
        await state.clear()
        return
    
    # Vazifa ma'lumotlarini olish
    task = db.get_task(task_id)
    if not task:
        await message.answer("❌ Vazifa topilmadi!")
        await state.clear()
        return
    
    task_id, task_text, task_type, role_name, filial_name = task
    
    # Guruh chat_id ni olish
    # group_chat_id = db.get_group_chat_id(user[4])  # filial_id
    group_chat_id = config.GROUP_LINKS[int(user[4])]  # filial_id
    
    if not group_chat_id:
        await message.answer("❌ Guruh topilmadi!")
        await state.clear()
        return
    
    # Caption tayyorlash
    caption = format_task_completion_caption(user, task_text)
    
    # Media turini aniqlash va guruhga yuborish
    media_type = None
    media_file_id = None
    text_message = None
    
    try:
        if message.video:
            media_type = "video"
            media_file_id = message.video.file_id
            await bot.send_video(
                chat_id=group_chat_id,
                video=message.video.file_id,
                caption=caption
            )
        elif message.photo:
            media_type = "photo"
            media_file_id = message.photo[-1].file_id
            await bot.send_photo(
                chat_id=group_chat_id,
                photo=message.photo[-1].file_id,
                caption=caption
            )
        elif message.voice:
            media_type = "voice"
            media_file_id = message.voice.file_id
            await bot.send_voice(
                chat_id=group_chat_id,
                voice=message.voice.file_id,
                caption=caption
            )
        elif message.audio:
            media_type = "audio"
            media_file_id = message.audio.file_id
            await bot.send_audio(
                chat_id=group_chat_id,
                audio=message.audio.file_id,
                caption=caption
            )
        elif message.document:
            media_type = "document"
            media_file_id = message.document.file_id
            await bot.send_document(
                chat_id=group_chat_id,
                document=message.document.file_id,
                caption=caption
            )
        elif message.text:
            media_type = "text"
            text_message = message.text
            await bot.send_message(
                chat_id=group_chat_id,
                text=f"{caption}\n\n💬 Xabar: {message.text}"
            )
        else:
            await message.answer(
                "❌ Noto'g'ri fayl turi!\n\n"
                "Iltimos, video, rasm, audio, hujjat yoki matn yuboring."
            )
            return
        
        # Vazifani bajarildi deb belgilash
        db.complete_task(task_id, user[0], media_type, media_file_id, text_message)
        
        # Userga tasdiqlash
        await message.answer(
            "<b>✅ QABUL QILINDI!</b>\n\n"
            "Vazifa bajarildi deb belgilandi.\n"
            "Guruhga yuborildi: ✔️",
            reply_markup=back_to_tasks_keyboard()
        )
        
        await state.clear()
        
    except Exception as e:
        await message.answer(
            f"<b>❌ Guruhga yuborishda xatolik:</b>\n<i>{str(e)}</i>\n\n"
            f"Botni guruhga qo'shganingizga ishonch hosil qiling!"
        )
        await state.clear()

# ===== STATISTIKA =====

@router.message(F.text == "📊 Mening statistikam")
async def my_statistics(message: Message):
    """User statistikasi"""
    await message.answer(
        "<b>📊 MENING STATISTIKAM</b>\n\n"
        "Bu bo'lim ishlab chiqilmoqda...\n\n"
        "Hozircha admin sizning ishlayotganingizni\n"
        "har kuni guruhdan ko'rib turadi."
    )

# ===== MA'LUMOT =====

@router.message(F.text == "ℹ️ Ma'lumot")
async def user_info(message: Message):
    """User haqida ma'lumot"""
    user_id = message.from_user.id
    user = db.get_user_by_telegram_id(user_id)
    
    if not user:
        await message.answer("❌ Xatolik yuz berdi.")
        return
    
    from utils import format_phone
    
    await message.answer(
        f"<b>ℹ️ MENING MA'LUMOTLARIM</b>\n\n"
        f"👤 Ism: {user[2]}\n"
        f"📱 Telefon: {format_phone(user[3])}\n"
        f"🏪 Filial: {user[5]}\n"
        f"🎭 Rol: {user[7]}\n\n"
        f"📋 Vazifalaringizni ko'rish uchun\n"
        f"'Vazifalar ro'yxati' tugmasini bosing."
    )

# ===== ASOSIY MENYU =====

@router.callback_query(F.data == "user_main_menu")
async def user_main_menu_callback(callback: CallbackQuery):
    """Asosiy menyuga qaytish"""
    await callback.message.delete()
    await callback.message.answer(
        "<b>🏠 Asosiy menyu</b>",
        reply_markup=user_main_menu()
    )
    await callback.answer()