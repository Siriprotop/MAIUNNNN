import sqlite3

class InfoDb:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect('repost_info.db')
        cursor = conn.cursor()
        cursor.execute(''' CREATE TABLE IF NOT EXISTS info (
            address TEXT,
            comment TEXT,
            hours INTEGER
        )
        ''')
        conn.commit()
        conn.close()

    def add_address(self, address, comment):
        conn = sqlite3.connect('repost_info.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO info (address, comment) VALUES (?, ?)", (address, comment))
        conn.commit()
        conn.close()

    def delete_old_addresses(self):
        conn = sqlite3.connect('repost_info.db')
        cursor = conn.cursor()
        # Удаляем адреса, которым более 24 часов
        cursor.execute("DELETE FROM info WHERE hours < datetime('now', '-1 day')")
        conn.commit()
        conn.close()
    def get_recent_addresses(self):
        conn = sqlite3.connect('repost_info.db')
        cursor = conn.cursor()
        # Получаем адреса, добавленные за последние 24 часа
        cursor.execute("SELECT address, comment FROM info ")
        recent_addresses = cursor.fetchall()
        conn.close()
        return recent_addresses