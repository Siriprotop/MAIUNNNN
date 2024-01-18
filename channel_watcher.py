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
import googleapiclient

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
        print(f'OPENAI {message}')
        try:
            res = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0301",
                messages=[
                    {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости. Отвечай тільки 'NO.' и 'YES.' согласно запросу"},
                    {"role": "user", "content": f"Сообщение далее содержит примерное описание характера местоположения, примерного адреса (рядом с чем-то) или направления движения (в сторону)? Напиши 'YES.' если хоть частично содержит, напиши 'NO.' если не содержит абсолютно. Сообщение: '{message}'"}
                ]
            )
            print('FIRST RESPONCE')
            print(res['choices'][0]['message']['content'])
            if res['choices'][0]['message']['content'] == "NO.":
                print('YES OF FIRST RESPONSE')
                return 404
            rs1 = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0301",
                messages=[
                    {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости. Отвечай тільки 'NO.' и 'YES.' согласно запросу"},
                    {"role": "user", "content": f"Сообщение в кавычках: '{message}' вопросительное? Напиши 'YES.' если вопросительное, напиши 'NO.' если нет."}
                ]
            )
            print('FIRST RESPONCE')
            print(rs1['choices'][0]['message']['content'])
            if rs1['choices'][0]['message']['content'] == "YES.":
                print('YES OF FIRST RESPONSE')
                return 404
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0301",
                messages=[
                    {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости. Отвечай тільки 'NO.' и 'YES.' согласно запросу"},
                    {"role": "user", "content": f"Сообщение содержит рекламный характера? Напиши 'YES.' если хоть частично содержит, напиши 'NO.' если не содержит абсолютно. Сообщение: '{message}'"}
                ]
            )
            print('FIRST RESPONCE')
            print(response['choices'][0]['message']['content'])
            if response['choices'][0]['message']['content'] == "YES.":
                print('YES OF FIRST RESPONSE')
                return 404
            print('STARTING RESPONSE1')
            response1 = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0301",
                messages=[
                    {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости. Переробляй пост і давай відповідь тільки пекреробленим постом згідно з запросом, без коментарієв"},
                    {"role": "user", "content": f"Сообщение далее содержит примерное описание характера местоположения, примерного адреса (рядом с чем-то) или направления движения (в сторону)? Удали все лишнее из него, и оставь только описание места. Не пиши комментарии или примечания к ответу. Удали слова оливки и маслинки. Сообщение:'{message}'"}
                ]
            )

            main_message = (response1['choices'][0]['message']['content'])
            print('STARTING RESPONSE2')
            response2 = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0301",
                messages=[
                    {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости. Отвечай только 'NO.' и 'YES.' согласно запросу"},
                    {"role": "user", "content": f"Сообщение далее содержит подсказку местоположения? Напиши 'YES.' если хоть частично содержит, напиши 'NO.' если не содержит абсолютно. Сообщение:'{main_message}'"}
                ]
            )
            print(response2['choices'][0]['message']['content'])
            if response2['choices'][0]['message']['content'] == "NO.":
                return 404

            # Connect to Google Translate API using API Key
            api_key = 'AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw'
            service = googleapiclient.discovery.build('translate', 'v2', developerKey=api_key)
            translated_address = service.translations().list(source='ru', target='uk', q=main_message).execute()
            translated_text = translated_address['translations'][0]['translatedText']
            return translated_text
        except Exception as e:
            print(e)
            return message

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
                    if gpt_response == 404:
                        print("ПОСТ НЕ ПОДХОДИТ")
                        return
                    
                    self.db.save_message(gpt_response, message.url, channel_name)
                    print(f"Отфильтрованное и модерированное сообщение в канале {channel_name}: {gpt_response}")
                    self.db.print_messages_from_db()
                    self.send_message_to_users(gpt_response, channel_name)
                    self.send_message_to_channels(gpt_response, channel_name)
                break
        except Exception as e:
            print(f"Ошибка при получении сообщений из канала {channel_name}: {e}")

    def run(self):
        while True:
            channel_names = self.dbm.get_all_channel_names()
            for channel_name in channel_names:
                self.fetch_last_message(channel_name)