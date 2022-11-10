import telebot
from telebot import types
import os
from flask import Flask, request
import logging
from configure import *
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

bot = telebot.TeleBot(TOKEN)

date=datetime.now()
day=date.strftime('%d/%m/%Y %H:%M:%S')

conn=psycopg2.connect(URI, sslmode='require')
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor=conn.cursor()


# Здесь пишем наши хэндлеры
@bot.message_handler(commands=['start'])
def start(message):
    id=message.from_user.id
    name=message.from_user.first_name
    cursor.execute(f'SELECT id FROM users WHERE id={id}')
    result=cursor.fetchone()
    if not result:
        cursor.execute('INSERT INTO users (id,username,date) VALUES (%s,%s,%s)', (id,name,day))
        conn.commit()
        
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton('Мой ID'),
        types.KeyboardButton('Дата регистрации в боте')
        )
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}', reply_markup=markup)

@bot.message_handler(commands=['send'])
def send(message):
    if message.from_user.id==admin:
        bot.send_message(message.chat.id,'Рассылка')
        if message.text:
            sending_message=message.text
            markup=types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton('Добавить фото',callback_data='add_photo'),
                types.InlineKeyboardButton('Начать рассылку', callback_data='start_sending')
                )
            msg=bot.send_message(message.chat.id, f'{message.text}',reply_markup=markup)


@bot.callback_query_handler(func=lambda call:True)
def call(call):
    if call.data=='add_photo':
        msg=bot.send_message(call.message.chat.id,'Отправьте фото')
        bot.register_next_step_handler(msg,send_photo)
    elif call.data=='start_sending':
        cursor.execute('SELECT id FROM users')
        for i in cursor.fetchall():
            bot.send_message(i[0],f'{sending_message}')

def send_photo(message):
    if message.photo:
        cursor.execute('SELECT id FROM users')
        for i in cursor.fetchall():
            bot.send_photo(i[0], photo=message.photo[0].file_id, caption=f'{sending_message}')
    else:
        bot.reply_to(message,'Фото не обнаружено!')
            
@bot.message_handler(content_types=['text'])
def mess(message):
    id=message.from_user.id
    if message.text=='Мой ID':
        bot.reply_to(message, f'Ваш ID: {id}')
    elif message.text=='Дата регистрации в боте':
        cursor.execute(f'SELECT date FROM users WHERE id = {id}')
        for row in cursor.fetchone():
            bot.send_message(message.chat.id, f'Дата регистрации: {row[2]}')
    else:
        bot.send_message(message.chat.id, 'Я ещё новый, умею только приветсвовать')

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
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
else:
    # если переменной окружения HEROKU нету, значит это запуск с машины разработчика.  
    # Удаляем вебхук на всякий случай, и запускаем с обычным поллингом.
    bot.remove_webhook()
    bot.polling(none_stop=True)
