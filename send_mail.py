import telegram
#token that can be generated talking with @BotFather on telegram

def send(msg):
        my_token='1701882651:AAGdL2zYR2hb3DyXfLgYOrTzTfXxi37gs4M'
        my_chat_id='1789575416'
        bot=telegram.Bot(token=my_token)
        bot.sendMessage(chat_id=my_chat_id, text=msg)

send('Testing')






