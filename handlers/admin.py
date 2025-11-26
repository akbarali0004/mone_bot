# handlers/admin.py
"""
Admin panel handlerlari - to'liq versiya
"""

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
import config
from keyboards import (
    admin_main_menu, admin_workers_menu, admin_tasks_menu,
    select_filial_keyboard, select_role_keyboard, 
    select_task_type_keyboard, confirm_keyboard, cancel_btn,
    admin_workers_list_menu, is_check, cancel_del_btn, admin_tasks_list_menu,
    admin_admins_menu, admin_admins_list_menu
)
from utils import format_phone

router = Router()

# ===== FSM STATES =====

class AddWorkerStates(StatesGroup):
    """Ishchi qo'shish states"""
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_filial = State()
    waiting_for_role = State()

class AddTaskStates(StatesGroup):
    """Vazifa qo'shish states"""
    waiting_for_filial = State()
    waiting_for_role = State()
    waiting_for_type = State()
    waiting_for_text = State()

class DeleteTaskStates(StatesGroup):
    """Vazifa o'chirish states"""
    waiting_for_task_id = State()

class DeleteWorkerStates(StatesGroup):
    """ishchi o'chirish states"""
    waiting_for_worker_phone = State()
    waiting_for_worker_check = State()


class AddAdminStates(StatesGroup):
    """Admin qo'shish states"""
    waiting_for_admin_phone = State()
    waiting_for_admin_check = State()


class DeleteAdminStates(StatesGroup):
    """ishchi o'chirish states"""
    waiting_for_admin = State()
    waiting_for_admin_phone = State()
    waiting_for_admin_check = State()


# ===== MIDDLEWARE - FAQAT ADMINLAR =====

@router.message.middleware()
@router.callback_query.middleware()
async def admin_only_middleware(handler, event, data):
    """Faqat adminlar uchun"""
    user_id = event.from_user.id
    user = db.get_user_by_telegram_id(user_id)
    
    if user and user[8]:  # is_admin
        return await handler(event, data)
    else:
        if isinstance(event, Message):
            await event.answer("⛔️ Bu bo'lim faqat adminlar uchun!")
        return

# ===== ASOSIY MENYU =====


@router.message(F.text == "👥 Ishchilar")
async def admin_workers_message(message: Message, state: FSMContext):
    await message.answer(
        "<b>👥 ISHCHILAR BOSHQARUVI</b>\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=admin_workers_menu()
    )


@router.callback_query(F.data.in_(["admin_back_list_main", "back_from_del_worker"]))
async def admin_workers_callback(call: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()

    if current_state == DeleteWorkerStates.waiting_for_worker_check.state:
        await call.message.delete()
        await call.message.answer(
            "<b>👥 ISHCHILAR BOSHQARUVI</b>\n\n"
            "Quyidagi amallardan birini tanlang:",
            reply_markup=admin_workers_menu()
        )

    elif current_state in (
        AddAdminStates.waiting_for_admin_check.state,
        DeleteAdminStates.waiting_for_admin.state,
        DeleteAdminStates.waiting_for_admin_phone.state
    ):
        await call.message.delete()
        await call.message.answer(
            "<b>👥 ADMINLAR BOSHQARUVI</b>\n\n"
            "Quyidagi amallardan birini tanlang:",
            reply_markup=admin_admins_menu()
        )

    else:
        await call.message.edit_text(
            "<b>👥 ISHCHILAR BOSHQARUVI</b>\n\n"
            "Quyidagi amallardan birini tanlang:",
            reply_markup=admin_workers_menu())



@router.message(F.text == "📋 Vazifalar")
async def admin_tasks(message: Message):
    """Vazifalar bo'limi"""
    await message.answer(
        "<b>📋 VAZIFALAR BOSHQARUVI</b>\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=admin_tasks_menu()
    )

@router.message(F.text == "📊 Statistika")
async def admin_statistics(message: Message):
    """Statistika bo'limi"""
    from datetime import date, timedelta
    
    # Kechagi statistika
    yesterday = date.today() - timedelta(days=1)
    
    message_text = "<b>📊 STATISTIKA</b>\n\n"
    message_text += "Qaysi filial uchun statistika ko'rmoqchisiz?\n\n"
    message_text += f"📅 Oxirgi hisobot: {yesterday.strftime('%d.%m.%Y')}\n"
    message_text += "⏰ Kunlik hisobot: Har kuni 00:00 da avtomatik yuboriladi"
    
    await message.answer(
        message_text,
        reply_markup=select_filial_keyboard("stats_filial")
    )

@router.callback_query(F.data.startswith("stats_filial_"))
async def show_filial_statistics(callback: CallbackQuery):
    """Filial statistikasini ko'rsatish"""
    from datetime import date, timedelta
    from utils import format_daily_statistics
    
    filial_id = int(callback.data.split("_")[-1])
    yesterday = date.today() - timedelta(days=1)
    
    filial = db.get_filial(filial_id)
    role_stats, user_stats = db.get_daily_statistics(filial_id, yesterday)
    
    if not user_stats:
        await callback.message.edit_text(
            f"📊 {filial[1]} - STATISTIKA\n\n"
            f"Bu filialda hali ishchilar yo'q yoki\n"
            f"kecha hech qanday vazifa bajarilmagan.",
            reply_markup=select_filial_keyboard("stats_filial")
        )
        await callback.answer()
        return
    
    stats_message = format_daily_statistics(filial[1], role_stats, user_stats, yesterday)
    
    # Telegram 4096 belgidan ko'p xabar yuborishni qabul qilmaydi
    if len(stats_message) > 4000:
        # Ikki qismga bo'lib yuborish
        await callback.message.answer(stats_message[:4000])
        await callback.message.answer(stats_message[4000:])
    else:
        await callback.message.edit_text(stats_message)
    
    await callback.answer("✅ Statistika ko'rsatildi")

@router.message(F.text == "⚙️ Sozlamalar")
async def admin_settings(message: Message):
    """Sozlamalar bo'limi"""
    filials = db.get_all_filials()
    roles = db.get_all_roles()
    users = db.get_all_users()
    tasks = db.get_all_tasks()
    admins = db.get_admins()
    
    filials_text = "\n".join([f"  {i}. {name}" for i, (_, name) in enumerate(filials, 1)])
    roles_text = "\n".join([f"  {i}. {name}" for i, (_, name) in enumerate(roles, 1)])
    
    # Admin raqamlari
    admins_text = "\n".join([f"  • {format_phone(admin[1])}" for admin in admins])
    
    # Guruh ID lari
    groups_info = []
    for filial_id, filial_name in filials:
        chat_id = db.get_group_chat_id(filial_id)
        groups_info.append(f"  • {filial_name}: {chat_id if chat_id else '❌ Guruh topilmadi'}")
    groups_text = "\n".join(groups_info)
    
    await message.answer(
        f"⚙️ <b>TIZIM SOZLAMALARI</b>\n\n"
        f"📊 <b>FILIALLAR</b> ({len(filials)} ta):\n{filials_text}\n\n"
        f"🎭 <b>ROLLAR</b> ({len(roles)} ta):\n{roles_text}\n\n"
        f"👥 <b>ISHCHILAR:</b> {len(users)} ta\n"
        f"📋 <b>VAZIFALAR:</b> {len(tasks)} ta\n\n"
        f"👨‍💼 <b>ADMINLAR</b> ({len(admins)} ta):\n{admins_text}\n\n"
        f"📱 <b>GURUHLAR:</b>\n{groups_text}\n\n"
        f"💾 <b>Database:</b> {config.DATABASE_NAME}\n"
        f"🕐 <b>Vaqt zonasi:</b> {config.TIMEZONE}"
    )

# ===== ISHCHI QO'SHISH =====

@router.callback_query(F.data == "admin_add_worker")
async def start_add_worker(callback: CallbackQuery, state: FSMContext):
    """Ishchi qo'shish boshlash"""
    await callback.message.edit_text(
        "➕ YANGI ISHCHI QO'SHISH\n\n"
        "1️⃣ Ishchining to'liq ismini kiriting:\n\n"
        "📝 Misol: Samandar Aliyev\n\n"
        "💡 Ism va familiyani to'liq yozing",
        reply_markup=cancel_btn
    )
    await state.set_state(AddWorkerStates.waiting_for_name)
    await callback.answer()


@router.message(AddWorkerStates.waiting_for_name)
async def process_worker_name(message: Message, state: FSMContext):
    """Ism qabul qilish"""
    full_name = message.text.strip()
    
    if len(full_name) < 3:
        await message.answer(
            "❌ Ism juda qisqa!\n\n"
            "Iltimos, to'liq ism va familiyani kiriting:"
        )
        return
    
    await state.update_data(full_name=full_name)
    await message.answer(
        f"✅ Ism: {full_name}\n\n"
        f"2️⃣ Telefon raqamini kiriting:\n\n"
        f"📝 Format: 998XXXXXXXXX (+ belgisisiz)\n"
        f"📌 Misol: 998901234567\n\n"
        f"⚠️ Faqat raqamlar, 12 ta belgi"
    )
    await state.set_state(AddWorkerStates.waiting_for_phone)

@router.message(AddWorkerStates.waiting_for_phone)
async def process_worker_phone(message: Message, state: FSMContext):
    """Telefon qabul qilish"""
    phone_text = message.text.strip()
    
    # Telefon formatini tekshirish
    if not phone_text.isdigit():
        await message.answer(
            "❌ Faqat raqamlar kiritilishi kerak!\n\n"
            "📝 To'g'ri format: 998901234567\n"
            "Qaytadan kiriting:"
        )
        return
    
    if len(phone_text) != 12:
        await message.answer(
            f"❌ Telefon 12 ta raqamdan iborat bo'lishi kerak!\n\n"
            f"Siz kiritdingiz: {len(phone_text)} ta raqam\n"
            f"📝 To'g'ri format: 998901234567\n"
            f"Qaytadan kiriting:"
        )
        return
    
    if not phone_text.startswith('998'):
        await message.answer(
            "❌ Telefon 998 bilan boshlanishi kerak!\n\n"
            "📝 To'g'ri format: 998901234567\n"
            "Qaytadan kiriting:"
        )
        return
    
    phone = int(phone_text)
    
    # Bunday telefon mavjudligini tekshirish
    existing_user = db.get_user_by_phone(phone)
    if existing_user:
        await message.answer(
            f"⚠️ Bu telefon raqami allaqachon ro'yxatdan o'tgan!\n\n"
            f"👤 Ism: {existing_user[2]}\n"
            f"🏪 Filial: {existing_user[5]}\n"
            f"🎭 Rol: {existing_user[7]}\n\n"
            f"Boshqa raqam kiriting:"
        )
        return
    
    await state.update_data(phone=phone)
    
    data = await state.get_data()
    await message.answer(
        f"✅ Ism: {data['full_name']}\n"
        f"✅ Telefon: {format_phone(phone)}\n\n"
        f"3️⃣ Filialni tanlang:",
        reply_markup=select_filial_keyboard("worker_filial")
    )
    await state.set_state(AddWorkerStates.waiting_for_filial)


@router.callback_query(F.data.startswith("worker_filial_"))
async def process_worker_filial(callback: CallbackQuery, state: FSMContext):
    """Filial tanlash"""
    filial_id = int(callback.data.split("_")[-1])
    await state.update_data(filial_id=filial_id)
    
    filial = db.get_filial(filial_id)
    data = await state.get_data()
    
    await callback.message.edit_text(
        f"✅ Ism: {data['full_name']}\n"
        f"✅ Telefon: {format_phone(data['phone'])}\n"
        f"✅ Filial: {filial[1]}\n\n"
        f"4️⃣ Rolni tanlang:",
        reply_markup=select_role_keyboard("worker_role")
    )
    await state.set_state(AddWorkerStates.waiting_for_role)
    await callback.answer()

@router.callback_query(F.data.startswith("worker_role_"))
async def process_worker_role(callback: CallbackQuery, state: FSMContext):
    """Rol tanlash va saqlash"""
    role_id = int(callback.data.split("_")[-1])
    
    data = await state.get_data()
    full_name = data['full_name']
    phone = data['phone']
    filial_id = data['filial_id']
    
    # Ishchini yaratish
    try:
        user_id = db.create_user(full_name, phone, filial_id, role_id, is_admin=False)
        
        filial = db.get_filial(filial_id)
        role = db.get_role(role_id)
        
        await callback.message.edit_text(
            f"<b>✅ ISHCHI MUVAFFAQIYATLI QO'SHILDI!</b>\n\n"
            f"👤 Ism: {full_name}\n"
            f"📱 Telefon: {format_phone(phone)}\n"
            f"🏪 Filial: {filial[1]}\n"
            f"🎭 Rol: {role[1]}\n"
            f"🆔 ID: {user_id}\n\n"
            f"📲 KEYINGI QADAM:\n"
            f"Ishchi botga /start buyrug'ini yuborishi\n"
            f"va {format_phone(phone)} raqamini kiritishi kerak.\n\n"
            f"✅ Shundan keyin u tizimga kira oladi!"
        )
        
        await state.clear()
        await callback.answer("✅ Ishchi qo'shildi!")
        
    except Exception as e:
        await callback.message.edit_text(
            f"<b>❌ XATOLIK!</b>\n\n"
            f"Ishchini qo'shishda muammo yuz berdi:\n"
            f"{str(e)}\n\n"
            f"Iltimos, qaytadan urinib ko'ring."
        )
        await state.clear()
        await callback.answer("❌ Xatolik!", show_alert=True)

# ===== ISHCHILAR RO'YXATI =====

@router.callback_query(F.data == "admin_list_workers")
async def list_workers(callback: CallbackQuery):
    """Barcha ishchilar ro'yxati"""
    users = db.get_all_users()
    
    if not users:
        await callback.message.edit_text(
            "📋 Hozircha ishchilar yo'q.\n\n"
            "➕ Ishchi qo'shish uchun tugmani bosing:",
            reply_markup=admin_workers_menu()
        )
        await callback.answer()
        return
    
    # Filial bo'yicha guruhlash
    users_by_filial = {}
    for user_id, name, phone, filial, role in users:
        if filial not in users_by_filial:
            users_by_filial[filial] = []
        users_by_filial[filial].append((user_id, name, phone, role))
    
    message = "<b>📋 ISHCHILAR RO'YXATI</b>\n\n"
    
    for filial, workers in users_by_filial.items():
        message += f"🏪 {filial} ({len(workers)} ta):\n"
        message += "━━━━━━━━━━━━━━━━━━━━\n"
        for user_id, name, phone, role in workers:
            message += f"👤 {name}\n"
            message += f"   🎭 {role}\n"
            message += f"   📱 {format_phone(phone)}\n"
            message += f"   🆔 ID: {user_id}\n\n"
    
    message += f"━━━━━━━━━━━━━━━━━━━━\n"
    message += f"📊 JAMI: {len(users)} ta ishchi"
    
    await callback.message.edit_text(message, reply_markup=admin_workers_list_menu())
    await callback.answer()


# ===== ISHCHI O'CHIRISH =====

@router.callback_query(F.data=="admin_delete_worker")
async def ask_del_woeker_phone(call:CallbackQuery, state:FSMContext):
    await call.message.delete()
    await call.message.answer(
        "<b>➖ O'chirmoqchi bolgan ishchi telefon nomerini yuboring</b>\n\n"
        "📝 Format: 998XXXXXXXXX (+ belgisisiz)\n"
        "📌 Misol: 998901234567\n\n"
        "⚠️ Faqat raqamlar, 12 ta belgi", reply_markup=cancel_del_btn)
    await state.set_state(DeleteWorkerStates.waiting_for_worker_phone)


@router.message(F.text.regexp(r'^998\d{9}$'), DeleteWorkerStates.waiting_for_worker_phone)
async def ask_del_worker_check(message:Message, state:FSMContext):
    user = db.get_user_by_phone(int(message.text))

    if not user:
        await message.answer(f"<b>📞 +{message.text} - Bu raqam bilan hech qanday ishchi topilmadi.</b>\n\n<i>Iltimos tekshirib qaytadan yuboring!</i>")
        return
    
    msg = f"<b>👤 {user[2]}</b>\n\n"
    msg += f"   🏪 {user[5]}\n"
    msg += f"   🎭 {user[7]}\n"
    msg += f"   📱 +{user[3]}\n"
    msg += f"   🆔 ID: {user[0]}\n\n"
    msg += "Haqiqatdan ham bu ishchini ochirmoqchimisz?"
    await message.answer(msg, reply_markup=is_check(user[0]))
    await state.set_state(DeleteWorkerStates.waiting_for_worker_check)


@router.callback_query(F.data.startswith("checked_"), DeleteWorkerStates.waiting_for_worker_check)
async def del_wrker(call:CallbackQuery, state:FSMContext):
    await call.message.delete()
    user_id = int(call.data.split("_")[1])
    db.delete_user(user_id)
    await call.answer("✅ Ishchi o'chirildi!")
    await call.message.answer("<b>🏠 ASOSIY MENYU</b>\n\nQuyidagilardan birini tanlang:", reply_markup=admin_workers_menu())


# ===== ADMIN QO'SHISH =====

@router.message(F.text == '👤 Adminlar')
async def admins_list(message:Message):
    await message.answer("<b>👤 ADMINLAR BOSHQARUVI</b>\n\nQuyidagi amallardan birini tanlang:", reply_markup=admin_admins_menu())


@router.callback_query(F.data=="admin_add_admin")
async def add_admin_1(call:CallbackQuery, state:FSMContext):
    await call.answer()
    await state.set_state(AddAdminStates.waiting_for_admin_phone)
    await call.message.answer(
        "<b>➕ YANGI ADMIN QO'SHISH</b>\n\n"
        "📞 Telefon raqamini kiriting:\n\n"
        "📝 Format: 998XXXXXXXXX (+ belgisisiz)\n"
        "📌 Misol: 998901234567\n\n"
        "⚠️ Faqat raqamlar, 12 ta belgi")
    

@router.message(F.text.regexp(r'^998\d{9}$'), AddAdminStates.waiting_for_admin_phone)
async def ask_add_admin_check(message:Message, state:FSMContext):
    user = db.get_user_by_phone(int(message.text))

    if not user:
        await message.answer(f"<b>📞 +{message.text} - Bu raqam bilan hech qanday ishchi topilmadi.</b>\n\n<i>Iltimos tekshirib qaytadan yuboring!</i>")
        return
    elif user[8]:
        await message.answer(f"<b>📞 +{message.text} - Bu raqam egasiga avvalroq admin huquqi berilgan.</b>\n\n<i>Orqaga qaytishingiz yoki boshqa raqam yuborishingiz mumkin!</i>", reply_markup=cancel_del_btn)
        return
    
    msg = f"<b>👤 {user[2]}</b>\n\n"
    msg += f"   🏪 {user[5]}\n"
    msg += f"   🎭 {user[7]}\n"
    msg += f"   📱 +{user[3]}\n"
    msg += f"   🆔 ID: {user[0]}\n\n"
    msg += "Haqiqatdan ham bu ishchiga <b>admin</b> huquqinin bermoqchimisz?"
    await message.answer(msg, reply_markup=is_check(user[3]))
    await state.set_state(AddAdminStates.waiting_for_admin_check)


@router.callback_query(F.data.startswith("checked_"), AddAdminStates.waiting_for_admin_check)
async def add_admin_check(call:CallbackQuery, state:FSMContext, bot:Bot):
    await call.message.delete()
    phone=int(call.data.split("_")[1])
    db.add_admin(phone)
    await call.answer("✅ Yangi admin qo'shildi!")
    user = db.get_user_by_phone(phone)
    await bot.send_message(user[1], f"<b>{user[2]}</b> - sizga admin huquqi berildi!\n\n<b>Istalgan paytda:</b>\n\n/admin_panel - <i>ni yuborish orqali admin panelga o'tishingiz mumkin.</i>\n\n/start - <i>buyrug'i bilan esa ishchi paneliga qaytishingiz mumkin.</i>")
    await call.message.answer("<b>🏠 ASOSIY MENYU</b>\n\nQuyidagilardan birini tanlang:", reply_markup=admin_main_menu())


@router.callback_query(F.data=="admin_list_admins")
async def get_admins_list(call:CallbackQuery, state:FSMContext):
    await call.answer()
    admins = db.get_admins()
    msg = "<b>📋 ADMINLAR RO'YXATI</b>\n\n"

    for admin in admins:
        msg += f"<b>{admin[0]}</b> - +{admin[1]}\n"

    msg += "\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📊 JAMI: <b>{len(admins)}</b> ta admin"

    await call.message.edit_text(msg, reply_markup=admin_admins_list_menu())
    await state.set_state(DeleteAdminStates.waiting_for_admin)


# ===== ADMIN O'CHIRISH =====

@router.callback_query(F.data=="admin_delete_admin")
async def ask_del_admin(call:CallbackQuery, state:FSMContext):
    await call.answer()
    await call.message.answer(
        "<b>➖ O'chirmoqchi bolgan admin telefon nomerini yuboring</b>\n\n"
        "📝 Format: 998XXXXXXXXX (+ belgisisiz)\n"
        "📌 Misol: 998901234567\n\n"
        "⚠️ Faqat raqamlar, 12 ta belgi", reply_markup=cancel_del_btn)
    await state.set_state(DeleteAdminStates.waiting_for_admin_phone)
    

@router.message(F.text.regexp(r'^998\d{9}$'), DeleteAdminStates.waiting_for_admin_phone)
async def ask_del_admin_check(message:Message, state:FSMContext):
    admin = db.get_admin_by_phone(int(message.text))

    if not admin:
        await message.answer(f"<b>📞 +{message.text} - Bu raqam bilan hech qanday admin topilmadi.</b>\n\n<i>Iltimos tekshirib qaytadan yuboring!</i>")
        return
    
    msg = f"<b>👤 {admin[0]}</b>\n\n"
    msg += f"   📱 +{admin[1]}\n\n"
    msg += "Haqiqatdan ham bu adminni ochirmoqchimisz?"
    await message.answer(msg, reply_markup=is_check(admin[1]))
    await state.set_state(DeleteAdminStates.waiting_for_admin_check)


@router.callback_query(F.data.startswith("checked_"), DeleteAdminStates.waiting_for_admin_check)
async def add_admin_check(call:CallbackQuery, state:FSMContext):
    await call.message.delete()
    user_id=int(call.data.split("_")[1])
    db.del_admin(user_id)
    await call.answer("✅ Admin o'chirildi!")
    await call.message.answer("<b>🏠 ASOSIY MENYU</b>\n\nQuyidagilardan birini tanlang:", reply_markup=admin_main_menu())


# ===== VAZIFA QO'SHISH =====

@router.callback_query(F.data == "admin_add_task")
async def start_add_task(callback: CallbackQuery, state: FSMContext):
    """Vazifa qo'shish boshlash"""
    await callback.message.edit_text(
        "<b>➕ YANGI VAZIFA QO'SHISH</b>\n\n"
        "1️⃣ Qaysi filial uchun vazifa qo'shmoqchisiz?\n\n"
        "Filialni tanlang:",
        reply_markup=select_filial_keyboard("task_filial")
    )
    await state.set_state(AddTaskStates.waiting_for_filial)
    await callback.answer()


@router.callback_query(F.data.startswith("task_filial_"))
async def process_task_filial(callback: CallbackQuery, state: FSMContext):
    """Vazifa uchun filial tanlash"""
    filial_id = int(callback.data.split("_")[-1])
    await state.update_data(filial_id=filial_id)
    
    filial = db.get_filial(filial_id)
    
    await callback.message.edit_text(
        f"✅ Filial: {filial[1]}\n\n"
        f"2️⃣ Qaysi rol uchun vazifa?\n\n"
        f"Rolni tanlang:",
        reply_markup=select_role_keyboard("task_role")
    )
    await state.set_state(AddTaskStates.waiting_for_role)
    await callback.answer()


@router.callback_query(F.data.startswith("task_role_"))
async def process_task_role(callback: CallbackQuery, state: FSMContext):
    """Vazifa uchun rol tanlash"""
    role_id = int(callback.data.split("_")[-1])
    await state.update_data(role_id=role_id)
    
    data = await state.get_data()
    filial = db.get_filial(data['filial_id'])
    role = db.get_role(role_id)
    
    await callback.message.edit_text(
        f"✅ Filial: {filial[1]}\n"
        f"✅ Rol: {role[1]}\n\n"
        f"3️⃣ Vazifa qanchalik tez-tez bajariladi?\n\n"
        f"Vazifa turini tanlang:",
        reply_markup=select_task_type_keyboard()
    )
    await state.set_state(AddTaskStates.waiting_for_type)
    await callback.answer()


@router.callback_query(F.data.startswith("tasktype_"))
async def process_task_type(callback: CallbackQuery, state: FSMContext):
    """Vazifa turini tanlash"""
    task_type = callback.data.split("_")[-1]
    await state.update_data(task_type=task_type)
    
    data = await state.get_data()
    filial = db.get_filial(data['filial_id'])
    role = db.get_role(data['role_id'])
    
    type_name = config.TASK_TYPES.get(task_type, task_type)
    
    await callback.message.edit_text(
        f"✅ Filial: {filial[1]}\n"
        f"✅ Rol: {role[1]}\n"
        f"✅ Tur: {type_name}\n\n"
        f"4️⃣ Vazifa matnini kiriting:\n\n"
        f"📝 Misol: Nonni tayyorlash\n"
        f"📝 Misol: Oshxonani tozalash\n\n"
        f"💡 Qisqa va aniq yozing"
    )
    await state.set_state(AddTaskStates.waiting_for_text)
    await callback.answer()


@router.message(AddTaskStates.waiting_for_text)
async def process_task_text(message: Message, state: FSMContext):
    """Vazifa matnini qabul qilish va saqlash"""
    task_text = message.text.strip()
    
    if len(task_text) < 3:
        await message.answer(
            "❌ Vazifa matni juda qisqa!\n\n"
            "Iltimos, vazifani aniqroq yozing:"
        )
        return
    
    data = await state.get_data()
    filial_id = data['filial_id']
    role_id = data['role_id']
    task_type = data['task_type']
    
    # Vazifani saqlash
    try:
        task_id = db.create_task(task_text, task_type, role_id, filial_id)
        
        filial = db.get_filial(filial_id)
        role = db.get_role(role_id)
        type_name = config.TASK_TYPES.get(task_type, task_type)
        
        await message.answer(
            f"✅ VAZIFA MUVAFFAQIYATLI QO'SHILDI!\n\n"
            f"🏪 Filial: {filial[1]}\n"
            f"🎭 Rol: {role[1]}\n"
            f"📅 Tur: {type_name}\n"
            f"📝 Vazifa: {task_text}\n"
            f"🆔 ID: {task_id}\n\n"
            f"✅ Endi bu vazifa avtomatik ravishda\n"
            f"tegishli ishchilarga ko'rsatiladi!",
            reply_markup=admin_main_menu()
        )
        
        await state.clear()
        
    except Exception as e:
        await message.answer(
            f"<b>❌ XATOLIK!</b>\n\n"
            f"Vazifani saqlashda muammo:\n"
            f"{str(e)}"
        )
        await state.clear()


# ===== VAZIFALAR RO'YXATI =====

@router.callback_query(F.data == "admin_list_tasks")
async def list_tasks(callback: CallbackQuery):
    """Barcha vazifalar ro'yxati"""
    tasks = db.get_all_tasks()
    
    if not tasks:
        await callback.message.edit_text(
            "📋 Hozircha vazifalar yo'q.\n\n"
            "➕ Vazifa qo'shish uchun tugmani bosing:",
            reply_markup=admin_tasks_list_menu()
        )
        await callback.answer()
        return
    
    message = "📋 VAZIFALAR RO'YXATI\n\n"
    
    # Filial va rol bo'yicha guruhlash
    current_filial = None
    current_role = None
    task_count = 0
    
    for task_id, text, task_type, role, filial in tasks:
        if filial != current_filial:
            if current_filial is not None:
                message += "\n"
            current_filial = filial
            message += f"🏪 {filial}\n"
            message += "━━━━━━━━━━━━━━━━━━━━\n"
        
        if role != current_role:
            if current_role is not None:
                message += "\n"
            current_role = role
            message += f"  🎭 {role}:\n"
        
        type_emoji = config.TASK_TYPES.get(task_type, task_type)
        message += f"    {type_emoji} {text}\n"
        message += f"       (ID: {task_id})\n"
        task_count += 1
    
    message += "\n━━━━━━━━━━━━━━━━━━━━\n"
    message += f"📊 JAMI: {task_count} ta vazifa"
    
    # Telegram xabar limiti
    if len(message) > 4000:
        await callback.message.answer(message[:4000])
        await callback.message.answer(message[4000:], reply_markup=admin_tasks_menu())
    else:
        await callback.message.edit_text(message, reply_markup=admin_tasks_menu())
    
    await callback.answer()

# ===== VAZIFA O'CHIRISH =====

@router.callback_query(F.data == "admin_delete_task")
async def start_delete_task(callback: CallbackQuery, state: FSMContext):
    """Vazifa o'chirish boshlash"""
    tasks = db.get_all_tasks()
    
    if not tasks:
        await callback.message.edit_text(
            "📋 Hozircha vazifalar yo'q.\n\n"
            "O'chirish uchun vazifa mavjud emas.",
            reply_markup=admin_tasks_menu()
        )
        await callback.answer()
        return
    
    message = "🗑 VAZIFA O'CHIRISH\n\n"
    message += "O'chirmoqchi bo'lgan vazifaning ID raqamini kiriting:\n\n"
    
    # Birinchi 10 ta vazifani ko'rsatish
    message += "📋 VAZIFALAR:\n"
    for i, (task_id, text, task_type, role, filial) in enumerate(tasks[:10], 1):
        type_emoji = config.TASK_TYPES.get(task_type, task_type)
        short_text = text[:30] + "..." if len(text) > 30 else text
        message += f"{i}. ID:{task_id} - {short_text}\n"
    
    if len(tasks) > 10:
        message += f"\n...va yana {len(tasks) - 10} ta vazifa\n"
    
    message += "\n💡 Vazifa ID sini kiriting (masalan: 5)"
    
    await callback.message.edit_text(message)
    await state.set_state(DeleteTaskStates.waiting_for_task_id)
    await callback.answer()

@router.message(DeleteTaskStates.waiting_for_task_id)
async def process_delete_task(message: Message, state: FSMContext):
    """Vazifa ID ni qabul qilish va o'chirish"""
    task_id_text = message.text.strip()
    
    if not task_id_text.isdigit():
        await message.answer(
            "❌ Faqat raqam kiriting!\n\n"
            "Masalan: 5"
        )
        return
    
    task_id = int(task_id_text)
    
    # Vazifa mavjudligini tekshirish
    task = db.get_task(task_id)
    
    if not task:
        await message.answer(
            f"❌ ID {task_id} bilan vazifa topilmadi!\n\n"
            f"Iltimos, to'g'ri ID kiriting."
        )
        return
    
    task_id, task_text, task_type, role_name, filial_name = task
    type_name = config.TASK_TYPES.get(task_type, task_type)
    
    # Tasdiqlash so'rash
    await message.answer(
        f"⚠️ DIQQAT!\n\n"
        f"Quyidagi vazifani o'chirmoqchimisiz?\n\n"
        f"🏪 Filial: {filial_name}\n"
        f"🎭 Rol: {role_name}\n"
        f"📅 Tur: {type_name}\n"
        f"📝 Vazifa: {task_text}\n"
        f"🆔 ID: {task_id}\n\n"
        f"❗️ Bu amalni bekor qilib bo'lmaydi!",
        reply_markup=confirm_keyboard(f"delete_task_{task_id}")
    )
    
    await state.clear()

@router.callback_query(F.data.startswith("delete_task_") & F.data.endswith("_yes"))
async def confirm_delete_task(callback: CallbackQuery):
    """Vazifa o'chirishni tasdiqlash"""
    task_id = int(callback.data.split("_")[2])
    
    try:
        # Vazifa ma'lumotlarini olish
        task = db.get_task(task_id)
        
        if task:
            task_id, task_text, task_type, role_name, filial_name = task
            
            # O'chirish
            db.delete_task(task_id)
            
            await callback.message.edit_text(
                f"✅ VAZIFA O'CHIRILDI!\n\n"
                f"🏪 Filial: {filial_name}\n"
                f"🎭 Rol: {role_name}\n"
                f"📝 Vazifa: {task_text}\n"
                f"🆔 ID: {task_id}\n\n"
                f"✅ Vazifa tizimdan olib tashlandi."
            )
        else:
            await callback.message.edit_text("❌ Vazifa topilmadi!")
        
        await callback.answer("✅ O'chirildi!")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ XATOLIK!\n\n"
            f"Vazifani o'chirishda muammo:\n"
            f"{str(e)}"
        )
        await callback.answer("❌ Xatolik!", show_alert=True)

@router.callback_query(F.data.startswith("delete_task_") & F.data.endswith("_no"))
async def cancel_delete_task(callback: CallbackQuery):
    """Vazifa o'chirishni bekor qilish"""
    await callback.message.edit_text(
        "❌ Bekor qilindi.\n\n"
        "Vazifa o'chirilmadi.",
        reply_markup=admin_tasks_menu()
    )
    await callback.answer()

# ===== BEKOR QILISH VA ORQAGA =====

@router.callback_query(F.data == "admin_cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Amalni bekor qilish"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Bekor qilindi."
    )
    await callback.message.answer(
        "<b>🏠 Asosiy menyu</b>",
        reply_markup=admin_main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Asosiy menyuga qaytish"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "<b>🏠 ASOSIY MENYU</b>\n\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=admin_main_menu()
    )
    await callback.answer()