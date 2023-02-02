from loader import bot
from telebot.types import Message
from states.hotel_information import HotelInfoState
from utils.api_requests.city_request import get_city_request
from time import sleep
from random import choice
from utils.create_search_history_db import User
from datetime import datetime

is_low_price = None
is_best_deal = None
cost_var = None
user_low = None
user_high = None
user_best = None


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def any_command(message: Message) -> None:
    """
    Базовый хэндлер поиска отелей,
    ловит одну из трех команд: /lowprice, /highprice, /bestdeal.
    Устанавливает состояние города
    """

    global is_low_price, is_best_deal, cost_var, user_low, user_high, user_best

    if message.text[1:] == 'lowprice':
        is_low_price, is_best_deal = True, False
        cost_var = 'дешевые'
        user_low = User.create(name=message.from_user.full_name,
                               userID=message.from_user.id,
                               command='lowprice',
                               time=datetime.now().strftime('%d-%b-%Y %H:%M:%S'))

    elif message.text[1:] == 'bestdeal':
        is_best_deal, is_low_price = True, False
        user_best = User.create(name=message.from_user.full_name,
                                userID=message.from_user.id,
                                command='bestdeal',
                                time=datetime.now().strftime('%d-%b-%Y %H:%M:%S'))
    else:
        is_low_price, is_best_deal = False, False
        cost_var = 'дорогие'
        user_high = User.create(name=message.from_user.full_name,
                                userID=message.from_user.id,
                                command='highprice',
                                time=datetime.now().strftime('%d-%b-%Y %H:%M:%S'))

    bot.set_state(message.from_user.id, HotelInfoState.city, message.chat.id)
    bot.send_message(message.from_user.id, choice(['Введите название города',
                                                   'Где будем искать?',
                                                   'Какой город выбрали для поиска?',
                                                   'В каком городе будем искать?',
                                                   'Введите город для поиска']))


@bot.message_handler(state=HotelInfoState.city)
def get_city(message: Message) -> None:
    """
    Хэндлер состояния города, в котором будет поиск.
    Устанавливает состояние кол-ва отелей
    """

    if message.text.isalpha() and get_city_request(message.text):
        bot.set_state(message.from_user.id, HotelInfoState.hotel_amt, message.chat.id)
        sleep(2)
        bot.send_message(message.from_user.id, choice(['Отлично! Теперь введите количество отелей',
                                                       'Прекрасно! Теперь мне нужно количество отелей',
                                                       'Замечательно! Сколько отелей ищем?']))

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['city'], data['cityID'] = get_city_request(message.text)
    else:
        bot.send_message(message.from_user.id, choice(['Не нашел такого города.\n'
                                                       'Попробуйте еще раз',
                                                       'Что-то не могу найти такой город.\n'
                                                       'Попробуйте еще раз',
                                                       'Странно... Нет информации по такому городу.\n'
                                                       'Попробуйте еще раз']))


@bot.message_handler(state=HotelInfoState.hotel_amt)
def get_hotel_amt(message: Message) -> None:
    """
    Хэндлер состояния кол-ва отелей для поиска.
    Устанавливает состояние необходимости фотографий
    """

    if message.text.isdigit() and 0 < int(message.text) <= 10:
        bot.set_state(message.from_user.id, HotelInfoState.need_photo, message.chat.id)
        sleep(2)
        bot.send_message(message.from_user.id, choice(['Отлично! Нужны ли фотографии?',
                                                       'Замечательно! Фотографии будем искать?',
                                                       'Очень хорошо! Нужны фотографии?']))

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['hotel_amt'] = int(message.text)
    else:
        bot.send_message(message.from_user.id, choice(['Количество должно быть положительным числом '
                                                       'и я смогу обработать '
                                                       'не больше 10 отелей',
                                                       'Моих сил хватит на 10 отелей и тут жду число...\n'
                                                       'Положительное...',
                                                       'Нужно ввести число, которое больше 0 и меньше 11']))


@bot.message_handler(state=HotelInfoState.need_photo)
def get_photos(message: Message) -> None:
    """
    Хэндлер состояния необходимости фотографий.
    Если фотографии нужны, то отправляет в хэндлер состояния кол-ва фотографий.
    Если не нужны, то отправляет в хэндлер состояния вывода информации
    по командам /lowprice и /highprice
    """

    if message.text == 'Да':

        bot.set_state(message.from_user.id, HotelInfoState.photo_amt, message.chat.id)
        sleep(2)
        bot.send_message(message.from_user.id, choice(['Значит с фотографиями.\n'
                                                       'Введите количество фотографий',
                                                       'Хорошо, будут фотографии.📸\n'
                                                       'Пойду нафоткаю😊\n'
                                                       'Сколько фотографий на отель?',
                                                       'Отметил у себя в блокноте.\n'
                                                       'Фотографии нужны ✅\n'
                                                       'Запишу - какое количество фотографий?']))
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['need_photo'] = True

    elif message.text == 'Нет':
        bot.set_state(message.from_user.id, HotelInfoState.info_low_high, message.chat.id)
        sleep(2)
        if not is_best_deal:
            bot.send_message(message.from_user.id, choice(['Вывести информацию по запросу?',
                                                           'Так...\nВыводим информацию по запросу?',
                                                           'Нужна информация по запросу?\n'
                                                           'Принимаю только "Да"🤫']))
        else:
            bot.send_message(message.from_user.id, choice(['Продолжаем?',
                                                           'Идем дальше?',
                                                           'Вы тут?🥶',
                                                           'Ау🔎, пойдем дальше искать?']))

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['need_photo'] = False

    else:
        bot.send_message(message.from_user.id, choice(['Так "Да" или "Нет"?',
                                                       '🔙 Нужно "Нет" либо "Да"',
                                                       '📴 "Да" или "Нет"',
                                                       '🤦 Пойму только "Да" или "Нет"']))


@bot.message_handler(state=HotelInfoState.photo_amt)
def get_photo_amt(message: Message) -> None:
    """
    Хэндлер состояния кол-ва фотографий.
    Устанавливает состояние вывода информации
    по командам /lowprice и /highprice
    """

    if message.text.isdigit() and 0 < int(message.text) <= 5:
        bot.set_state(message.from_user.id, HotelInfoState.info_low_high, message.chat.id)
        if not is_best_deal:
            bot.send_message(message.from_user.id, choice(['Прекрасно!\n'
                                                           'Выводим информацию по запросу?📑',
                                                           'Успешно!\n'
                                                           'Вывести информацию по запросу?📜',
                                                           'Готово!\n'
                                                           'Нужна информация по запросу?📃']))
        else:
            bot.send_message(message.from_user.id, choice(['Превосходно!\n'
                                                           'Продолжаем, чтобы подобрать лучшие варианты?🏩',
                                                           'Отличненько!\n'
                                                           'Подбираем дальше лучшие предложения?🏨',
                                                           'Отлично!\n'
                                                           'Идем дальше, искать лучшие отели?🏨']))

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['photo_amt'] = int(message.text)
    else:
        bot.send_message(message.from_user.id, choice(['Я смогу обработать только 5 фотографий\n'
                                                       'И убедитесь, что вводите число',
                                                       'Тут такое дело...\n'
                                                       'Мой процессор вытянет только 5 фотографий\n'
                                                       'И только положительное число',
                                                       'Всё, что между 0 и 5(включительно) я приму😊']))
