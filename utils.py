# utils.py
"""
Yordamchi funksiyalar
"""

from datetime import datetime, date
import config

def format_date(target_date):
    """Sanani o'zbekcha formatda chiqarish"""
    day = target_date.day
    month = config.MONTHS[target_date.month]
    year = target_date.year
    weekday = config.WEEKDAYS[target_date.weekday()]
    
    return f"{day}-{month}, {year}-yil ({weekday})"

def format_phone(phone):
    """Telefon raqamini formatda ko'rsatish"""
    phone_str = str(phone)
    return f"+{phone_str}"

def get_status_emoji(percentage):
    """Foiz bo'yicha emoji berish"""
    if percentage >= 80:
        return config.STATUS_EMOJI[100]
    elif percentage >= 50:
        return config.STATUS_EMOJI[80]
    elif percentage >= 1:
        return config.STATUS_EMOJI[50]
    else:
        return config.STATUS_EMOJI[0]

def format_user_tasks_message(user_data, tasks, target_date):
    """User uchun vazifalar ro'yxati xabarini yaratish"""
    
    # User ma'lumotlari
    user_id, telegram_id, full_name, phone, filial_id, filial_name, role_id, role_name, is_admin = user_data
    
    # Vazifalarni guruhlash
    daily_tasks = []
    monday_tasks = []
    monthly_tasks = []
    total_incomplete = 0
    
    for task_id, task_text, task_type, completed in tasks:
        if not completed:
            total_incomplete += 1
        
        if task_type == 'daily':
            daily_tasks.append((task_id, task_text, completed))
        elif task_type == 'monday':
            monday_tasks.append((task_id, task_text, completed))
        elif task_type == 'monthly':
            monthly_tasks.append((task_id, task_text, completed))
    
    # Xabar matni
    message = f"""<b>📋 SIZNING VAZIFALARINGIZ</b>

Filial: {filial_name}
Rol: {role_name}
Sana: {format_date(target_date)}

"""
    
    # Har kunlik vazifalar
    if daily_tasks:
        message += "🔴 HAR KUNLIK VAZIFALAR:\n"
        for i, (task_id, text, completed) in enumerate(daily_tasks, 1):
            emoji = "✅" if completed else "❗"
            message += f"{i}. [{emoji}] {text}\n"
        message += "\n"
    
    # Dushanba vazifalar
    if monday_tasks:
        message += "🔵 HAR DUSHANBA VAZIFALAR:\n"
        for i, (task_id, text, completed) in enumerate(monday_tasks, 1):
            emoji = "✅" if completed else "❗"
            message += f"{i}. [{emoji}] {text}\n"
        message += "\n"
    
    # Oylik vazifalar
    if monthly_tasks:
        message += "🟢 HAR OY VAZIFALAR:\n"
        for i, (task_id, text, completed) in enumerate(monthly_tasks, 1):
            emoji = "✅" if completed else "❗"
            message += f"{i}. [{emoji}] {text}\n"
        message += "\n"
    
    if total_incomplete > 0:
        message += f"Jami bajarilmagan: {total_incomplete} ta vazifa"
    else:
        message += "✅ Barcha vazifalar bajarildi!"
    
    return message

def format_task_completion_caption(user_data, task_text):
    """Vazifa bajarilganligi haqida guruhga yuborish uchun caption"""
    user_id, telegram_id, full_name, phone, filial_id, filial_name, role_id, role_name, is_admin = user_data
    
    now = datetime.now()
    time_str = now.strftime('%d-%B-%Y, %H:%M')
    # Oyni o'zbekchaga o'zgartirish
    for en_month, uz_month in {
        'January': 'Yanvar', 'February': 'Fevral', 'March': 'Mart',
        'April': 'Aprel', 'May': 'May', 'June': 'Iyun',
        'July': 'Iyul', 'August': 'Avgust', 'September': 'Sentabr',
        'October': 'Oktabr', 'November': 'Noyabr', 'December': 'Dekabr'
    }.items():
        time_str = time_str.replace(en_month, uz_month)
    
    caption = f"""<b>📌 VAZIFA BAJARILDI</b>

🏪 Filial: {filial_name}
👤 Ishchi: {full_name}
📱 Telefon: {format_phone(phone)}
🎭 Rol: {role_name}
📝 Vazifa: {task_text}
⏰ Bajarilgan vaqt: {time_str}"""
    
    return caption

def format_daily_statistics(filial_name, role_stats, user_stats, target_date):
    """Kunlik statistika xabarini yaratish"""
    
    message = f"""<b>📊 KUNLIK HISOBOT</b>
📅 Sana: {format_date(target_date)}
🏪 Filial: {filial_name}

"""
    
    total_workers = 0
    total_tasks = 0
    total_completed = 0
    
    # Rol bo'yicha guruhlangan userlar
    users_by_role = {}
    for user_id, user_name, role_name, user_total, user_completed in user_stats:
        if role_name not in users_by_role:
            users_by_role[role_name] = []
        users_by_role[role_name].append({
            'name': user_name,
            'total': user_total,
            'completed': user_completed,
            'percentage': round(user_completed / user_total * 100) if user_total > 0 else 0
        })
    
    # Har bir rol uchun
    for role_id, role_name, user_count, role_total, role_completed in role_stats:
        if user_count == 0:
            continue
        
        total_workers += user_count
        total_tasks += role_total
        total_completed += role_completed
        
        role_percentage = round(role_completed / role_total * 100) if role_total > 0 else 0
        
        message += "━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"👨‍💼 {role_name.upper()} ({user_count} ta ishchi)\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Rol ichidagi userlar
        if role_name in users_by_role:
            for user in users_by_role[role_name]:
                emoji = get_status_emoji(user['percentage'])
                message += f"{emoji} {user['name']} - {user['completed']}/{user['total']} ({user['percentage']}%)\n"
        
        message += f"\nJAMI: {role_completed}/{role_total} ({role_percentage}%)\n\n"
    
    # Umumiy natija
    overall_percentage = round(total_completed / total_tasks * 100) if total_tasks > 0 else 0
    
    message += "━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "📈 UMUMIY NATIJA\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += f"Jami ishchilar: {total_workers} ta\n"
    message += f"Jami vazifalar: {total_tasks} ta\n"
    message += f"Bajarildi: {total_completed} ta ({overall_percentage}%)\n"
    message += f"Bajarilmagan: {total_tasks - total_completed} ta ({100 - overall_percentage}%)\n\n"
    
    # TOP va PAST ishchilar
    all_users = []
    for users in users_by_role.values():
        all_users.extend(users)
    
    all_users.sort(key=lambda x: x['percentage'], reverse=True)
    
    if len(all_users) >= 3:
        message += "🌟 TOP-3 ISHCHILAR:\n"
        for i, user in enumerate(all_users[:3], 1):
            message += f"{i}. {user['name']} ({user['percentage']}%)\n"
        message += "\n"
    
    # Kam ishlagan ishchilar (50% dan past)
    low_performers = [u for u in all_users if u['percentage'] < 50]
    if low_performers:
        message += "📉 E'TIBOR BERISH KERAK:\n"
        for i, user in enumerate(low_performers[:3], 1):
            message += f"{i}. {user['name']} ({user['percentage']}%)\n"
    
    return message