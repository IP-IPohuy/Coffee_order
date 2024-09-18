import sqlite3

import telebot

# Замените 'YOUR_TOKEN_HERE' на ваш токен, полученный от BotFather
bot = telebot.TeleBot('7281032997:AAGVZnjWdfJQuZk4NbnuZhc3m_-i02sO39E')

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"Привет, {message.from_user.first_name}! Я ваш Telegram бот.")

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

# Запуск бота
bot.polling()

conn = sqlite3.connect('c0ffe-0rder.db')

cursor = conn.cursor()
