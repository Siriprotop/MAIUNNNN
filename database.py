import sqlite3
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class DataBase:
    def __init__(self, db_file):
        self.db_file = db_file
        self.lock = Lock()
        self.init_db()

    def init_db(self):
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS channel_messages 
                              (channel_name TEXT PRIMARY KEY, last_message_id TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS messages 
                              (id INTEGER PRIMARY KEY, message TEXT, date TEXT, source_id TEXT, city TEXT)''')
            conn.commit()
            conn.close()

    def save_message(self, message, source_id, city):
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO messages (message, date, source_id, city) VALUES (?, datetime('now'), ?, ?)",
                           (message, source_id, city))
            conn.commit()
            conn.close()

    def is_new_message(self, channel, message_hash):
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT last_message_id FROM channel_messages WHERE channel_name = ?", (channel,))
            result = cursor.fetchone()
            conn.close()
            return not result or result[0] != message_hash

    def update_last_message(self, channel, message_hash):
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("REPLACE INTO channel_messages (channel_name, last_message_id) VALUES (?, ?)", 
                           (channel, message_hash))
            conn.commit()
            conn.close()

    def print_messages_from_db(self):
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT * FROM messages")
                messages = cursor.fetchall()
                for message in messages:
                    logger.info(f"ID: {message[0]}, Message: {message[1]}, Date: {message[2]}, Source ID: {message[3]}, City: {message[4]}")
            except Exception as e:
                logger.error(f"Ошибка при чтении из базы данных: {e}")
            finally:
                conn.close()
