from imports import *
EXACT_ADDRESS, DETAILS, PHOTO, YR_MODERATION, BONUS_CODE = range(5)


bot = None
user_data = {}
moderator_ids = [6964683351]
# classes
dbm = ChannelDB("channels_list.db")
info_dbs = InfoDb()
dbs = DataB()
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

def format_without_photo(address, details, date_time):
    message_parts = [address, details if details.strip() != '' else None, date_time]
    return "\n".join(filter(None, message_parts))

def generate_bonus_code(user_id, conn):
    cursor = conn.cursor()

    # Проверяем, есть ли уже активный промокод у пользователя
    cursor.execute("SELECT promocode, expiry_date FROM promocodes WHERE user_id = ? AND active = 1", (user_id,))
    active_promocode = cursor.fetchone()
    if active_promocode:
        promocode, expiry_date = active_promocode
        if datetime.now() <= datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S'):
            return f"У вас уже есть активный промокод: {promocode}."
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
                f"3) Отправь бонус-код боту.\n"

    return message
def ask_for_bonus_code(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Напиши бонус-код в чат")
    return BONUS_CODE  # Это состояние для ConversationHandler

def check_bonus_code(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    entered_code = update.message.text.strip()
    conn = sqlite3.connect('subscribe.db')
    cursor = conn.cursor()

    # Проверяем, активировал ли пользователь уже какой-либо промокод
    cursor.execute("SELECT promocode, expiry_date FROM promocodes WHERE activated_by_user_id LIKE ? AND active = 1", (f'%{user_id}%',))
    active_promocodes = cursor.fetchall()

    for promocode, expiry_date in active_promocodes:
        if datetime.now() <= datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S'):
            update.message.reply_text(f"❌ У вас уже активирован промокод {promocode}. Вы не можете активировать новый промокод до его истечения.")
            conn.close()
            return ConversationHandler.END

    # Проверяем наличие введенного промокода в базе и его срок действия
    cursor.execute("SELECT promocode, expiry_date, activated_by_user_id, count FROM promocodes WHERE promocode = ? AND active = 1", (entered_code,))
    code_data = cursor.fetchone()

    if code_data:
        promocode, expiry_date, activated_user_ids_str, count = code_data
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
                update.message.reply_text("✅ Ваш промокод успешно активирован.")
            else:
                update.message.reply_text("❌ Вы уже активировали этот промокод.")
            return ConversationHandler.END
        else:
            update.message.reply_text("❌ Ваш промокод просрочен.")
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
            except telegram.error.BadRequest as e:
                # Log the error and continue with the next user ID
                print(f"Failed to send message to {user_id}: {e}")
    elif message.photo:
        # Send the highest quality photo
        photo = message.photo[-1].file_id
        for user_id in user_ids:
            try:
                context.bot.send_photo(chat_id=user_id, photo=photo)
            except telegram.error.BadRequest as e:
                # Log the error and continue with the next user ID
                print(f"Failed to send message to {user_id}: {e}")
    elif message.document:
        # Send document
        document = message.document.file_id
        for user_id in user_ids:
            try:
                context.bot.send_document(chat_id=user_id, document=document)
            except telegram.error.BadRequest as e:
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

def broadcast_to_all_cities(update: Update, context: CallbackContext) -> int:
    message = update.message
    caption = message.caption if message.caption else None
    content = message.text if message.text else None
    photo = message.photo[-1].file_id if message.photo else None
    document = message.document.file_id if message.document else None

    try:
        user_ids = dbs.get_all_users()
        for user_tuple in user_ids:
                user_id = user_tuple[0]  # Извлекаем user_id из кортежа
                for city_channel in channelsss:
                    res1 = is_user_in_channel(bot, city_channel, user_id)
                    if res1 == True:
                        break
                if res1 == True:
                    continue
                if photo and caption:
                    context.bot.send_photo(chat_id=user_id, photo=photo, caption=caption)
                elif content:
                    context.bot.send_message(chat_id=user_id, text=content)
                elif photo:
                    context.bot.send_photo(chat_id=user_id, photo=photo)
                elif document:
                    context.bot.send_document(chat_id=user_id, document=document)
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
            except telegram.error.BadRequest as e:
                print(f"Failed to send message to channel {channel_id}: {e}")

        update.message.reply_text("Content sent to all city channels and users.")
    except Exception as e:
        update.message.reply_text(f"Failed to send messages: {e}")
        print(f"Exception: {e}")

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
        query.edit_message_text(text="Введите сообщение для рассылки:")
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
    update.effective_message.reply_text(
        "<b>1) Введите точный адрес (обязательно)</b>\n"
        "Чем точнее будет адрес, тем лучше.\n"
        "Например: Богдана Хмельницкого, 33.",
        parse_mode='HTML'
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
                
                    except telegram.error.BadRequest as e:
                        print(f"Failed to send message to user {user_id}: {e}")
                return ConversationHandler.END
            else:
                print(f"Файл данных для города {city_to_check} не найден.")
                context.user_data.clear()  # Используйте clear() для очистки данных
                return ConversationHandler.END
        print('GGG')
        query.message.reply_text("<b>Дякуємо, що залишили нову адресу. Ваша інформація буде перебувати на перевірці, і незабаром буде опублікована.</b>", parse_mode='HTML')
        now = datetime.now()
        month_name = ukrainian_months[now.month]  # Get Ukrainian month name
        formatted_date = now.strftime(f"%d {month_name}, %H:%M")  # Format the date
        user_data[user_id]['DATE_TIME'] = formatted_date
        city = user_data[user_id].get('city', '').strip()
        context.user_data['city_name'] = city
        if city in city_files:
            context.user_data['city_file'] = city_files[city]
        if user_data[user_id]['DETAILS']:
            process_message_for_publication(update, context)
            return ConversationHandler.END
        else:
            process_message_for_publication(update, context)
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
    if query.data.startswith('no_'):
        user_id_to_delete = int(query.data.split('_')[1])
        post_id_to_delete = user_data[user_id_to_delete].get('POST_ID')
        query.edit_message_text(text="This post has already been published")

        # Удаляем пост из базы данных
        if post_id_to_delete is not None:
            dbs.delete_post(post_id_to_delete)

        try:
            query.edit_message_text(text="Отклонено")
            return ConversationHandler.END
        except Exception as e:
            print(e)
            return ConversationHandler.END


    elif query.data.startswith('yr_'):
        query.edit_message_text(text="This post has already published")
        return yr_moderation(update, context)
    elif query.data.startswith('yp'):
        user_id_to_edit = int(query.data[3:])
        if user_id_to_edit in user_data:
            post_id = user_data[user_id_to_edit].get('POST_ID')
            query.edit_message_text('This post has already been published')
            city_to_check = user_data[user_id_to_edit]['city']
            address = user_data[user_id_to_edit]['EXACT_ADDRESS']
            details = user_data[user_id_to_edit].get('DETAILS', '')
            photo = user_data[user_id_to_edit].get('PHOTO', '')
            date_time = user_data[user_id_to_edit].get('DATE_TIME', '')
            info_dbs.add_address(address, details)
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
                    except telegram.error.BadRequest as e:
                        print(f"Failed to send message to user {user_id}: {e}")

            else:
                print(f"Файл данных для города {city_to_check} не найден.")
    else:
        user_data[user_id]['city'] = query.data
        dbs.add_user(user_id, query.data)
        print(dbs.get_all_users())
        print("City set to:", user_data[user_id]['city'])  # Debug print
        query.edit_message_text(text=f"Вибране місто: {query.data}")

        reply_keyboard = [
            ["Повідомити нову адресу"],
            ["Відкрити карту адрес"],
            ["Получить бонус-код"],
            ["Активировать промокод"]
        ]
        if user_id in moderator_ids:
            reply_keyboard.append(["Рассылка модератором"])
        update.effective_message.reply_text(
            'Оберіть опцію:',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
        )

def new_address(update: Update, context: CallbackContext) -> int:
    user_id = update.message.chat_id
    if user_id in user_data and 'PHOTO' in user_data[user_id]:
        del user_data[user_id]['PHOTO']
    update.message.reply_text("<b>1) Введите точный адрес (обязательно)</b>\nЧем точнее будет адрес, тем лучше.\nНапр: Богдана Хмельницкого, 33.", parse_mode='HTML')
    return EXACT_ADDRESS

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
        update.message.reply_text('<b>3) Фото місця (необязательно)</b>', parse_mode='HTML', reply_markup=reply_markup)
        return PHOTO
    user_data[user_id]['DETAILS'] = text
    update.message.reply_text("<b>3) Фото місця (необязательно)</b>", parse_mode='HTML', reply_markup=reply_markup)
    return PHOTO



def updaterPhoto(update: Update, context: CallbackContext) -> int:
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
                    except telegram.error.BadRequest as e:
                        print(f"Failed to send message to user {user_id}: {e}")

            else:
                print(f"Файл данных для города {city_to_check} не найден.")
    context.user_data.clear()
    return ConversationHandler.END
def compose_final_message(address, details, photo_url):
    return f"Адрес: {address}\nКомментарий: {details}\nФото: {photo_url}"


def publish_message_city(update: Update, context: CallbackContext):
    try:
        user_id = update.message.chat_id
    except Exception as e:
        query = update.callback_query
        query.answer()
        user_id = query.message.chat_id
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
def process_message_for_publication(update, context):
    try:
        user_id = update.message.chat_id
    except Exception as e:
        query = update.callback_query
        query.answer()
        user_id = query.message.chat_id
    # Получаем данные из user_data
    address = user_data[user_id].get('EXACT_ADDRESS', '').strip()
    details = user_data[user_id].get('DETAILS', '').strip()
    photo_url = user_data[user_id].get('PHOTO', '').strip()
    formatted_date = user_data[user_id].get('DATE_TIME', '').strip()
    print(f"ADDRESS DETAILS {address} {details}")

    # Подготавливаем запросы к Chat GPT для модерации
    prompt_address = f"Візьми це повідомлення: {address}, та проведи модерацію та виправленняа, а саме: Видали з тексту всі образи, лайки та сленги. Прибери всі спец.символи, теги, посилання. Переклади текст українською"
    prompt_details = f"Візьми це повідомлення: {details}, та проведи модерацію та виправлення, а саме: Видали з тексту всі образи, лайки та сленги. Прибери всі спец.символи, теги, посилання. Переклади текст українською"

    # Отправляем запросы к Chat GPT (псевдокод, так как интеграция недоступна)
    moderated_address = send_to_chat_gpt(prompt_address)
    moderated_details = send_to_chat_gpt(prompt_details)
    print(f"ADDRESS {moderated_address}\n\n")

    print(f"DETAILS:{moderated_details}\n\n")
    user_data[user_id]['EXACT_ADDRESS'] = moderated_address
    user_data[user_id]['DETAILS'] = moderated_details
    # Формируем итоговое сообщение для публикации
    post_id = dbs.add_post(user_id, moderated_address, moderated_details, photo_url, formatted_date)
    if details:
        info_dbs.add_address(moderated_address, moderated_details)
    user_data[user_id]['POST_ID'] = post_id
    final_message = compose_final_message(moderated_address, moderated_details, photo_url)
    print(final_message)
    # Публикация сообщения
    publish_message_city(update, context)
    return ConversationHandler.END

def send_to_chat_gpt(prompt):
    openai.api_key = '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'
    try:
        print(prompt)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ти - Модератор, який допомогає перевіряти і перероблювати пости."},
                {"role": "user", "content": prompt}
            ]
        )
    except Exception as e:
        print(e)
    return response['choices'][0]['message']['content']
    
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
        city = user_data[user_id].get('city', '').strip()
        context.user_data['city_name'] = city
        if city in city_files:
            context.user_data['city_file'] = city_files[city]
        photo_status = user_data[user_id].get('PHOTO', '').strip()
        date_time = user_data[user_id].get('DATE_TIME', '').strip()
        user_id_str = str(user_id).strip()
        update.message.reply_text("<b>Дякуємо, що залишили нову адресу. Ваша інформація буде перебувати на перевірці, і незабаром буде опублікована.</b>", parse_mode='HTML')
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
    update.message.reply_text('https://www.google.com/maps/')
    return ConversationHandler.END
def skip_photo(update: Update, context: CallbackContext) -> int:

    print(123)
    print(context.user_data)
    if 'EDIT_USER_ID' in context.user_data:
        print('SKIP PHOTO DPLASJDAIOHAS9YW98FWYRQ98WFHESU89FHSA9FHD')
        context.user_data.clear()
    update.message.reply_text("<b>Дякуємо, що залишили нову адресу. Ваша інформація буде перебувати на перевірці, і незабаром буде опублікована.</b>", parse_mode='HTML')
    process_message_for_publication(update, context)
    return CallbackQueryHandler.END

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
            CallbackQueryHandler(button, pattern='^yr_')  # Добавлен YR как точка входа
        ],
        states={
            EXACT_ADDRESS: [MessageHandler(Filters.text & ~Filters.command, exact_address)],
            DETAILS: [MessageHandler(Filters.text & ~Filters.command, details), CallbackQueryHandler(button, pattern='^skip_details$')],
            PHOTO: [MessageHandler(Filters.all, photo), CallbackQueryHandler(button, pattern='^skip_photo$')]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    conv_handler_broadcast = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Рассылка модератором$'), broadcast_moderator)],
        states={
            CHOOSE_city: [CallbackQueryHandler(choose_city)],
            BROADCAST_MSG: [MessageHandler(Filters.all & ~Filters.command, broadcast_to_city)],
            BROADCAST_ALL: [MessageHandler(Filters.all & ~Filters.command, broadcast_to_all_cities)]
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


    dispatcher.add_handler(conv_handler_broadcast)
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("city", city))
    dispatcher.add_handler(MessageHandler(Filters.regex('^Получить бонус-код$'), share_bonus_code))
    dispatcher.add_handler(conv_handler_message)
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(conv_handler_bon_code)
    dispatcher.add_handler(CallbackQueryHandler(button))  # Добавлен в конце
    daily_message_job = DailyMessageJob('bot.db', info_dbs)
    daily_message_job.schedule(updater)
    watcher = TelegramChannelWatcher(dbm, dbs, bot)
    dbm.add_channel("odessapublic01", "Одеса", "-1002018743530")
    dbm.add_channel("dsadaad123", "Одеса", "-1002018743530")
    print(dbm.print_all_channels())
    watcher.start()

    updater.start_polling()
    job_queue = updater.job_queue
    job_queue.run_repeating(expire_promocodes, interval=3600, first=0)  # Запускается каждый час

    updater.idle()
    
if __name__ == '__main__':
    asyncio.run(main())
