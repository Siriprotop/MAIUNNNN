import json
import snscrape.modules.telegram as sntelegram
import time
from threading import Thread
from hashlib import md5
import openai
import logging
from database import DataBase
from other import *
from config import channelsss

class TelegramChannelWatcher:
    def __init__(self, dbm, dbs, bot):
        self.bot = bot
        print(self.bot)
        self.dbm = dbm
        self.dbs = dbs
        self.db = DataBase("channels.db")

    def send_message_to_users(self, message, channel_name):
        channel_info = self.dbm.get_channel_info(channel_name)
        user_ids = self.dbs.get_users_by_city(channel_info.get('user_file'))
        for user_id in user_ids:
            for city_channel in channelsss:
                res1 = is_user_in_channel(self.bot, city_channel, user_id)
                if res1 == True:
                    break
            if res1 == True:
                continue
            try:
                self.bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
    def chat_gpt_query(self, message):
        openai.api_key = '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'
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0301",
                messages=[
                    {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости."},
                    {"role": "user", "content": f"Сообщение далее содержит примерное описание характера местоположения, примерного адреса или направления движения? Напиши YES если хоть частично содержит, напиши NO если не содержит абсолютно. Сообщение: {message}"}
                ]
            )
            first_response = response['choices'][0]['message']['content']
            if "YES" in first_response.upper():
                moderated_response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-0301",
                    messages=[
                        {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости."},
                        {"role": "user", "content": f"Візьми це повідомлення: '{message}', та проведи модерацію та виправлення, а саме: Видали з тексту всі образи, лайки та сленги. Прибери всі спец.символи, теги, посилання. Переклади текст українською. Залиш тільки адрес і город і важну інформацію, і все. Без всяких лишних комментариев"}
                    ]
                )
                return moderated_response['choices'][0]['message']['content']
            return first_response
        except Exception as e:
            print(f"Ошибка при запросе к GPT: {e}")
            return "NO"

    def start(self):
        thread = Thread(target=self.run, args=())
        thread.start()

    def send_message_to_channels(self, message, channel_name):
        """ Отправить сообщение в канал по его имени. """
        channel_info = self.dbm.get_channel_info(channel_name)
        if channel_info:
            channel_id = channel_info["channel_id"]
            try:
                self.bot.send_message(chat_id=channel_id, text=message)
            except Exception as e:
                print(f"Ошибка при отправке сообщения в канал {channel_name}: {e}")

    def fetch_last_message(self, channel_name):
        scraper = sntelegram.TelegramChannelScraper(channel_name)
        try:
            for message in scraper.get_items():
                message_hash = md5(message.content.encode('utf-8')).hexdigest()
                if self.db.is_new_message(channel_name, message_hash):
                    self.db.update_last_message(channel_name, message_hash)
                    gpt_response = self.chat_gpt_query(message.content)
                    if gpt_response != "NO":
                        self.db.save_message(gpt_response, message.url, channel_name)
                        print(f"Отфильтрованное и модерированное сообщение в канале {channel_name}: {gpt_response}")
                        self.db.print_messages_from_db()
                        self.send_message_to_users(gpt_response, channel_name)
                        self.send_message_to_channels(gpt_response, channel_name)
                    else:
                        print(f"Сообщение из канала {channel_name} не содержит адреса или направления.")
                break
        except Exception as e:
            print(f"Ошибка при получении сообщений из канала {channel_name}: {e}")

    def run(self):
        while True:
            channel_names = self.dbm.get_all_channel_names()
            for channel_name in channel_names:
                self.fetch_last_message(channel_name)
