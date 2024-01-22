from imports import *
EXACT_ADDRESS, EXACT_ADDR, DETAILS, PHOTO, YR_MODERATION, BONUS_CODE = range(6)


moderator_ids = [6964683351]
# classes
dbm = ChannelDB("channels_list.db")
info_dbs = InfoDb()
dbs = DataB()
manage_limits = AddressLimits(dbs)
ukrainian_months = {
    1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
    5: "травня", 6: "червня", 7: "липня", 8: "серпня",
    9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
}


CHOOSE_city, BROADCAST_MSG, BROADCAST_ALL = range(5, 8)
# def create_promocodes_table():
#     conn = sqlite3.connect('subscribe.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS promocodes (
#             user_id INTEGER,
#             promocode TEXT,
#             expiry_date DATETIME,
#             active INTEGER,
#             count INTEGER DEFAULT 0
#         )
#     ''')
#     conn.commit()
#     conn.close()



def format_message(address, details, photo, date_time):
    message_parts = [address, details if details.strip() != '' else None, photo if photo.strip() != '' else None, date_time]
    return "\n".join(filter(None, message_parts))

# Исправленная функция process_message_for_publication с обработкой случая, когда комментарий пропущен
def process_message_for_publication(update, context):
    try:
        user_id = user_data['user_id']

        # Retrieve data from user_data
        address = user_data[user_id].get('EXACT_ADDRESS', '').strip()
        details = user_data[user_id].get('DETAILS', '').strip()
        photo_url = user_data[user_id].get('PHOTO', '').strip()
        formatted_date = user_data[user_id].get('DATE_TIME', '').strip()
        user_id_str = str(user_id).strip()

        # Define city variable if not present
        city = user_data[user_id].get('CITY', '').strip()

        # Check if address and details are available
        if not address:
            return YR_MODERATION  # Send to moderation if address is not available

        moderated_address = filter_and_translate_address(address)
        if moderated_address == 404:
            # Send to moderation if address filtering fails
            send_message_to_moderation(user_id, context, address, details, photo_url, formatted_date, user_id_str)
            return

        # Check if details are provided, filter and translate
        if details:
            moderated_details = filter_and_translate_details(details)
            if moderated_details == 404:
                # Send to moderation if details filtering fails
                send_message_to_moderation(user_id, context, address, details, photo_url, formatted_date, user_id_str)
                return
        else:
            moderated_details = ""  # Set empty string if details are skipped

        user_data[user_id]['EXACT_ADDRESS'] = moderated_address
        user_data[user_id]['DETAILS'] = moderated_details

        # Формируем итоговое сообщение для публикации
        post_id = dbs.add_post(user_id, moderated_address, moderated_details, photo_url, formatted_date)
        info_dbs.add_address(moderated_address, moderated_details)
        user_data[user_id]['POST_ID'] = post_id
        final_message = compose_final_message(moderated_address, moderated_details, photo_url)
        
        # Публикация сообщения
        publish_message_city(update, context)
        return ConversationHandler.END
    except Exception as e:
        send_message_to_moderation(user_id, context, address, details, photo_url, formatted_date, user_id_str)
    return ConversationHandler.END

# Дополнительная функция для отправки сообщений на модерацию
def send_message_to_moderation(user_id, context, address, details, photo_url, formatted_date, user_id_str):
    city = user_data[user_id].get('CITY', '').strip()  # Убедитесь, что city - это строка
    message_parts = [address, details, city, formatted_date, user_id_str]

    # Добавляем photo_url в message_parts только если он существует и не пустой
    if photo_url and photo_url.strip():
        message_parts.append(photo_url)

    message_text = "\n".join(part for part in message_parts if part)  # Теперь все элементы - строки
    message_text = "Опублікувати наступну адресу?\n" + message_text

    keyboard = [
        [InlineKeyboardButton("N", callback_data=f"no_{user_id}"),
         InlineKeyboardButton("YR", callback_data=f"yr_{user_id}"),
         InlineKeyboardButton("YP", callback_data=f"yp_{user_id}"),
         InlineKeyboardButton("CHATGPT", callback_data=f"chatgpt_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    sent_message = context.bot.send_message(
        chat_id=6964683351,
        text=message_text,
        reply_markup=reply_markup
    )
    user_data[user_id]['POST_ID'] = sent_message.message_id


def format_without_photo(address, details, date_time):
    message_parts = [address, details if details.strip() != '' else None, date_time]
    return "\n".join(filter(None, message_parts))

def generate_bonus_code(user_id, conn):
    cursor = conn.cursor()
    count = 0
    # Проверяем, есть ли уже активный промокод у пользователя
    cursor.execute("SELECT promocode, expiry_date, count FROM promocodes WHERE user_id = ? AND active = 1", (user_id,))
    active_promocode = cursor.fetchone()
    
    if active_promocode:
        promocode, expiry_date, count = active_promocode
        print(count)
        if count is None:
            count = 0
        if datetime.now() <= datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S'):
            return f"ПОДЕЛИСЬ ЭТИМ СООБЩЕНИЕМ С ДРУГОМ и получи PREMIUM ДОСТУП к каналу на 1 месяц:\n" \
                    f"📍 Доступ к карте адресов\n" \
                    f"🤡 Отсутствие рекламы и новостей\n" \
                    f"🚨 Уведомления об опасной зоне\n" \
                    f"💵 Участие в акции “Лучший реферал”\n\n" \
                    f"Твой бонус-код: {promocode}\n" \
                    f"Он действует 48 часов.\n\n" \
                    f"Инструкция активации для друга:\n" \
                    f"1) Зайди в бот https://t.me/sasadas_bot/\n" \
                    f"2) Выбери 'Получить бонус-код'\n" \
                    f"3) Отправь бонус-код боту.\n\n" \
                    f"Ты пригласил уже {count} подписчиков.\n" \
                    f"3 лучших реферала, каждый месяц\n" \
                    f"получают в подарок 100$. Рефералы\n" \
                    f"будут объявлены анонимно."
    # Проверка, подписан ли пользователь более 24 часов
    cursor.execute("SELECT subscribe_date FROM subscribers WHERE user_id = ?", (user_id,))
    subscribe_date = cursor.fetchone()
    bonus_code = "B" + str(random.randint(1000, 9999))
    expiry_date = datetime.now() + timedelta(minutes=1)
    cursor.execute("INSERT INTO promocodes (user_id, promocode, expiry_date, active, count) VALUES (?, ?, ?, 1, 0)",
                    (user_id, bonus_code, expiry_date.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()

    message = f"ПОДЕЛИСЬ ЭТИМ СООБЩЕНИЕМ С ДРУГОМ и получи PREMIUM ДОСТУП к каналу на 1 месяц:\n" \
                f"📍 Доступ к карте адресов\n" \
                f"🤡 Отсутствие рекламы и новостей\n" \
                f"🚨 Уведомления об опасной зоне\n" \
                f"💵 Участие в акции “Лучший реферал”\n\n" \
                f"Твой бонус-код: {bonus_code}\n" \
                f"Он действует 48 часов.\n\n" \
                f"Инструкция активации для друга:\n" \
                f"1) Зайди в бот https://t.me/sasadas_bot/\n" \
                f"2) Выбери 'Получить бонус-код'\n" \
                f"3) Отправь бонус-код боту.\n\n" \
                f"Ты пригласил уже {count} подписчиков.\n" \
                f"3 лучших реферала, каждый месяц\n" \
                f"получают в подарок 100$. Рефералы\n" \
                f"будут объявлены анонимно."

    return message
def ask_for_bonus_code(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Напиши бонус-код в чат")
    return BONUS_CODE  

def is_promo_code_active_for_user(user_id):
    conn = sqlite3.connect('subscribe.db')
    cursor = conn.cursor()
    cursor.execute("SELECT activated_by_user_id FROM promocodes WHERE active = 1")
    active_promocodes = cursor.fetchall()
    conn.close()
    for record in active_promocodes:
        activated_user_ids = record[0].split(',') if record[0] else []
        if str(user_id) in activated_user_ids:
            return True
    return False

def check_bonus_code(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    entered_code = update.message.text.strip()
    conn = sqlite3.connect('subscribe.db')
    cursor = conn.cursor()

    # Проверяем, является ли пользователь создателем промокода
    cursor.execute("SELECT user_id FROM promocodes WHERE promocode = ? AND active = 1", (entered_code,))
    promo_creator = cursor.fetchone()
    if promo_creator and promo_creator[0] == user_id:
        update.message.reply_text("Вы не можете активировать свой промокод!")
        return ConversationHandler.END

    # Проверяем, активировал ли пользователь уже какой-либо промокод
    cursor.execute("SELECT promocode, expiry_date FROM promocodes WHERE activated_by_user_id LIKE ? AND active = 1", (f'%{user_id}%',))
    active_promocodes = cursor.fetchall()

    for promocode, expiry_date in active_promocodes:
        if datetime.now() <= datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S'):
            update.message.reply_text(f"❌ У вас уже активирован промокод {promocode}. Вы не можете активировать новый промокод до его истечения.")
            conn.close()
            return ConversationHandler.END

    # Проверяем наличие введенного промокода в базе и его срок действия
    cursor.execute("SELECT user_id, promocode, expiry_date, activated_by_user_id, count FROM promocodes WHERE promocode = ? AND active = 1", (entered_code,))
    code_data = cursor.fetchone()

    if code_data:
        promo_user_id, promocode, expiry_date, activated_user_ids_str, count = code_data
        expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S')

        if not isinstance(activated_user_ids_str, str):
            activated_user_ids_str = str(activated_user_ids_str)
        
        activated_user_ids = activated_user_ids_str.split(',') if activated_user_ids_str else []
        
        if datetime.now() <= expiry_date:
            if str(user_id) not in activated_user_ids:
                activated_user_ids.append(str(user_id))
                new_user_ids_str = ','.join(activated_user_ids)
                new_count = count + 1
                cursor.execute("UPDATE promocodes SET activated_by_user_id = ?, count = ? WHERE promocode = ?", (new_user_ids_str, new_count, entered_code))
                conn.commit()
                update.message.reply_text(
                    "✅ Ваш код успешно активирован. Ваш Premium доступ активирован.\n\n"
                    "🤝 Чтобы помочь нашему каналу развиваться, поделитесь бонусным кодом со своими друзьями.\n\n"
                    "👉 Или просто попросите его подписаться на нашего бота: https://t.me/sasadas_bot/"
                )

                congratulatory_message = (
                    f"🎁 Поздравляем! Кто-то только что активировал ваш бонус-код и вы получили +1 реферала. "
                    f"Вы оба получаете +30 дней Premium подписки на бота, а также шанс получить 100$ в конце месяца. "
                    f"Рефералы будут объявлены анонимно. Деньги зачислены на USDT кошелек.\n\n"
                    f"🤝 Спасибо за помощь проекту. Это очень важно для нас."
                )
                context.bot.send_message(chat_id=promo_user_id, text=congratulatory_message)
            
            else:
                update.message.reply_text("❌ Вы уже активировали этот промокод.")
            return ConversationHandler.END
        else:
            update.message.reply_text(
                "❌ Ваш бонус-код, к сожалению, просрочен.\n\n"
                "🤝 Но вы можете получить Premium, и помочь нашему каналу развиваться, если поделитесь “Бонус-кодом” с любым своим другом."
            )

            return ConversationHandler.END
    else:
        update.message.reply_text("❌ Неверный промокод.")
        return ConversationHandler.END
    conn.close()


def share_bonus_code(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    conn = sqlite3.connect('subscribe.db') 
    response = generate_bonus_code(user_id, conn)
    update.message.reply_text(response)
    conn.close()



def broadcast(update: Update, context: CallbackContext, user_ids) -> None:
    message = update.message
    if message.text:
        for user_id in user_ids:
            print(user_id)
            try:
                # Attempt to send the message
                context.bot.send_message(chat_id=user_id, text=message.text)
            except Exception as e:
                # Log the error and continue with the next user ID
                print(f"Failed to send message to {user_id}: {e}")
    elif message.photo:
        # Send the highest quality photo
        photo = message.photo[-1].file_id
        for user_id in user_ids:
            try:
                context.bot.send_photo(chat_id=user_id, photo=photo)
            except Exception as e:
                # Log the error and continue with the next user ID
                print(f"Failed to send message to {user_id}: {e}")
    elif message.document:
        # Send document
        document = message.document.file_id
        for user_id in user_ids:
            try:
                context.bot.send_document(chat_id=user_id, document=document)
            except Exception as e:
                # Log the error and continue with the next user ID
                print(f"Failed to send message to {user_id}: {e}")
def upload_image_to_imgur(image_path, client_id):
    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": f"Client-ID {client_id}"}
    with open(image_path, "rb") as image:
        img = image.read()
    response = requests.post(url, headers=headers, files={"image": img})
    data = response.json()
    if response.status_code == 200:
        return data["data"]["link"]
    else:
        print(f"Ошибка загрузки изображения: {data}")
        return None

def broadcast_moderator(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    if user_id in moderator_ids:
        keyboard = [
            [InlineKeyboardButton("Всем городам", callback_data='broadcast_all')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Выберите опцию рассылки:", reply_markup=reply_markup)
        return CHOOSE_city
    else:
        update.message.reply_text("У вас нет прав на использование этой команды.")
        return ConversationHandler.END

def broadcast_to_all_cities(update, context):
    message = update.message
    caption = message.caption if message.caption else None
    content = message.text if message.text else None
    photo = message.photo[-1].file_id if message.photo else None
    document = message.document.file_id if message.document else None

    user_ids = dbs.get_all_users()
    for user_tuple in user_ids:
        user_id = user_tuple[0]  # Extract user_id from tuple
        try:
            for city_channel in channelsss:
                res1 = is_user_in_channel(bot, city_channel, user_id)
                if res1:
                    break
            if res1:
                continue

            if photo and caption:
                context.bot.send_photo(chat_id=user_id, photo=photo, caption=caption)
            elif content:
                context.bot.send_message(chat_id=user_id, text=content)
            elif photo:
                context.bot.send_photo(chat_id=user_id, photo=photo)
            elif document:
                context.bot.send_document(chat_id=user_id, document=document)
        except Unauthorized:
            print(f"User {user_id} has blocked the bot or deleted their account.")
            continue
        except Exception as e:
            print(f"Failed to send message to user {user_id}: {e}")
            continue

    for city, channel_id in city_channels.items():
        try:
            if photo and caption:
                context.bot.send_photo(chat_id=channel_id, photo=photo, caption=caption)
            elif content:
                context.bot.send_message(chat_id=channel_id, text=content)
            elif photo:
                context.bot.send_photo(chat_id=channel_id, photo=photo)
            elif document:
                context.bot.send_document(chat_id=channel_id, document=document)
        except Exception as e:
            print(f"Failed to send message to channel {channel_id}: {e}")

    update.message.reply_text("Content sent to all city channels and users.")

    return ConversationHandler.END



def broadcast_to_city(update: Update, context: CallbackContext) -> int:
    city_file = context.user_data.get('city_file')
    city_name = context.user_data.get('city_name')
    print(city_file)
    message = update.message

    if not city_file:
        update.message.reply_text("No city file found.")
        return ConversationHandler.END


    caption = message.caption if message.caption else None
    content = message.text if message.text else None
    photo = message.photo[-1].file_id if message.photo else None
    document = message.document.file_id if message.document else None

    try:
        user_ids = dbs.get_users_by_city(city_name)
        print(user_ids)
        print(f"sadasadsasada {city_name}")
        for user_id in user_ids:
                for city_channel in channelsss:
                    res1 = is_user_in_channel(bot, city_channel, user_id)
                    if res1 == True:
                        break
                if res1 == True:
                    continue
                try:

                    if photo and caption:
                        context.bot.send_photo(chat_id=user_id, photo=photo, caption=caption)
                    elif content:
                        context.bot.send_message(chat_id=user_id, text=content)
                    elif photo:
                        context.bot.send_photo(chat_id=user_id, photo=photo)
                    elif document:
                        context.bot.send_document(chat_id=user_id, document=document)
                except Exception as e:
                    print(e)
        for filek, channel_id in file_to_channel_id.items():
            if filek == city_file:
                if photo and caption:
                    context.bot.send_photo(chat_id=channel_id, photo=photo, caption=caption)
                elif content:
                    context.bot.send_message(chat_id=channel_id, text=content)
                elif photo:
                    context.bot.send_photo(chat_id=channel_id, photo=photo)
                elif document:
                    context.bot.send_document(chat_id=channel_id, document=document)

        update.message.reply_text(f"Content sent to users in {city_file}.")
    except Exception as e:
        update.message.reply_text(f"Failed to send messages: {e}")
    
    return ConversationHandler.END





def choose_city(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user_id = update.effective_user.id  # Get user_id from the effective user
    chosen_city = query.data
    if user_id not in user_data:
        user_data[user_id] = {}  # Initialize an empty dict for the user

    if chosen_city == 'broadcast_all':
        keyboard = [
            [InlineKeyboardButton("Відмінити", callback_data='stop_pls')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Введите сообщение для рассылки:", reply_markup=reply_markup)
        return BROADCAST_ALL
    elif chosen_city in city_files:
        # Now we're sure user_id is initialized, so we can safely assign city
        user_data[user_id]['city'] = chosen_city
        context.user_data['city_name'] = chosen_city
        context.user_data['city_file'] = city_files[chosen_city]
        print(chosen_city)
        dbs.add_user(user_id, chosen_city)
        print(f"ALL users: {dbs.get_all_users()}")
        query.edit_message_text(text=f"Введите сообщение для рассылки пользователям из {chosen_city}:")
        return BROADCAST_MSG

    query.edit_message_text(text="Некорректный выбор города.")
    return ConversationHandler.END

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    user_data[user_id] = {}
    update.message.reply_text(
        "Дякую що підписалися на робота WTU. Ми будемо повідомляти Вас про актуальні адреси WTU.\n\n"
    )

    city(update, context)

def city(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    cities = [
        "Київ", "Харків", "Одеса", "Львів", "Дніпро", "Запоріжжя", "Миколаїв",
        "Івано-Франківськ", "Кривий Ріг", "Рівне", "Чернівці", "Черкаси", "Суми",
        "Житомир", "Кропивницький", "Тернопіль", "Луцьк", "Хмельницький", "Полтава",
        "Ужгород", "Чернігів", "Вінниця", "Херсон"
    ]
    keyboard = [[InlineKeyboardButton(cities[i], callback_data=cities[i]),
                 InlineKeyboardButton(cities[i + 1], callback_data=cities[i + 1])]
                 for i in range(0, len(cities) - 1, 2)]
    if len(cities) % 2 != 0:
        keyboard.append([InlineKeyboardButton(cities[-1], callback_data=cities[-1])])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Вибери місто:', reply_markup=reply_markup)


def yr_moderation(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user_id_to_edit = int(query.data.split('_')[1])  # Извлечение user_id из callback_data

    context.user_data['EDIT_USER_ID'] = user_id_to_edit  # Сохранение user_id для дальнейшего использования
    print(user_id_to_edit)
    # Переход к шагу ввода точного адреса
    keyboard = [
        [InlineKeyboardButton("Публикуем", callback_data=f"publish_address_{user_id_to_edit}"),
         InlineKeyboardButton("Не публикуем", callback_data=f"do_not_publish_address_{user_id_to_edit}")],
        
        # Other buttons...
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.reply_text(
        "<b>1) Введите точный адрес (обязательно)</b>\n"
        "Чем точнее будет адрес, тем лучше.\n"
        "Например: Богдана Хмельницкого, 33.",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return EXACT_ADDRESS  # Переход к следующему состоянию диалога

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_id = query.message.chat_id
    chosen_city = query.data
    
    if query.data == 'skip_photo':
        users_datas3 = {}
        if 'EDIT_USER_ID' in context.user_data:
            user_id_to_edit = context.user_data['EDIT_USER_ID']
            if user_id_to_edit in user_data:
                post_id = user_data[user_id_to_edit].get('POST_ID')
                city_to_check = user_data[user_id_to_edit]['city']
                address = user_data[user_id_to_edit]['EXACT_ADDRESS']
                details = user_data[user_id_to_edit].get('DETAILS', '')
                user_data[user_id_to_edit].pop('PHOTO', None)
                date_time = user_data[user_id_to_edit].get('DATE_TIME', '')
                city_channel = city_channels.get(city_to_check)
                dbs.increment_daily_address(user_id_to_edit)
                dbs.increment_weekly_address(user_id_to_edit)
                if city_channel:
                    try:
                        context.bot.send_message(
                            chat_id=city_channel,
                            text=format_without_photo(address, details, date_time)
                        )
                    except Exception as e:
                        print(f"Не удалось отправить сообщение в канал {city_channel}: {e}")
                else:
                    query.answer(text="Канал для данного города не найден.")
            city_file = city_files.get(city_to_check)
            if city_file:
                user_ids = dbs.get_users_by_city(city_to_check)
                for user_id in user_ids:
                    res1 = is_user_in_channel(bot, city_channel, user_id)
                    if res1 == True:
                        continue
                    try:
                        context.bot.send_message(chat_id=user_id, text=format_without_photo(address, details, date_time))
                
                    except Exception as e:
                        print(f"Failed to send message to user {user_id}: {e}")
                context.user_data.clear()
                return ConversationHandler.END
            else:
                print(f"Файл данных для города {city_to_check} не найден.")
                context.user_data.clear()  # Используйте clear() для очистки данных
                return ConversationHandler.END
        print('GGG')
        city = user_data[user_id].get('city')
        if city is None:
            query.message.reply_text("Выберите город с помощью команды /city!")
            return ConversationHandler.END
        query.message.reply_text("<b>Дякуємо, що залишили нову адресу. Ваша інформація буде перебувати на перевірці, і незабаром буде опублікована.</b>", parse_mode='HTML')
        now = datetime.now()
        month_name = ukrainian_months[now.month]  # Get Ukrainian month name
        formatted_date = now.strftime(f"%d {month_name}, %H:%M")  # Format the date
        user_data[user_id]['DATE_TIME'] = formatted_date
        user_data['user_id'] = user_id
        context.user_data['city_name'] = city
        user_data[user_id]['user_id'] = user_id
        if city in city_files:
            context.user_data['city_file'] = city_files[city]
        if user_data[user_id]['DETAILS']:
            process_message_for_publication(update, context)
            return ConversationHandler.END
        else:
            process_message_for_publication(update, context)
            return ConversationHandler.END
    if query.data == 'stop_pls':
        query.message.reply_text("Відмінилось!")
        return ConversationHandler.END
    if query.data == 'skip_details':
        user_data[user_id]['DETAILS'] = ""
        keyboard = [
        [InlineKeyboardButton("Пропустити", callback_data='skip_photo')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=user_id, text="<b>3) Фото місця (необязательно)</b>", parse_mode='HTML', reply_markup=reply_markup)
        return PHOTO
    if user_id not in user_data:
        user_data[user_id] = {}
    if query.data.startswith('publish_address_'):
        data_parts = query.data.split('_')
        user_id_to_edit = int(data_parts[-1])  # Get the last part of the split which should be the user ID

        keyboard = [
            [InlineKeyboardButton("Публикуем", callback_data=f"publish_details_{user_id_to_edit}"),
            InlineKeyboardButton("Не публикуем", callback_data=f"do_not_publish_details_{user_id_to_edit}")],
            # Other buttons...
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text("<b>2) Деталі місця (необязательно)</b>\nУкажите где вы это заметили\nНапр: Рядом красная вывеска, и магазин Море Пива", reply_markup=reply_markup, parse_mode='HTML')
        
        return DETAILS
    elif query.data.startswith('no_post'):
        channel_data.clear()
        query.edit_message_text("❌ ПОСТ ОТКЛОНЕН")
        return
    elif query.data.startswith('yr_post'):
        update.effective_message.reply_text(
            "Введите новое сообщение"
        )
        return EXACT_ADDR
    elif query.data.startswith('yp_post'):
        try:
            message = channel_data['TEXT']
            channel_name = channel_data['CITY']
        except Exception as e:
            print(e)
            return
        channel_info = dbm.get_channel_info(channel_name)
        
        user_ids = dbs.get_users_by_city(channel_info.get('user_file'))
        print(user_ids)
        for user_id in user_ids:
            print(user_id)
            for city_channel in channelsss:
                res1 = is_user_in_channel(bot, city_channel, user_id)
                if res1 == True:
                    break
            if res1 == True:
                continue
            try:
                print('TRY')
                bot.send_message(chat_id=user_id, text=message)
                print(f'SUCCESS. MESSAGE: {message}')
            except Exception as e:
                print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
        channel_id = channel_info["channel_id"]
        try:
            bot.send_message(chat_id=channel_id, text=message)
        except Exception as e:
            print(e)
        query.edit_message_text(text="✅ ПОСТ ОПУБЛИКОВАН ")
    elif query.data.startswith('publish_details_'):
        data_parts = query.data.split('_')
        user_id_to_edit = int(data_parts[-1])

        keyboard = [
            [InlineKeyboardButton("Публикуем", callback_data=f"publish_photo_{user_id_to_edit}"),
            InlineKeyboardButton("Не публикуем", callback_data=f"do_not_publish_photo_{user_id_to_edit}")],
            # Other buttons...
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text('<b>3) Фото місця (необязательно)</b>', parse_mode='HTML', reply_markup=reply_markup)
        
        return PHOTO
    elif query.data.startswith('do_not_publish_photo_'):
        data_parts = query.data.split('_')
        user_id_to_edit = int(data_parts[-1])
        user_data[user_id_to_edit]['PHOTO'] = ""
        if user_id_to_edit in user_data:
            post_id = user_data[user_id_to_edit].get('POST_ID')
            city_to_check = user_data[user_id_to_edit]['city']
            address = user_data[user_id_to_edit]['EXACT_ADDRESS']
            details = user_data[user_id_to_edit].get('DETAILS', '')
            photo = user_data[user_id_to_edit].get('PHOTO', '')
            date_time = user_data[user_id_to_edit].get('DATE_TIME', '')
            info_dbs.add_address(address, details)
            dbs.increment_daily_address(user_id_to_edit)
            dbs.increment_weekly_address(user_id_to_edit)
            city_channel = city_channels.get(city_to_check)
            if address and detals:
                if city_channel:
                    try:
                        context.bot.send_message(
                            chat_id=city_channel,
                            text=format_message(address, details, photo, date_time)
                        )
                    except Exception as e:  
                        print(f"Не удалось отправить сообщение в канал {city_channel}: {e}")
                else:
                    query.answer(text="Канал для данного города не найден.")

                city_file = city_files.get(city_to_check)
                if city_file:
                    user_ids = dbs.get_users_by_city(city_to_check)
                    for user_id in user_ids:
                        res1 = is_user_in_channel(bot, city_channel, user_id)
                        if res1 == True:
                            continue
                        try:
                            context.bot.send_message(chat_id=user_id, text=format_message(address, details, photo, date_time))
                        except Exception as e:
                            print(f"Failed to send message to user {user_id}: {e}")

                else:
                    print(f"Файл данных для города {city_to_check} не найден.")
        post_id = user_data[user_id_to_edit].get('POST_ID')
        print("DSDADSADA")
        print(user_id_to_edit)
        print(post_id)
        if post_id and user_id_to_edit in user_data:
            try:
                context.bot.edit_message_text(chat_id=user_id_to_edit, 
                                            message_id=post_id, 
                                            text="✅ ПОСТ ОПУБЛИКОВАН")
            except Exception as e:
                print(f"Не удалось отредактировать сообщение: {e}")
        context.user_data.clear()
        return ConversationHandler.END
    elif query.data.startswith('publish_photo_'):
        data_parts = query.data.split('_')
        user_id_to_edit = int(data_parts[-1])
        if user_id_to_edit in user_data:
            post_id = user_data[user_id_to_edit].get('POST_ID')
            city_to_check = user_data[user_id_to_edit]['city']
            address = user_data[user_id_to_edit]['EXACT_ADDRESS']
            details = user_data[user_id_to_edit].get('DETAILS', '')
            photo = user_data[user_id_to_edit].get('PHOTO', '')
            date_time = user_data[user_id_to_edit].get('DATE_TIME', '')
            info_dbs.add_address(address, details)
            dbs.increment_daily_address(user_id_to_edit)
            dbs.increment_weekly_address(user_id_to_edit)
            city_channel = city_channels.get(city_to_check)
            if city_channel:
                try:
                    context.bot.send_message(
                        chat_id=city_channel,
                        text=format_message(address, details, photo, date_time)
                    )
                except Exception as e:  
                    print(f"Не удалось отправить сообщение в канал {city_channel}: {e}")
            else:
                query.answer(text="Канал для данного города не найден.")

            city_file = city_files.get(city_to_check)
            if city_file:
                user_ids = dbs.get_users_by_city(city_to_check)
                for user_id in user_ids:
                    res1 = is_user_in_channel(bot, city_channel, user_id)
                    if res1 == True:
                        continue
                    try:
                        context.bot.send_message(chat_id=user_id, text=format_message(address, details, photo, date_time))
                    except Exception as e:
                        print(f"Failed to send message to user {user_id}: {e}")

            else:
                print(f"Файл данных для города {city_to_check} не найден.")
        post_id = user_data[user_id_to_edit].get('POST_ID')
        print("DSDADSADA")
        print(user_id_to_edit)
        print(post_id)
        if post_id and user_id_to_edit in user_data:
            try:
                context.bot.edit_message_text(chat_id=user_id_to_edit, 
                                            message_id=post_id, 
                                            text="✅ ПОСТ ОПУБЛИКОВАН")
            except Exception as e:
                print(f"Не удалось отредактировать сообщение: {e}")
        context.user_data.clear()
        return ConversationHandler.END
    elif query.data.startswith('do_not_publish_details_'):
        data_parts = query.data.split('_')
        user_id_to_edit = int(data_parts[-1])  # Get the last part of the split which should be the user ID

        print('PUBLISH ADDRES')
        if user_id_to_edit in user_data:
            user_data[user_id_to_edit]['DETAILS'] = ""
        keyboard = [
            [InlineKeyboardButton("Публикуем", callback_data=f"publish_photo_{user_id_to_edit}"),
            InlineKeyboardButton("Не публикуем", callback_data=f"do_not_publish_photo_{user_id_to_edit}")],
            # Other buttons...
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text('<b>3) Фото місця (необязательно)</b>', parse_mode='HTML', reply_markup=reply_markup)
        return PHOTO
    elif query.data.startswith('do_not_publish_add'):
        data_parts = query.data.split('_')
        user_id_to_edit = int(data_parts[-1])  # Get the last part of the split which should be the user ID

        print('PUBLISH ADDRES')
        if user_id_to_edit in user_data:
            user_data[user_id_to_edit]['EXACT_ADDRESS'] = ""
        keyboard = [
            [InlineKeyboardButton("Публикуем", callback_data=f"publish_details_{user_id_to_edit}"),
            InlineKeyboardButton("Не публикуем", callback_data=f"do_not_publish_details_{user_id_to_edit}")],
            # Other buttons...
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text("<b>2) Деталі місця (необязательно)</b>\nУкажите где вы это заметили\nНапр: Рядом красная вывеска, и магазин Море Пива", reply_markup=reply_markup, parse_mode='HTML')
        return DETAILS
    elif query.data.startswith('no_'):
        user_id_to_delete = int(query.data.split('_')[1])
        post_id_to_delete = user_data[user_id_to_delete].get('POST_ID')

        # Удаляем пост из базы данных
        if post_id_to_delete is not None:
            dbs.delete_post(post_id_to_delete)

        try:
            query.edit_message_text(text="❌ ПОСТ ОТКЛОНЕН")
            return ConversationHandler.END
        except Exception as e:
            print(e)
            return ConversationHandler.END


    elif query.data.startswith('yr_'):
        return yr_moderation(update, context)
    elif query.data.startswith('chatgpt_'):
        try:
            process_message_for_publication(update, context)
            query.edit_message_text(text="This post has already been published")
        except Exception as e:
            print(e)
    elif query.data.startswith('yp'):
        user_id_to_edit = int(query.data[3:])
        if user_id_to_edit in user_data:
            post_id = user_data[user_id_to_edit].get('POST_ID')
            city_to_check = user_data[user_id_to_edit]['city']
            address = user_data[user_id_to_edit]['EXACT_ADDRESS']
            details = user_data[user_id_to_edit].get('DETAILS', '')
            photo = user_data[user_id_to_edit].get('PHOTO', '')
            date_time = user_data[user_id_to_edit].get('DATE_TIME', '')
            info_dbs.add_address(address, details)
            city_channel = city_channels.get(city_to_check)
            dbs.increment_daily_address(user_id_to_edit)
            dbs.increment_weekly_address(user_id_to_edit)
            if city_channel:
                try:
                    context.bot.send_message(
                        chat_id=city_channel,
                        text=format_message(address, details, photo, date_time)
                    )
                except Exception as e:  
                    print(f"Не удалось отправить сообщение в канал {city_channel}: {e}")
            else:
                query.answer(text="Канал для данного города не найден.")

            city_file = city_files.get(city_to_check)
            if city_file:
                user_ids = dbs.get_users_by_city(city_to_check)
                for user_id in user_ids:
                    res1 = is_user_in_channel(bot, city_channel, user_id)
                    if res1 == True:
                        continue
                    try:
                        context.bot.send_message(chat_id=user_id, text=format_message(address, details, photo, date_time))
                    except Exception as e:
                        print(f"Failed to send message to user {user_id}: {e}")


            else:
                print(f"Файл данных для города {city_to_check} не найден.")
            query.edit_message_text(text="✅ ПОСТ ОПУБЛИКОВАН ")
    else:
        user_data[user_id]['city'] = query.data
        dbs.add_user(user_id, query.data)
        print(dbs.get_all_users())
        print("City set to:", user_data[user_id]['city'])  # Debug print
        query.edit_message_text(text=f"Вибране місто: {query.data}")

        reply_keyboard = [
            ["Повідомити нову адресу"],
            ["Получить бонус-код"],
            ["Активировать промокод"]
        ]
        if user_id in moderator_ids:
            reply_keyboard.append(["Рассылка модератором"])
        if is_promo_code_active_for_user(user_id):
            reply_keyboard.append(["Відкрити карту адрес"])
        update.effective_message.reply_text(
            'Оберіть опцію:',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
        )

def new_address(update: Update, context: CallbackContext) -> int:
    user_id = update.message.chat_id

    current_date = datetime.now()
    if manage_limits.can_send_address(user_id, current_date):
        if user_id in user_data and 'PHOTO' in user_data[user_id]:
            del user_data[user_id]['PHOTO']
        keyboard = [
            [InlineKeyboardButton("Відмінити", callback_data='stop_pls')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("<b>1) Введите точный адрес (обязательно)</b>\nЧем точнее будет адрес, тем лучше.\nНапр: Богдана Хмельницкого, 33.", parse_mode='HTML', reply_markup=reply_markup)
        return EXACT_ADDRESS
    else:
        update.message.reply_text("Вы не можете больше подать адрес")
        return ConversationHandler.END

def exact_address(update: Update, context: CallbackContext) -> int:
    print("EXACT ADDRESS")
    text = update.message.text
    user_id = update.message.chat_id
    if user_id not in user_data:
        user_data[user_id] = {}
        print('user_id in exact address not in user_data')
    keyboard = [
        [InlineKeyboardButton("Пропустити", callback_data='skip_details')]
    ]
    print('reply_markup')
    reply_markup = InlineKeyboardMarkup(keyboard)
    if 'EDIT_USER_ID' in context.user_data:
        print('edit user id in exact adddress')
        user_id_to_edit = context.user_data['EDIT_USER_ID']
        print(user_id_to_edit)
        print(f'USER ID TO EDIT IN EXACT {user_id_to_edit}')
        keyboard = [
            [InlineKeyboardButton("Публикуем", callback_data=f"publish_details_{user_id_to_edit}"),
            InlineKeyboardButton("Не публикуем", callback_data=f"do_not_publish_details_{user_id_to_edit}")],
            # Other buttons...
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        user_data[user_id_to_edit]['EXACT_ADDRESS'] = text
        update.message.reply_text("<b>2) Деталі місця (необязательно)</b>\nУкажите где вы это заметили\nНапр: Рядом красная вывеска, и магазин Море Пива", reply_markup=reply_markup, parse_mode='HTML')
        return DETAILS
    else:
        user_data[user_id]['EXACT_ADDRESS'] = text
        update.message.reply_text("<b>2) Деталі місця (необязательно)</b>\nУкажите где вы это заметили\nНапр: Рядом красная вывеска, и магазин Море Пива", reply_markup=reply_markup, parse_mode='HTML')
        return DETAILS


def details(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    user_id = update.message.chat_id
    if user_id not in user_data:
        user_data[user_id] = {}
    keyboard = [
        [InlineKeyboardButton("Пропустити", callback_data='skip_photo')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if 'EDIT_USER_ID' in context.user_data:
        print('DETAILS UPDATE')
        user_id_to_edit = context.user_data['EDIT_USER_ID']
        user_data[user_id_to_edit]['DETAILS'] = text
        keyboard = [
            [InlineKeyboardButton("Публикуем", callback_data=f"publish_photo_{user_id_to_edit}"),
            InlineKeyboardButton("Не публикуем", callback_data=f"do_not_publish_photo_{user_id_to_edit}")],
            # Other buttons...
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            query.message.reply_text('<b>3) Фото місця (необязательно)</b>', parse_mode='HTML', reply_markup=reply_markup)
        except Exception as e:
            update.message.reply_text('<b>3) Фото місця (необязательно)</b>', parse_mode='HTML', reply_markup=reply_markup)
        return PHOTO
    user_data[user_id]['DETAILS'] = text
    update.message.reply_text("<b>3) Фото місця (необязательно)</b>", parse_mode='HTML', reply_markup=reply_markup)
    return PHOTO



def updaterPhoto(update: Update, context: CallbackContext) -> int:
    print("UPDATER PHOTO")
    user_id = update.message.chat_id
    user_id_to_edit = context.user_data.get('EDIT_USER_ID', user_id)  # getting the user id to edit

    if update.message.photo:
        photo_file = update.message.photo[-1].get_file()
        photo_path = f'imgs/user_{user_id}_photo.jpg'
        photo_file.download(photo_path)
        imgur_url = upload_image_to_imgur(photo_path, "a4d7dd18d36705f")

        if imgur_url:
            user_data[user_id_to_edit]['PHOTO'] = imgur_url
        else:
            update.message.reply_text("Не удалось загрузить фото.")

    now = datetime.now()
    month_name = ukrainian_months[now.month]
    formatted_date = now.strftime(f"%d {month_name}, %H:%M")
    user_data[user_id_to_edit]['DATE_TIME'] = formatted_date
    if True:
        if user_id_to_edit in user_data:
            post_id = user_data[user_id_to_edit].get('POST_ID')
            city_to_check = user_data[user_id_to_edit]['city']
            address = user_data[user_id_to_edit]['EXACT_ADDRESS']
            details = user_data[user_id_to_edit].get('DETAILS', '')
            photo = user_data[user_id_to_edit].get('PHOTO', '')
            date_time = user_data[user_id_to_edit].get('DATE_TIME', '')
            dbs.increment_daily_address(user_id_to_edit)
            dbs.increment_weekly_address(user_id_to_edit)

            if address and details:
                city_channel = city_channels.get(city_to_check)
                if city_channel:
                    try:
                        context.bot.send_message(
                            chat_id=city_channel,
                            text=format_message(address, details, photo, date_time)
                        )
                    except Exception as e:
                        print(f"Не удалось отправить сообщение в канал {city_channel}: {e}")
                else:
                    query.answer(text="Канал для данного города не найден.")
                city_file = city_files.get(city_to_check)
                if city_file:
                    user_ids = dbs.get_users_by_city(city_to_check)
                    for user_id in user_ids:
                        try:
                            context.bot.send_message(chat_id=user_id, text=format_message(address, details, photo, date_time))
                        except Exception as e:
                            print(f"Failed to send message to user {user_id}: {e}")

                else:
                    print(f"Файл данных для города {city_to_check} не найден.")
    post_id = user_data[user_id_to_edit].get('POST_ID')
    print("DSDADSADA")
    print(user_id_to_edit)
    print(post_id)
    if post_id and user_id_to_edit in user_data:
        try:
            context.bot.edit_message_text(chat_id=user_id_to_edit, 
                                          message_id=post_id, 
                                          text="✅ ПОСТ ОПУБЛИКОВАН")
        except Exception as e:
            print(f"Не удалось отредактировать сообщение: {e}")

    context.user_data.clear()
    return ConversationHandler.END
def compose_final_message(address, details, photo_url):
    return f"Адрес: {address}\nКомментарий: {details}\nФото: {photo_url}"


def publish_message_city(update: Update, context: CallbackContext):
    user_id = user_data['user_id']
    city_file = context.user_data['city_file']
    city_name = context.user_data['city_name']

    address = user_data[user_id].get('EXACT_ADDRESS', '').strip()
    details = user_data[user_id].get('DETAILS', '').strip()
    photo = user_data[user_id].get('PHOTO', '').strip()
    print(f"PHOTO IS : {photo}")
    date_time = user_data[user_id].get('DATE_TIME', '').strip()
    text = format_message(address, details, photo, date_time)
    try:
        user_ids = dbs.get_users_by_city(city_name)
        print(user_ids)
        print(city_name)
        for user_id in user_ids:
            print(user_id)
            for city_channel in channelsss:
                res1 = is_user_in_channel(bot, city_channel, user_id)
                if res1 == True:
                    break
            if res1 == True:
                continue
            try:
                context.bot.send_message(chat_id=user_id, text=text)
            except Exception as e:
                print(e)
        print('USER_ID SSWAPPED')
        for filek, channel_id in file_to_channel_id.items():
            print(filek)
            print(city_file)
            if filek == city_file:
                print('URAAAAAA')
                context.bot.send_message(chat_id=channel_id, text=text)
    except Exception as e:
        print(e)


def filter_and_translate_details(details):
    openai.api_key = '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'
    print(f'OPENAI {details}')
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301",
            messages=[
                {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости. Отвечай тільки 'NO.' и 'YES.' согласно запросу"},
                {"role": "user", "content": f"Сообщение содержит рекламный характера? Напиши 'YES.' если хоть частично содержит, напиши 'NO.' если не содержит абсолютно. Сообщение: '{details}'"}
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
                {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости. Отвечай только 'NO.' и 'YES.' согласно запросу"},
                {"role": "user", "content": f"Сообщение содержит грубую лексику или ругательства? Напиши 'YES.' если хоть частично содержит, напиши 'NO.' если не содержит абсолютно. Сообщение: '{details}'"}
            ]
        )
        print(response1['choices'][0]['message']['content'])
        if response1['choices'][0]['message']['content'] == "YES.":
            return 404
        print('STARTING RESPONSE2')
        response2 = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301",
            messages=[
                {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости. Отвечай только 'NO.' и 'YES.' согласно запросу"},
                {"role": "user", "content": f"Сообщение похоже на комментарий описанывающий местоположение или направление? Напиши 'YES.' если хоть частично содержит, напиши 'NO.' если не содержит абсолютно. Сообщение: '{details}'"}
            ]
        )
        print(response2['choices'][0]['message']['content'])
        if response2['choices'][0]['message']['content'] == "NO.":
            return 404

        # Connect to Google Translate API using API Key
        api_key = 'AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw'
        service = googleapiclient.discovery.build('translate', 'v2', developerKey=api_key)
        translated_details = service.translations().list(source='ru', target='uk', q=details).execute()
        translated_text = translated_details['translations'][0]['translatedText']
        return translated_text
    except Exception as e:
        print(e)
        return details
def filter_and_translate_address(address):
    openai.api_key = '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'
    print(f'OPENAI {address}')
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301",
            messages=[
                {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости. Отвечай тільки 'NO.' и 'YES.' согласно запросу"},
                {"role": "user", "content": f"Сообщение далее содержит примерное описание характера местоположения, примерного адреса (рядом с чем-то) или направления движения (в сторону)? Напиши 'YES.' если хоть частично содержит, напиши 'NO.' если не содержит абсолютно. Сообщение: '{address}'"}
            ]
        )
        print('FIRST RESPONCE')
        print(res['choices'][0]['message']['content'])
        if res['choices'][0]['message']['content'] == "NO.":
            print('YES OF FIRST RESPONSE')
            return 404
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301",
            messages=[
                {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости. Отвечай тільки 'NO.' и 'YES.' согласно запросу"},
                {"role": "user", "content": f"Сообщение содержит рекламный характера? Напиши 'YES.' если хоть частично содержит, напиши 'NO.' если не содержит абсолютно. Сообщение: '{address}'"}
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
                {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости. Отвечай только 'NO.' и 'YES.' согласно запросу"},
                {"role": "user", "content": f"Сообщение содержит грубую лексику или ругательства? Напиши 'YES.' если хоть частично содержит, напиши 'NO.' если не содержит абсолютно. Сообщение: '{address}'"}
            ]
        )
        print(response1['choices'][0]['message']['content'])
        if response1['choices'][0]['message']['content'] == "YES.":
            return 404
        print('STARTING RESPONSE2')
        response2 = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301",
            messages=[
                {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости. Отвечай только 'NO.' и 'YES.' согласно запросу"},
                {"role": "user", "content": f"Сообщение похоже на комментарий описанывающий местоположение или направление? Напиши 'YES.' если хоть частично содержит, напиши 'NO.' если не содержит абсолютно. Сообщение: '{address}'"}
            ]
        )
        print(response2['choices'][0]['message']['content'])
        if response2['choices'][0]['message']['content'] == "NO.":
            return 404

        # Connect to Google Translate API using API Key
        api_key = 'AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw'
        service = googleapiclient.discovery.build('translate', 'v2', developerKey=api_key)
        translated_address = service.translations().list(source='ru', target='uk', q=address).execute()
        translated_text = translated_address['translations'][0]['translatedText']
        return translated_text
    except Exception as e:
        print(e)
        return details
def send_to_chat_gpt(prompt):
    openai.api_key = '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'
    try:

        print(prompt)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301",
            messages=[
                {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости."},
                {"role": "user", "content": prompt}
            ]
        )
    except Exception as e:
        print(e)
    return response['choices'][0]['message']['content']

def exact_post_addres(update: Update, context: CallbackContext):
    print("POST EXACT ADDRESS")
    new_text = update.message.text
    channel_data['TEXT'] = new_text
    message = channel_data['TEXT']
    post_id = channel_data['POST_ID']
    try:
        channel_name = channel_data['CITY']
    except Exception as e:
        print(e)
        return
    channel_info = dbm.get_channel_info(channel_name)
    
    user_ids = dbs.get_users_by_city(channel_info.get('user_file'))
    print(user_ids)
    for user_id in user_ids:
        print(user_id)
        for city_channel in channelsss:
            res1 = is_user_in_channel(bot, city_channel, user_id)
            if res1 == True:
                break
        if res1 == True:
            continue
        try:
            print('TRY')
            bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
    channel_id = channel_info["channel_id"]
    try:
        bot.send_message(chat_id=channel_id, text=message)
    except Exception as e:
        print(e)
    if post_id:
        update.message.reply_text("SUCCESS!")
        try:
            context.bot.edit_message_text(chat_id=6964683351, 
                                          message_id=post_id, 
                                          text="✅ ПОСТ ОПУБЛИКОВАН")
        except Exception as e:
            print(f"Не удалось отредактировать сообщение: {e}")
    return ConversationHandler.END
def photo(update, context: CallbackContext) -> int:
    
    user_id = update.message.chat_id
    if user_id not in user_data:
        user_data[user_id] = {}
    # Check if the update message actually has a photo
    if 'EDIT_USER_ID' in context.user_data:
        updaterPhoto(update, context)
        return ConversationHandler.END
    if update.message.photo:
        photo_file = update.message.photo[-1].get_file()
        photo_path = f'imgs/user_{user_id}_photo.jpg'
        photo_file.download(photo_path)
        imgur_url = upload_image_to_imgur(photo_path, "a4d7dd18d36705f")
        
        # Process the photo and update user data
        if imgur_url:
            user_data[user_id]['PHOTO'] = imgur_url
            photo_status = imgur_url  # Successfully uploaded photo URL
        else:
            user_data[user_id]['PHOTO'] = "Failed to upload photo"
            photo_status = "Не удалось загрузить фото."
            update.message.reply_text(photo_status)
    else:
        # If there's no photo, set a placeholder or skip the photo part
        photo_status = ""
    # Common details for both cases
    now = datetime.now()
    month_name = ukrainian_months[now.month]  # Ensure ukrainian_months dict is defined
    formatted_date = now.strftime(f"%d {month_name}, %H:%M")
    user_data[user_id]['DATE_TIME'] = formatted_date

    # Prepare the message text with or without the photo URL
    try:
        # Сначала соберите все части сообщения, проверяя наличие содержимого.
        address = user_data[user_id].get('EXACT_ADDRESS', '').strip()
        details = user_data[user_id].get('DETAILS', '').strip()
        city = user_data[user_id].get('city')
        if city is None:
            update.message.reply_text("Выберите город с помощью команды /city!")
            return ConversationHandler.END
        context.user_data['city_name'] = city
        if city in city_files:
            context.user_data['city_file'] = city_files[city]
        photo_status = user_data[user_id].get('PHOTO', '').strip()
        date_time = user_data[user_id].get('DATE_TIME', '').strip()
        user_id_str = str(user_id).strip()
        message_parts = [address, details if details else "", city, photo_status, date_time, user_id_str]

        # Объедините непустые строки, вставляя перенос строки между ними.
        message_text = "\n".join(part for part in message_parts if part)
        update.message.reply_text("<b>Дякуємо, що залишили нову адресу. Ваша інформація буде перебувати на перевірці, і незабаром буде опублікована.</b>", parse_mode='HTML')
        user_data['user_id'] = user_id
        process_message_for_publication(update, context)
        return ConversationHandler.END
    except Exception as e:
        print(f"PHOTO {e}")
def expire_promocodes(context: CallbackContext):
    conn = sqlite3.connect('subscribe.db')
    cursor = conn.cursor()

    # Устанавливаем статус "неактивный" для промокодов, срок действия которых истек
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("UPDATE promocodes SET active = 0 WHERE expiry_date < ?", (current_time,))
    conn.commit()
    conn.close()

def broadcast_message(update: Update, context: CallbackContext) -> int:
    user_id = update.message.chat_id
    if is_promo_code_active_for_user(user_id):
        update.message.reply_text('https://www.google.com/maps/')
    else:
        update.message.reply_text("Нема дозволу!")

    return ConversationHandler.END
def skip_photo(update: Update, context: CallbackContext) -> int:

    print(123)
    print(context.user_data)
    user_id = update.message.chat_id
    print(f"DSASADAD {user_id}")
    user_data['user_id'] = user_id
    if 'EDIT_USER_ID' in context.user_data:
        print('SKIP PHOTO DPLASJDAIOHAS9YW98FWYRQ98WFHESU89FHSA9FHD')
        context.user_data.clear()
    update.message.reply_text("<b>Дякуємо, що залишили нову адресу. Ваша інформація буде перебувати на перевірці, і незабаром буде опублікована.</b>", parse_mode='HTML')
    context.user_data.clear()
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Отменено.', reply_markup=ReplyKeyboardRemove())

async def main() -> None:
    global bot
    updater = Updater("6868089807:AAHZQOe_6ex-eKgRwzmQ2rCXLnnbcvSnbDE")
    dispatcher = updater.dispatcher
    bot = updater.bot

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(Filters.regex('^Повідомити нову адресу$'), new_address),
            CallbackQueryHandler(button, pattern='^yr_') # Добавлен YR как точка входа
        ],
        states={
            EXACT_ADDRESS: [MessageHandler(Filters.text & ~Filters.command, exact_address), CallbackQueryHandler(button, pattern='^publish_address'), CallbackQueryHandler(button, pattern='^do_not_publish_add'), CallbackQueryHandler(button, pattern='^stop_pls')],
            DETAILS: [MessageHandler(Filters.text & ~Filters.command, details), CallbackQueryHandler(button, pattern='^skip_details$'), CallbackQueryHandler(button, pattern='^do_not_publish_details_'), CallbackQueryHandler(button, pattern='^publish_details_'), CallbackQueryHandler(button, pattern='^stop_pls')],
            PHOTO: [MessageHandler(Filters.all, photo), CallbackQueryHandler(button, pattern='^skip_photo$'), CallbackQueryHandler(button, pattern='^publish_photo_'), CallbackQueryHandler(button, pattern='^do_not_publish_photo_'), CallbackQueryHandler(button, pattern='^stop_pls')]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    conv_handler_broadcast = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Рассылка модератором$'), broadcast_moderator)],
        states={
            CHOOSE_city: [CallbackQueryHandler(choose_city)],
            BROADCAST_MSG: [MessageHandler(Filters.all & ~Filters.command, broadcast_to_city)],
            BROADCAST_ALL: [MessageHandler(Filters.all & ~Filters.command, broadcast_to_all_cities), CallbackQueryHandler(button, pattern='^stop_pls')]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    conv_handler_message = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Відкрити карту адрес'), broadcast_message)],
        states={
            CHOOSE_city: [CallbackQueryHandler(choose_city)],
            BROADCAST_MSG: [MessageHandler(Filters.all & ~Filters.command, broadcast_to_city)],
            BROADCAST_ALL: [MessageHandler(Filters.all & ~Filters.command, broadcast_to_all_cities)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    conv_handler_bon_code = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Активировать промокод$'), ask_for_bonus_code)],
        states={
            BONUS_CODE: [MessageHandler(Filters.text & ~Filters.command, check_bonus_code)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]

    )

    conv_handler_edit_post = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='^yr_post')],  # Entry point for editing the post
        states={
            EXACT_ADDR: [MessageHandler(Filters.text & ~Filters.command, exact_post_addres)]  # State for exact address editing
        },
        fallbacks=[CommandHandler('cancel', cancel)]  # Fallback command
    )

    # Register the ConversationHandler in the Dispatcher
    dispatcher.add_handler(conv_handler_edit_post)

    dispatcher.add_handler(conv_handler_broadcast)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("city", city))
    dispatcher.add_handler(MessageHandler(Filters.regex('^Получить бонус-код$'), share_bonus_code))
    dispatcher.add_handler(conv_handler_message)
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(conv_handler_bon_code)
    dispatcher.add_handler(CallbackQueryHandler(button))  # Добавлен в конце
    daily_message_job = DailyMessageJob('bot.db', info_dbs, dbs)
    daily_message_job.schedule(updater)
    watcher = TelegramChannelWatcher(dbm, dbs, bot)
    print(dbm.delete_all_channels())
    dbm.get_all_channel_names()
    dbm.add_channel("kanal_pars_odessa1", "Одеса", "-1002018743530")
    dbm.add_channel("kanal_pars_odessa2", "Одеса", "-1002018743530")
    dbm.add_channel("kanal_pars_kiev1", "Киев", "-1002009215054")
    dbm.add_channel("kanal_pars_kiev2", "Киев", "-1002009215054")
    dbm.add_channel("dsadaad123", "Одеса", "-1002018743530")
    print(dbm.get_all_channel_names())
    watcher.start()

    updater.start_polling()
    job_queue = updater.job_queue
    job_queue.run_repeating(expire_promocodes, interval=3600, first=0)  # Запускается каждый час

    updater.idle()
    
if __name__ == '__main__':
    asyncio.run(main())
