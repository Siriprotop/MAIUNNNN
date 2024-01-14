
def is_user_in_channel(bot, channel_id, user_id):
    try:
        chat_member = bot.get_chat_member(channel_id, user_id)
        return chat_member.status in ['creator', 'administrator', 'member']
    except TelegramError as e:
        print("Ошибка:", e)
        return False