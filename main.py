import sqlite3

def clear_promocodes_table():
    conn = sqlite3.connect('subscribe.db')
    cursor = conn.cursor()

    # Удаляем все записи из таблицы promocodes
    cursor.execute("DELETE FROM promocodes")
    conn.commit()

    conn.close()
    print("Таблица promocodes была очищена.")

# Вызов функции для очистки таблицы
clear_promocodes_table()
