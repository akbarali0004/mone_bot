# keyboards.py
"""
Barcha inline va reply klaviaturalari.
"""

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

# ============================================================
# ADMIN KLAVIATURALAR
# ============================================================

def admin_main_menu():
    """Admin asosiy menyu"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👥 Ishchilar"),
                KeyboardButton(text="📋 Vazifalar"),
            ],
            [
                KeyboardButton(text="📊 Statistika"),
                KeyboardButton(text="⚙️ Sozlamalar"),
            ],
            [
                KeyboardButton(text="👤 Adminlar")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def admin_workers_menu():
    """Admin — ishchilar bo‘limi menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Ishchi qo'shish",
                    callback_data="admin_add_worker"
                ),
                InlineKeyboardButton(
                    text="📋 Ishchilar ro'yxati",
                    callback_data="admin_list_workers"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data="admin_back_main"
                )
            ]
        ]
    )


def admin_workers_list_menu():
    """Admin — ishchilar bo‘limi menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➖ Ishchi o'chirish",
                    callback_data="admin_delete_worker"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data="admin_back_list_main"
                )
            ]
        ]
    )


def admin_tasks_menu():
    """Admin — vazifalar bo‘limi menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Vazifa qo'shish",
                    callback_data="admin_add_task"
                ),
                InlineKeyboardButton(
                    text="📋 Vazifalar ro'yxati",
                    callback_data="admin_list_tasks"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Vazifa o'chirish",
                    callback_data="admin_delete_task"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data="admin_back_main"
                )
            ]
        ]
    )


def admin_tasks_list_menu():
    """Admin — vazifalar bo‘limi menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Vazifa qo'shish",
                    callback_data="admin_add_task"
                ),
                InlineKeyboardButton(
                    text="➖ Vazifa o'chirish",
                    callback_data="admin_delete_task"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data="admin_back_main"
                )
            ]
        ]
    )


def select_filial_keyboard(callback_prefix="filial"):
    """Filial tanlash klaviaturasi"""
    from database import db
    filials = db.get_all_filials()

    buttons = [
        [
            InlineKeyboardButton(
                text=f"🏪 {name}",
                callback_data=f"{callback_prefix}_{fid}"
            )
        ]
        for fid, name in filials
    ]

    buttons.append([
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data="admin_back_main"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def select_role_keyboard(callback_prefix="role"):
    """Role tanlash klaviaturasi"""
    from database import db
    roles = db.get_all_roles()

    buttons = [
        [
            InlineKeyboardButton(
                text=f"🎭 {name}",
                callback_data=f"{callback_prefix}_{rid}"
            )
        ]
        for rid, name in roles
    ]

    buttons.append([
        InlineKeyboardButton(
            text="🔙 Bekor qilish",
            callback_data="admin_cancel"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def select_task_type_keyboard():
    """Vazifa turi tanlash klaviaturasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔴 Har kunlik", callback_data="tasktype_daily")],
            [InlineKeyboardButton(text="🔵 Har dushanba", callback_data="tasktype_monday")],
            [InlineKeyboardButton(text="🟢 Har oy", callback_data="tasktype_monthly")],
            [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="admin_cancel")],
        ]
    )


def confirm_keyboard(callback_prefix="confirm"):
    """Tasdiqlash klaviaturasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha",
                    callback_data=f"{callback_prefix}_yes"
                ),
                InlineKeyboardButton(
                    text="❌ Yo'q",
                    callback_data=f"{callback_prefix}_no"
                ),
            ]
        ]
    )

# ============================================================
# USER KLAVIATURALAR
# ============================================================

def user_main_menu():
    """User asosiy menyu"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Vazifalar ro'yxati"),
                KeyboardButton(text="📊 Mening statistikam"),
            ],
            [
                KeyboardButton(text="ℹ️ Ma'lumot"),
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def user_tasks_keyboard(tasks):
    """
    tasks = [
        (task_id, task_text, task_type, completed_bool)
    ]
    """
    buttons = []

    for task_id, task_text, task_type, completed in tasks:
        emoji = "✅" if completed else "❗"
        short_text = (task_text[:40] + "...") if len(task_text) > 40 else task_text

        buttons.append([InlineKeyboardButton(
            text=f"[{emoji}] {short_text}",
            callback_data=f"task_{task_id}"
        )])

    buttons.append([
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_tasks")
    ])
    buttons.append([
        InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="user_main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def task_action_keyboard(task_id, completed=False):
    """Vazifa ichidagi tugmalar"""
    buttons = []

    if not completed:
        buttons.append([
            InlineKeyboardButton(
                text="📎 Bajarilganini yuborish",
                callback_data=f"complete_{task_id}"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Bajarilgan",
                callback_data="already_completed"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data="back_to_tasks"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_tasks_keyboard():
    """Vazifalar ro'yxatiga qaytish"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Vazifalar ro'yxati",
                    callback_data="back_to_tasks"
                )
            ]
        ]
    )



phone_ask = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='📞 Kontankt yuborish', request_contact=True)
    ]
], resize_keyboard=True)


cancel_btn = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back_main")
    ]
])


def is_check(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"checked_{user_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_from_del_worker")
        ]
    ])



cancel_del_btn = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_from_del_worker")
        ]
    ])


def admin_admins_menu():
    """Admin — adminlar bo‘limi menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin_add_admin"),
                InlineKeyboardButton(text="📋 Adminlar ro'yxati", callback_data="admin_list_admins"),
            ],
            [
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back_main")
            ]
        ]
    )


def admin_admins_list_menu():
    """Admin — adminlar bo‘limi menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➖ Admin o'chirish",
                    callback_data="admin_delete_admin"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data="admin_back_list_main"
                )
            ]
        ]
    )
