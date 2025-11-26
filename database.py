# database.py
"""
Database operatsiyalari - SQLite
"""

import sqlite3
from datetime import datetime, date
import config

class Database:
    def __init__(self, db_name=config.DATABASE_NAME):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Database ga ulanish"""
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Barcha jadvallarni yaratish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Filiallar jadvali
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS filials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 2. Guruhlar jadvali
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filial_id INTEGER UNIQUE,
            chat_id BIGINT NOT NULL,
            chat_title TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (filial_id) REFERENCES filials(id)
        )
        """)
        
        # 3. Rollar jadvali
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 4. Foydalanuvchilar jadvali
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT UNIQUE,
            full_name TEXT NOT NULL,
            phone BIGINT NOT NULL UNIQUE,
            filial_id INTEGER,
            role_id INTEGER,
            is_admin BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (filial_id) REFERENCES filials(id),
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )
        """)
        
        # 5. Vazifalar jadvali
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            task_type TEXT NOT NULL,
            role_id INTEGER,
            filial_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (role_id) REFERENCES roles(id),
            FOREIGN KEY (filial_id) REFERENCES filials(id)
        )
        """)
        
        # 6. Bajarilgan vazifalar jadvali
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            user_id INTEGER,
            completion_date DATE NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            media_type TEXT,
            media_file_id TEXT,
            text_message TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(task_id, user_id, completion_date)
        )
        """)
        
        # Boshlang'ich ma'lumotlar
        self._insert_initial_data(cursor)
        
        conn.commit()
        conn.close()
    
    def _insert_initial_data(self, cursor):
        """Boshlang'ich ma'lumotlarni kiritish"""
        
        # Filiallar
        cursor.execute("SELECT COUNT(*) FROM filials")
        if cursor.fetchone()[0] == 0:
            filials = [
                ('Gelyon',),
                ('Marxabo',),
                ('Vogzal',)
            ]
            cursor.executemany("INSERT INTO filials (name) VALUES (?)", filials)
        
        # Guruhlar
        cursor.execute("SELECT COUNT(*) FROM group_chats")
        if cursor.fetchone()[0] == 0:
            groups = [
                (1, config.GROUP_LINKS[0], 'Gelyon Guruh'),
                (2, config.GROUP_LINKS[1], 'Marxabo Guruh'),
                (3, config.GROUP_LINKS[2], 'Vogzal Guruh')
            ]
            cursor.executemany(
                "INSERT INTO group_chats (filial_id, chat_id, chat_title) VALUES (?, ?, ?)", 
                groups
            )
        
        # Rollar
        cursor.execute("SELECT COUNT(*) FROM roles")
        if cursor.fetchone()[0] == 0:
            roles = [
                ('Oshpaz',),
                ('Ofitsiant',),
                ('Kassa',),
                ('Menejer',)
            ]
            cursor.executemany("INSERT INTO roles (name) VALUES (?)", roles)
        

        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        admin_count = cursor.fetchone()[0]

        if admin_count == 0:
            cursor.execute("""
                INSERT INTO users (full_name, phone, filial_id, role_id, is_admin)
                VALUES (?, ?, ?, ?, ?)
            """, ("Super Admin", 998770451117, None, None, 1))
    # ===== FILIAL OPERATSIYALARI =====
    
    def get_all_filials(self):
        """Barcha filiallarni olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM filials ORDER BY id")
        filials = cursor.fetchall()
        conn.close()
        return filials
    
    def get_filial(self, filial_id):
        """Bitta filialni olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM filials WHERE id = ?", (filial_id,))
        filial = cursor.fetchone()
        conn.close()
        return filial
    
    # ===== ROL OPERATSIYALARI =====
    
    def get_all_roles(self):
        """Barcha rollarni olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM roles ORDER BY id")
        roles = cursor.fetchall()
        conn.close()
        return roles
    
    def get_role(self, role_id):
        """Bitta rolni olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM roles WHERE id = ?", (role_id,))
        role = cursor.fetchone()
        conn.close()
        return role
    
    # ===== USER OPERATSIYALARI =====
    
    def create_user(self, full_name, phone, filial_id, role_id, is_admin=False):
        """Yangi user yaratish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (full_name, phone, filial_id, role_id, is_admin)
            VALUES (?, ?, ?, ?, ?)
        """, (full_name, phone, filial_id, role_id, is_admin))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    def get_user_by_phone(self, phone):
        """Telefon orqali userni topish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.telegram_id, u.full_name, u.phone, 
                   u.filial_id, f.name as filial_name,
                   u.role_id, r.name as role_name, u.is_admin
            FROM users u
            LEFT JOIN filials f ON u.filial_id = f.id
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.phone = ? AND u.is_active = 1
        """, (phone,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def get_user_by_telegram_id(self, telegram_id):
        """Telegram ID orqali userni topish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.telegram_id, u.full_name, u.phone, 
                   u.filial_id, f.name as filial_name,
                   u.role_id, r.name as role_name, u.is_admin
            FROM users u
            LEFT JOIN filials f ON u.filial_id = f.id
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.telegram_id = ? AND u.is_active = 1
        """, (telegram_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def update_user_telegram_id(self, phone, telegram_id):
        """User telegram ID sini yangilash"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET telegram_id = ? WHERE phone = ?
        """, (telegram_id, phone))
        conn.commit()
        conn.close()
    
    def get_all_users(self, filial_id=None):
        """Barcha userlarni olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if filial_id:
            cursor.execute("""
                SELECT u.id, u.full_name, u.phone, f.name, r.name
                FROM users u
                LEFT JOIN filials f ON u.filial_id = f.id
                LEFT JOIN roles r ON u.role_id = r.id
                WHERE u.filial_id = ? AND u.is_active = 1
                ORDER BY r.name, u.full_name
            """, (filial_id,))
        else:
            cursor.execute("""
                SELECT u.id, u.full_name, u.phone, f.name, r.name
                FROM users u
                LEFT JOIN filials f ON u.filial_id = f.id
                LEFT JOIN roles r ON u.role_id = r.id
                WHERE u.is_active = 1
                ORDER BY f.name, r.name, u.full_name
            """)
        users = cursor.fetchall()
        conn.close()
        return users
    
    def delete_user(self, user_id):
        """Userni (ishchini) ID bo‘yicha o‘chirish (soft delete)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET is_active = 0 WHERE id = ?
        """, (user_id,))
        conn.commit()
        conn.close()
    
    def add_admin(self, phone):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET is_admin = 1 WHERE phone = ?
        """, (phone,))
        conn.commit()
        conn.close()

    def get_admins(self):
        """Barcha adminlarni olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT full_name, phone
            FROM users
            WHERE is_admin = 1
        """)
        user = cursor.fetchall()
        conn.close()
        return user
    
    def get_admin_by_phone(self, phone):
        """Phone nomer orqali adminni topish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT full_name, phone
            FROM users
            WHERE is_admin = 1 AND phone = ?
        """, (phone,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def del_admin(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET is_admin = 0 WHERE phone = ?
        """, (user_id,))
        conn.commit()
        conn.close()
    
    # ===== VAZIFA OPERATSIYALARI =====
    
    def create_task(self, text, task_type, role_id, filial_id):
        """Yangi vazifa yaratish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (text, task_type, role_id, filial_id)
            VALUES (?, ?, ?, ?)
        """, (text, task_type, role_id, filial_id))
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    def get_user_tasks(self, user_id, target_date):
        """User uchun bugungi vazifalarni olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # User ma'lumotlarini olish
        cursor.execute("""
            SELECT filial_id, role_id FROM users WHERE id = ?
        """, (user_id,))
        user_data = cursor.fetchone()
        if not user_data:
            conn.close()
            return []
        
        filial_id, role_id = user_data
        
        # Qaysi vazifa turlarini ko'rsatish kerak
        task_types = ['daily']
        if target_date.weekday() == 0:  # Dushanba
            task_types.append('monday')
        if target_date.day == 1:  # Oyning 1-kuni
            task_types.append('monthly')
        
        # Vazifalarni olish
        placeholders = ','.join('?' * len(task_types))
        cursor.execute(f"""
            SELECT t.id, t.text, t.task_type,
                   CASE WHEN tc.id IS NOT NULL THEN 1 ELSE 0 END as completed
            FROM tasks t
            LEFT JOIN task_completions tc ON t.id = tc.task_id 
                AND tc.user_id = ? 
                AND tc.completion_date = ?
            WHERE t.role_id = ? 
                AND t.filial_id = ? 
                AND t.task_type IN ({placeholders})
                AND t.is_active = 1
            ORDER BY t.task_type, t.id
        """, (user_id, target_date, role_id, filial_id, *task_types))
        
        tasks = cursor.fetchall()
        conn.close()
        return tasks
    
    def complete_task(self, task_id, user_id, media_type=None, media_file_id=None, text_message=None):
        """Vazifani bajarildi deb belgilash"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = date.today()
        
        cursor.execute("""
            INSERT OR REPLACE INTO task_completions 
            (task_id, user_id, completion_date, media_type, media_file_id, text_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (task_id, user_id, today, media_type, media_file_id, text_message))
        
        conn.commit()
        conn.close()
    
    def get_task(self, task_id):
        """Vazifa ma'lumotlarini olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.text, t.task_type, r.name, f.name
            FROM tasks t
            LEFT JOIN roles r ON t.role_id = r.id
            LEFT JOIN filials f ON t.filial_id = f.id
            WHERE t.id = ?
        """, (task_id,))
        task = cursor.fetchone()
        conn.close()
        return task
    
    def get_all_tasks(self, filial_id=None, role_id=None, task_type=None):
        """Barcha vazifalarni olish (filtrlash bilan)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT t.id, t.text, t.task_type, r.name, f.name
            FROM tasks t
            LEFT JOIN roles r ON t.role_id = r.id
            LEFT JOIN filials f ON t.filial_id = f.id
            WHERE t.is_active = 1
        """
        params = []
        
        if filial_id:
            query += " AND t.filial_id = ?"
            params.append(filial_id)
        if role_id:
            query += " AND t.role_id = ?"
            params.append(role_id)
        if task_type:
            query += " AND t.task_type = ?"
            params.append(task_type)
        
        query += " ORDER BY f.name, r.name, t.task_type"
        
        cursor.execute(query, params)
        tasks = cursor.fetchall()
        conn.close()
        return tasks
    
    def delete_task(self, task_id):
        """Vazifani o'chirish (soft delete)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET is_active = 0 WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
    
    # ===== GURUH OPERATSIYALARI =====
    
    def get_group_chat_id(self, filial_id):
        """Filial guruh chat ID sini olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT chat_id FROM group_chats 
            WHERE filial_id = ? AND is_active = 1
        """, (filial_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    # ===== STATISTIKA =====
    
    def get_daily_statistics(self, filial_id, target_date):
        """Kunlik statistika"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Qaysi vazifa turlarini hisobga olish
        task_types = ['daily']
        if target_date.weekday() == 0:
            task_types.append('monday')
        if target_date.day == 1:
            task_types.append('monthly')
        
        placeholders = ','.join('?' * len(task_types))
        
        # Rol bo'yicha statistika
        cursor.execute(f"""
            SELECT 
                r.id,
                r.name,
                COUNT(DISTINCT u.id) as user_count,
                COUNT(t.id) as total_tasks,
                COUNT(tc.id) as completed_tasks
            FROM roles r
            INNER JOIN users u ON r.id = u.role_id
            LEFT JOIN tasks t ON t.role_id = r.id 
                AND t.filial_id = ? 
                AND t.task_type IN ({placeholders})
                AND t.is_active = 1
            LEFT JOIN task_completions tc ON t.id = tc.task_id 
                AND tc.user_id = u.id 
                AND tc.completion_date = ?
            WHERE u.filial_id = ? AND u.is_active = 1
            GROUP BY r.id, r.name
            ORDER BY r.id
        """, (filial_id, *task_types, target_date, filial_id))
        
        role_stats = cursor.fetchall()
        
        # Har bir user bo'yicha
        cursor.execute(f"""
            SELECT 
                u.id,
                u.full_name,
                r.name as role_name,
                COUNT(DISTINCT t.id) as total_tasks,
                COUNT(DISTINCT tc.id) as completed_tasks
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            LEFT JOIN tasks t ON t.role_id = u.role_id 
                AND t.filial_id = u.filial_id 
                AND t.task_type IN ({placeholders})
                AND t.is_active = 1
            LEFT JOIN task_completions tc ON t.id = tc.task_id 
                AND tc.user_id = u.id 
                AND tc.completion_date = ?
            WHERE u.filial_id = ? AND u.is_active = 1
            GROUP BY u.id, u.full_name, r.name
            ORDER BY r.name, u.full_name
        """, (*task_types, target_date, filial_id))
        
        user_stats = cursor.fetchall()
        
        conn.close()
        return role_stats, user_stats

# Global database obyekti
db = Database()