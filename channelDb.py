import sqlite3

class ChannelDB:
    def __init__(self, db_file):
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                name TEXT PRIMARY KEY,
                user_file TEXT,
                channel_id TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_channel(self, name, user_file, channel_id):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO channels (name, user_file, channel_id) VALUES (?, ?, ?)",
                       (name, user_file, channel_id))
        conn.commit()
        conn.close()
    def get_all_channel_names(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM channels")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except sqlite3.Error as e:
            print(f"Ошибка при выполнении запроса к базе данных: {e}")
            return []
        finally:
            conn.close()
    def get_channel_info(self, name):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT user_file, channel_id FROM channels WHERE name = ?", (name,))
        info = cursor.fetchone()
        conn.close()
        return {"user_file": info[0], "channel_id": info[1]} if info else None

    def print_all_channels(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM channels")
        result = cursor.fetchone()
        conn.close()
        return result