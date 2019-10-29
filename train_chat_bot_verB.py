import pytz
import telebot
import requests
import json
import time
import datetime
import pytz
from flask import Flask
import os

server = Flask(__name__)

# Глобальные переменные времени
tz = pytz.timezone('Europe/Moscow')

# Информация по боту
TOKEN = '1021829672:AAFfhtoenReBeiqMfw3kJpeOfqH_GSFXY7o'
bot = telebot.TeleBot(TOKEN)

# Код для парса электричек

API = 'ef07933a-471d-462a-a481-3852e0784860'

station_list = {"Москва": "s2000002", "Москва-3": "s9601018", "Маленковская": "s9601882", "Яуза": "s9601236",
                "Северянин": "s9601217", "Лосиноостровская": "s9601716", "Лось": "s9600831", "Перловская": "s9600841",
                "Тайнинская": "s9601001", "Мытищи": "s9600681", "Строитель": "s9601887", "Челюскинская": "s9602281",
                "Тарасовская": "s9601954", "Клязьма": "s9601246", "Мамонтовская": "s9601241", "Пушкино": "c10748"}

station_1 = "Москва"
station_2 = "Пушкино"


def info_train(station_1, station_2):
    response = requests.get('https://api.rasp.yandex.net/v3.0/search/?'
                            'apikey=ef07933a-471d-462a-a481-3852e0784860&'
                            'format=json&'
                            'from={station_1}&'
                            'to={station_2}&'
                            'lang=ru_RU&'
                            'transport_types=suburban&'
                            'page=1&'
                            'date={date_now}&'
                            'offset=1&'
                            'limit=10000'.format(station_1=station_1, station_2=station_2,
                                                 date_now=str(datetime.datetime.now(tz))[0:10]))

    response.encoding = 'utf-8'
    global page_1
    page_1 = json.loads(response.text)
    return page_1


# Колдовство для расчета разницы во времени

def different_time(time: str):
    time_now = str(datetime.datetime.now())[11:16]
    requared_now = time_now.split(':')
    time_now_all = int(requared_now[0]) * 60 + int(requared_now[1])

    time_train = time
    requared_train = time_train.split(':')
    time_train_all = int(requared_train[0]) * 60 + int(requared_train[1])

    how_time = str((time_train_all - time_now_all) // 60).zfill(2), ":", str(
        (time_train_all - time_now_all) % 60).zfill(2)
    final_time = "".join(how_time)
    return final_time


@bot.message_handler(commands=["First"])
def first_station(message):
    global station_1
    set_system(message, station_1)
    return station_1


@bot.message_handler(commands=["Second"])
def second_station(message):
    global station_2
    set_system(message, station_2)
    return station_2


@bot.message_handler(commands=["First"])
def set_system(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    for i in station_list:
        keyboard.row(telebot.types.InlineKeyboardButton(i, callback_data=i))
    bot.send_message(message.from_user.id, 'Выбери, куда поедешь', reply_markup=keyboard)
    print(message)
    callback_inline(message, station)

@bot.callback_query_handlers(func=lambda call: True)
def callback_inline(message, station):
    data = message.data
    bot.send_message(call.from_user.id, "Изменить Первую станцию - /First, "
                                            "Изменить вторую станцию - /Second,"
                                            "Показать расписание - /start")
    print(data + " Городок Первый")
    print(type(data))
    global station_1
    station_1 = data
    print(station_1)
    bot.answer_callback_query(call.id, "Первый город настроен")



# Код для работы парсера

def station_parse(station_1, station_2):
    info_train(station_1, station_2)
    list = []
    for i in range(page_1['pagination']['total'] - 1):
        if page_1['segments'][i]['departure'][11:16] > str(datetime.datetime.now(tz))[11:16]:
            list.append(((' ' + page_1["segments"][i]['thread']['title'] + ". Отправлением в : " +
                          (page_1['segments'][i]['departure'][11:16]) +
                          ". Прибытием в : "
                          + page_1['segments'][i]['arrival'][11:16] +
                          " Отправится через: "
                          + different_time(page_1['segments'][i]['departure'][11:16]))))
        else:
            pass

    go_train = '\n \n'.join(list[0:5])
    return go_train


# Код для работы бота
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == "/help":
        bot.send_message(message.from_user.id,
                         "Привет! Все очень просто, бот выдаст тебе ближайшие 5 электричек в том направлении, куда тебе захочется. Если вдруг бот не работает, то это чистая случайность :) Для рывка, просто тыкни сюда /start")
    elif message.text == "/start":
        start_find(message)
    elif message.text == '/time':
        bot.send_message(message.from_user.id, str(datetime.datetime.now(tz))[11:16])
    elif message.text == '/First':
        set_system(message)
    else:
        bot.send_message(message.from_user.id, "Возможно опечатка? Тут функций-то всего две! "
                                               "Ты хотел начать /start ? Инфа тут /help или "
                                               "изменить первую станцию: /First "
                                               "изменить вторую станцию: /Second")


@bot.message_handler()
def start_find(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton('Едем в ' + station_1, callback_data=station_1),
        telebot.types.InlineKeyboardButton('Едем в ' + station_2, callback_data=station_2)
    )
    bot.send_message(message.chat.id, 'Выбери, куда поедешь', reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: True)
    def iq_callback(message, station_1, station_2):
        data = message.data
        if data.startswith(station_1):
            station_1 = station_list.get(station_1)
            station_2 = station_list.get(station_2)
            bot.send_message(message.from_user.id, station_parse(station_1, station_2))
        elif data.startswith(station_2):
            station_1 = station_list.get(station_2)
            station_2 = station_list.get(station_1)
            bot.send_message(message.from_user.id, station_parse(station_1, station_2))


# Запуск БОТА
try:
    bot.polling(none_stop=True, interval=0)
except Exception:
    pass

"""
@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://https://salty-fjord-17491.herokuapp.com//' + TOKEN)
    return "!", 200


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
"""

"""https://www.mindk.com/blog/how-to-develop-a-chat-bot/"""
