import telebot
import os
from flask import Flask, request
import logging
from configure import *
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

bot = telebot.TeleBot(TOKEN)

try:
    conn=psycopg2.connect(URI, sslmode='require')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor=conn.cursor()
except (Exception, Error) as error:
    print("Ошибка при работе с PostgreSQL", error)

    

# Здесь пишем наши хэндлеры
@bot.message_handler(commands=['start'])
def start(message):
    id=message.from_user.id
    name=message.from_user.first_name
    result=cursor.execute(f'SELECT id FROM users WHERE id={id}')
    if not result:
        cursor.execute('INSERT INTO users (id,username,messages) VALUES (%s,%s,%s)', (id,name,0))
        conn.commit()
    bot.reply_to(message, f'Привет, {message.from_user.first_name}')


# Проверим, есть ли переменная окружения Хероку (как ее добавить смотрите ниже)
if "HEROKU" in list(os.environ.keys()):
    logger = telebot.logger
    telebot.logger.setLevel(logging.INFO)

    server = Flask(__name__)
    @server.route("/bot", methods=['POST'])
    def getMessage():
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!", 200
    @server.route("/")
    def webhook():
        bot.remove_webhook()
        bot.set_webhook(url=APP_URL) # этот url нужно заменить на url вашего Хероку приложения
        return "?", 200
    server.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))
else:
    # если переменной окружения HEROKU нету, значит это запуск с машины разработчика.  
    # Удаляем вебхук на всякий случай, и запускаем с обычным поллингом.
    bot.remove_webhook()
    bot.polling(none_stop=True)
