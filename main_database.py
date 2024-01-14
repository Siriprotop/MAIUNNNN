import sqlite3




class DataB:
    def __init__ (self):
        self.init_db()

    def init_db(self):
        print('1231321313')
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        # Создание таблицы для пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                city TEXT,
                is_moderator INTEGER DEFAULT 0
            )
        ''')
        # Создание таблицы для постов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                address TEXT,
                details TEXT,
                photo_url TEXT,
                date_time DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        conn.commit()
        conn.close()

    def add_user(self, user_id, city):
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (user_id, city) VALUES (?, ?)", (user_id, city))
        conn.commit()
        conn.close()


    def add_post(self, user_id, address, details, photo_url, date_time):
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO posts (user_id, address, details, photo_url, date_time) VALUES (?, ?, ?, ?, ?)",
                    (user_id, address, details, photo_url, date_time))
        conn.commit()
        post_id = cursor.lastrowid
        conn.close()
        return post_id
    def get_users_by_city(self, city):
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE city = ?", (city,))
        users = cursor.fetchall()
        conn.close()
        return [user[0] for user in users]


    def get_all_users(self):
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        conn.close()
        return users

    def get_all_posts(self):
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM posts")
        posts = cursor.fetchall()
        conn.close()
        return posts
    def delete_post(self, user_id):
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM posts WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()