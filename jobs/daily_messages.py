# jobs/daily_messages.py
import sqlite3
from telegram.ext import CallbackContext
import datetime
import pytz
from config import channelsss

class DailyMessageJob:
    def __init__(self, db_path, info_dbs, dbs):
        self.db_path = db_path
        self.info_dbs = info_dbs
        self.dbs = dbs
    def send_addresses(self, context:CallbackContext):
        self.info_dbs.delete_old_addresses()
        recent_addresses = self.info_dbs.get_recent_addresses()
        print(recent_addresses)
        if recent_addresses:
        
            message_text = '\n'.join(f"📍{address}\n{comment}" for address, comment in recent_addresses)
            message = f"<b>🚨 Актуальный список адресов WTU (за 24 часа):</b>\n\n{message_text}"
        else:
            message_text = "На данный момент нет новых адресов."
        for channel_id in channelsss:
            try:
                context.bot.send_message(chat_id=channel_id, text=message, parse_mode='HTML')
            except Exception as e:
                print(e)

    def reset_weekly_addresses(self, context: CallbackContext):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET addresses = 0")
            conn.commit()
        except Exception as e:
            print(f"Error resetting weekly addresses: {e}")
        finally:
            conn.close()

    def send_daily_message(self, context: CallbackContext):
        message_text = context.job.context['message_text']
        print(message_text)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for channel_id in channelsss:
                try:
                    context.bot.send_message(chat_id=channel_id, text=message_text)
                except Exception as e:
                    print(f"Ошибка при отправке сообщения каналу {channel_id}: {e}")
        finally:
            conn.close()

    def schedule(self, updater):
        tz = pytz.timezone('Europe/Moscow')

        # Обновленные тексты сообщений
        morning_message = "✅ Чтобы не потерять информацию про адреса WTU, обязательно подписывайтесь на нашего бота на базе искусственного интеллекта Chat GPT: https://t.me/sasadas_bot/"
        evening_message = ("ПОДЕЛИСЬ БОНУС-КОДОМ С ДРУГОМ, и получи PREMIUM доступ к каналу на 2 месяца, что дает тебе:\n"
                           "📍 Доступ к карте адресов (новинка).\n"
                           "🤡 Отсутствие рекламы и новостей (нет спама)\n"
                           "🚨 Уведомления об опасной зоне (скоро).\n"
                           "💵 Участие в акции “Лучший реферал”\n\n"
                           "Получить бонусный код очень просто:\n"
                           "1) Подпишись на бота https://t.me/sasadas_bot/\n"
                           "2) Выбери в меню \"Получить бонус-код\"\n"
                           "3) Отправь полученный код другу.")
        updater.job_queue.run_daily(self.send_daily_message, time=datetime.time(hour=7, minute=0, tzinfo=tz), context={'message_text': morning_message})
        updater.job_queue.run_daily(self.send_daily_message, time=datetime.time(hour=19, minute=0, tzinfo=tz), context={'message_text': evening_message})
        updater.job_queue.run_daily(self.send_addresses, time=datetime.time(hour=0, minute=55, tzinfo=tz))
        updater.job_queue.run_daily(self.send_addresses, time=datetime.time(hour=12, minute=7, tzinfo=tz))
        updater.job_queue.run_daily(self.send_addresses, time=datetime.time(hour=16, minute=0, tzinfo=tz))
        weekly_reset_day = 0 
        weekly_reset_time = datetime.time(hour=0, minute=0, second=0)
        now = datetime.datetime.now()
        days_until_reset = (weekly_reset_day - now.weekday()) % 7
        next_reset = now + datetime.timedelta(days=days_until_reset)
        next_reset = next_reset.replace(hour=weekly_reset_time.hour, minute=weekly_reset_time.minute, second=weekly_reset_time.second)
        one_week_interval = 7 * 24 * 60 * 60 
        updater.job_queue.run_repeating(self.reset_weekly_addresses, interval=one_week_interval, first=next_reset)