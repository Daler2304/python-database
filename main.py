import telebot
from telebot import types
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
    cursor.execute(f'SELECT id FROM users WHERE id={id}')
    result=cursor.fetchone()
    if not result:
        cursor.execute('INSERT INTO users (id,username,messages) VALUES (%s,%s,%s)', (id,name,0))
        conn.commit()
        conn.close()
    
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(
        types.KeyboardButton('Привет')
        )
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}',reply_markup=markup)

@bot.message_handler(content_types=['text'])
def mess(message):
    if message.text=='Привет':
        bot.reply_to(message, f'Приветствую!')
    else:
        bot.send_message(message.chat.id, 'Я ещё новый, умею только приветсвовать')

# Проверим, есть ли переменная окружения Хероку (как ее добавить смотрите ниже)
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

