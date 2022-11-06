import os
import logging
import telebot
import psycopg2
from configure import *
from flask import Flask, request

bot=telebot.TeleBot(TOKEN)
server=Flask(__name__)
logger=telebot.logger
logger.setLevel(logging.DEBUG)

db_connection=psycopg2.connect(URI, sslmode='require')
db_object=db_connection.cursor()

@bot.message_handler(commands=['start'])
def start(message):
    id=message.from_user.id
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')

    db_ovject.execute(f'SELECT id FROM users WHERE id={id}')
    result=db_object.fetchone()
    if not result:
        db_object.execute('INSERT INTO users(id, username, messages) VALUES (%s,%s,%s)',(id,username,0))
        db_connection.commit()
        


@server.route(f'/{TOKEN}', methods=['POST'])
def redirect_message():
    json_string=request.get_data().decode('utf-8')
    update=telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!', 200


if __name__=='__main__':
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
