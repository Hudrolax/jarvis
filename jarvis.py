# Sergey Nazarov 26.03.2020
import sys
from time import sleep
from datetime import datetime
import threading
import queue
import requests
import telebot
import copy
import class_arduino
import class_watchdog
import gfunctions as gf

version = "1.02"
path = '/home/pi/jarvis/'
arduino_config_name = 'config.txt'
arduino_pinstate = 'arduino_pinstate.txt'
good_proxylist = 'good_proxylist.txt'
telegram_users = []  # telegram users list
API_TOKEN = '1123277123:AAFz7b_joMY-4yGavFAE5o5MKstU5cz5Cfw'
bot = telebot.TeleBot(API_TOKEN, threaded=False)  # Конструктор бота
NotImportantWords = ['в', 'на', 'к', 'у', 'для', 'за']
StartTime = datetime.now()


def append_goodproxy(proxy):
    try:
        # in first read the list
        try:
            f = open(path + good_proxylist, 'r')
            exist_proxies = f.read().split('\n')
            f.close()
        except:
            exist_proxies = []
        if proxy in exist_proxies:
            return
        try:
            f = open(path + good_proxylist, 'a')
        except:
            print('good proxylist file is not exist. Im create new.')
            f = open(path + good_proxylist, 'w')
        f.write(proxy + '\n')
        f.close()
    except:
        print(f'cant write {path + good_proxylist}!!!')


def remove_bad_proxy(proxy):
    try:
        try:
            f = open(path + good_proxylist, 'r')
        except:
            return
        p_list = f.read().split('\n')
        f.close()
        good_p_list = []
        for prox in p_list:
            if prox != proxy and prox != '':
                good_p_list.append(prox)
        f = open(path + good_proxylist, 'w')
        for gp in good_p_list:
            f.write(gp + '\n')
        f.close()
    except:
        print(f'cant write {path + good_proxylist}')


def load_good_proxylist():
    try:
        f = open(path + good_proxylist, 'r')
        lst = f.read().split('\n')
        f.close()
        lst2 = []
        for l in lst:
            if l != '':
                lst2.append(l)
        return lst2
    except:
        print(f'cant read {path + good_proxylist}')
        return None

def PingWatchdog(wd):
    while True:
        wd.ping()
        sleep(1)


# Function of input in thread
def read_kbd_input(inputQueue):
    while True:
        # Receive keyboard input from user.
        try:
            input_str = input()
            print('Enter command: ' + input_str)
            inputQueue.put((input_str, None, None))
        except:
            continue


def SendToTelegramId(_id, message):
    try:
        bot.send_message(_id, message)
    except:
        print(f'error send to telegramm id {_id}')


def SendToAllTelegram(message):
    for user in telegram_users:
        try:
            SendToTelegramId(user.ID, message)
        except:
            print('error send to all telegram ID')


def TelegramBot():
    while True:
        try:
            content = str(requests.get('https://www.proxy-list.download/api/v1/get?type=http').content)
            content = content.replace(r'\r\n', ',')
            content = content.replace("b'", '')
            content = content.replace(",'", '')
            a = content.split(',')
            print('Im try load good proxylist')
            gp_list = load_good_proxylist()
            contarr = []
            if gp_list != None:
                contarr.extend(gp_list)
                print('Good proxylist is loaded')
            else:
                print('Cant load good proxylist :(')
            contarr.extend(a)
        except:
            sleep(0.1)
            continue
        for prox in contarr:
            if prox != '':
                try:
                    telebot.apihelper.proxy = {'https': prox}
                    append_goodproxy(prox)
                    print('Try connect to Telegramm...')
                    bot.polling(none_stop=True)
                except:
                    print('I am have some problem with connect to Telegramm')
                    remove_bad_proxy(prox)
                    sleep(0.1)


# Telegram bot
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global inputQueue
    global TelegrammAnswerQueue

    _user = None
    for user in telegram_users:
        if str(message.from_user.id) == user.ID:
            _user = user
            break
    if message.text == "Привет":
        bot.reply_to(message, "Привет, чем я могу тебе помочь?")
    elif message.text == "/help" or message.text == "help":
        if _user != None:
            helpmessage = 'Help:\n'
            helpmessage += 'getmyid - получить свой telegram ID\n'
            helpmessage += '\n'
            helpmessage += 'pinstate - посмотреть список пинов\n'
            helpmessage += '\n'
            helpmessage += 'bind <pin1> <pin2> <...> - привязать к входному пину pin1 пины pin2 ..\n'
            helpmessage += '\n'
            helpmessage += 'unbind <pin1> <pin2> <...> - отвязать к входному пину pin1 пины pin2 ..\n'

            bot.reply_to(message, helpmessage)
        else:
            bot.reply_to(message, "Кто ты чудовище?")
    elif message.text == 'getmyid':
        bot.reply_to(message, "Ваш ID: %s" % message.from_user.id)
    elif message.text == 'getconfig':
        if _user != None:
            doc = open(arduino.config_path, 'rb')
            bot.send_document(message.from_user.id, doc)
        else:
            bot.reply_to(message, "Кто ты чудовище?")
    else:
        if _user != None:
            inputQueue.put((message.text, _user, message))  # Поместили сообщение в оцередь на обработку
            AnsweWaitTime = 10
            while AnsweWaitTime > 0:
                if (TelegrammAnswerQueue.qsize() > 0):
                    queue_typle = TelegrammAnswerQueue.get()
                    get_message = queue_typle[0]
                    answer = queue_typle[1]
                    if get_message == message:
                        bot.reply_to(message, answer)
                        break
                    else:
                        TelegrammAnswerQueue.put((get_message, answer))

                AnsweWaitTime -= 1
                sleep(1)
        else:
            bot.reply_to(message, "Кто ты чудовище?")


@bot.message_handler(content_types=["sticker", 'document'])
def handle_docs_audio(message):
    _user = None
    for user in telegram_users:
        if str(message.from_user.id) == user.ID:
            _user = user
            break
    if _user != None:
        if message.content_type == 'sticker':
            # Получим ID Стикера
            sticker_id = message.sticker.file_id
            bot.send_message(message.from_user.id, str(sticker_id))
        elif message.content_type == 'document':
            if message.document.file_name == 'config.txt':
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                with open(arduino.config_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                test_config = arduino.LoadConfig(False)
                if test_config == 'config loaded!':
                    bot.reply_to(message, "конфиг загрузил и применил")
                else:
                    bot.reply_to(message, "почему-то не вышло загрузить конфиг")
            else:
                bot.send_message(message.from_user.id, 'Не знаю что за файл такой ты мне шлешь. Мне нужен config.txt.')
    else:
        bot.reply_to(message, "Кто ты чудовище?")


def AccessError():
    return 'У вас нет доступа к этой команде\n'


# Command processing module
def CommandProcessing(cmd, telegramuser, message):
    global TelegrammAnswerQueue
    cmd = cmd.lower()
    print_lst = f'first command: {cmd}'
    if telegramuser != None:
        print_lst += f' from {telegramuser.name}'
    print(print_lst)
    global_cmd_list = cmd.split(' ')
    cmdlist_by_and = cmd.split(' и ')
    answer = ''
    for list_by_and in cmdlist_by_and:
        cmd_list = list_by_and.split(' ')

        if 'включи' not in cmd_list and 'включи' in global_cmd_list:
            cmd_list.append('включи')
        elif ('выключи' not in cmd_list and 'выключи' in global_cmd_list) or (
                'отключи' not in cmd_list and 'отключи' in global_cmd_list):
            cmd_list.append('выключи')
        elif 'заблокируй' not in cmd_list and 'заблокируй' in global_cmd_list:
            cmd_list.append('заблокируй')
        elif 'разблокируй' not in cmd_list and 'разблокируй' in global_cmd_list:
            cmd_list.append('разблокируй')

        if ('свет' not in cmd_list and 'свет' in global_cmd_list) or (
                'освещение' not in cmd_list and 'освещение' in global_cmd_list):
            cmd_list.append('свет')
        print(f'cmd in loop: {cmd_list}')

        if 'включи' in cmd_list or 'on' in cmd_list:
            if 'свет' in cmd_list and ('везде' in cmd_list or 'доме' in cmd_list or 'дома' in cmd_list):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if p.output and 'свет' in p.ConvertibleTerms and 'дом' in p.ConvertibleTerms:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.set_pin(p, 1)
                                print(f'Включил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Включил свет везде.\n'
                else:
                    answer += AccessError()
            elif 'свет' in cmd_list and ('первом' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if 'свет' in p.ConvertibleTerms and 'первый' in p.ConvertibleTerms and (
                                'этаж' in p.ConvertibleTerms or 'этаже' in p.ConvertibleTerms) and p.output:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.set_pin(p, 1)
                                print(f'Включил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Включил свет на первом этаже.\n'
                else:
                    answer += AccessError()
            elif 'свет' in cmd_list and ('втором' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if 'свет' in p.ConvertibleTerms and 'втором' in p.ConvertibleTerms and (
                                'этаж' in p.ConvertibleTerms or 'этаже' in p.ConvertibleTerms) and p.output:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.set_pin(p, 1)
                                print(f'Включил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Включил свет на втором этаже.\n'
                else:
                    answer += AccessError()
            else:
                # elif 'свет' in cmd_list:
                if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                    # Добавим личный флаг пользователя
                    findlist = copy.deepcopy(cmd_list)
                    if telegramuser != None:
                        findlist.append(telegramuser.name)
                    WinnerPin = arduino.FindByAuction(findlist)
                    if WinnerPin == None:
                        answer += 'Не понятно, что нужно включить. Уточни команду.\n'
                    elif str(type(WinnerPin)) == "<class 'list'>":
                        if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                            for p in WinnerPin:
                                if p.output:
                                    if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                        a = arduino.set_pin(p, 1)
                                        if a == True:
                                            answer += f'{p.description} включен\n'
                                        elif a == False:
                                            answer += f'{p.description} выключен\n'
                                        else:
                                            answer += 'Ошибка передачи данных\n'
                                    else:
                                        answer += f'{p.description} заблокирован для вас'
                        else:
                            answer += AccessError()
                    else:
                        if telegramuser != None and telegramuser.level <= 1 or telegramuser == None or (
                                telegramuser != None and telegramuser.name in WinnerPin.ConvertibleTerms):
                            if telegramuser != None and telegramuser.level <= 0 and WinnerPin.blocked or telegramuser == None or not WinnerPin.blocked:
                                a = arduino.set_pin(WinnerPin, 1)
                                if a == True:
                                    answer += f'{WinnerPin.description} включен\n'
                                elif a == False:
                                    answer += f'{WinnerPin.description} выключен\n'
                                else:
                                    answer += 'Ошибка передачи данных\n'
                            else:
                                answer += f'{WinnerPin.description} заблокирован для вас'
                        else:
                            answer += AccessError()
                else:
                    answer += AccessError()
        elif 'выключи' in cmd_list or 'отключи' in cmd_list or 'off' in cmd_list:
            if 'свет' in cmd_list and ('везде' in cmd_list or 'доме' in cmd_list or 'дома' in cmd_list):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if p.output and 'свет' in p.ConvertibleTerms and 'дом' in p.ConvertibleTerms:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.set_pin(p, 0)
                                print(f'Выключил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Выключил свет везде.\n'
                else:
                    answer += AccessError()
            elif 'свет' in cmd_list and ('первом' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if 'свет' in p.ConvertibleTerms and 'первом' in p.ConvertibleTerms and (
                                'этаж' in p.ConvertibleTerms or 'этаже' in p.ConvertibleTerms) and p.output:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.set_pin(p, 0)
                                print(f'Выключил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Выключил свет на первом этаже.\n'
                else:
                    answer += AccessError()
            elif 'свет' in cmd_list and ('втором' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if 'свет' in p.ConvertibleTerms and 'втором' in p.ConvertibleTerms and (
                                'этаж' in p.ConvertibleTerms or 'этаже' in p.ConvertibleTerms) and p.output:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.set_pin(p, 0)
                                print(f'Выключил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Выключил свет на втором этаже.\n'
                else:
                    answer += AccessError()
            else:
                # elif 'свет' in cmd_list:
                if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                    findlist = copy.deepcopy(cmd_list)
                    if telegramuser != None:
                        findlist.append(telegramuser.name)
                    WinnerPin = arduino.FindByAuction(findlist)
                    if WinnerPin == None:
                        answer += 'Не понятно, что нужно выключить. Уточни команду.\n'
                    elif str(type(WinnerPin)) == "<class 'list'>":
                        if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                            for p in WinnerPin:
                                if p.output:
                                    if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                        a = arduino.set_pin(p, 0)
                                        if a == True:
                                            answer += f'{p.description} включен\n'
                                        elif a == False:
                                            answer += f'{p.description} выключен\n'
                                        else:
                                            answer += 'Ошибка передачи данных\n'
                                    else:
                                        answer += f'{p.description} заблокирован для вас'
                        else:
                            answer += AccessError()
                    else:
                        if telegramuser != None and telegramuser.level <= 1 or telegramuser == None or (
                                telegramuser != None and telegramuser.name in WinnerPin.ConvertibleTerms):
                            if telegramuser != None and telegramuser.level <= 0 and WinnerPin.blocked or telegramuser == None or not WinnerPin.blocked:
                                a = arduino.set_pin(WinnerPin, 0)
                                if a == True:
                                    answer += f'{WinnerPin.description} включен\n'
                                elif a == False:
                                    answer += f'{WinnerPin.description} выключен\n'
                                else:
                                    answer += 'Ошибка передачи данных\n'
                            else:
                                answer += f'{WinnerPin.description} заблокирован для вас'
                        else:
                            answer += AccessError()
                else:
                    answer += AccessError()
        elif ('верни' in cmd_list and (
                'было' in cmd_list or 'обратно' in cmd_list)) or 'пошутил' in cmd_list or 'шутка' in cmd_list:
            if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                for p in arduino.pins:
                    if (datetime.now() - p.LastRevTime).total_seconds() <= 30:
                        if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                            a = arduino.set_pin(p, p.prevstate)  # prev pin state
                            print(f'pin {p.num} is {a}')
                        else:
                            answer += f'{p.description} заблокирован для вас'
                answer += 'Вернул все как было\n'
            else:
                answer += AccessError()
        elif 'оставь' in cmd_list and 'свет' in cmd_list:
            if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                WinnerPin = arduino.FindByAuction(cmd_list)
                if WinnerPin == None:
                    answer += 'Не понятно, что нужно оставить включенным. Уточни команду.\n'
                elif str(type(WinnerPin)) == "<class 'list'>":
                    if ('кухне' in cmd_list or 'кухня' in cmd_list) and len(WinnerPin) == 2:
                        if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                            for p in arduino.pins:
                                if p.output and p in WinnerPin:
                                    if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                        arduino.set_pin(p, 1)
                                    else:
                                        answer += f'{p.description} заблокирован для вас'
                                elif p.output and 'свет' in p.ConvertibleTerms and 'первый' in p.ConvertibleTerms and 'этаж' in p.ConvertibleTerms:
                                    if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                        arduino.set_pin(p, 0)
                                    else:
                                        answer += f'{p.description} заблокирован для вас'
                            answer += 'Оставил включенным только свет на кухне.\n'
                        else:
                            answer += AccessError()
                    else:
                        answer += 'Я нашел более одного объекта для оставления:\n'
                        for w in WinnerPin:
                            answer += f'{w.description}\n'
                        answer += 'Нужно уточнить, что конкретно оставить.\n'
                else:
                    if telegramuser != None and telegramuser.level <= 1 or telegramuser == None or (
                            telegramuser != None and telegramuser.name in WinnerPin.ConvertibleTerms):
                        HouseLevel = 'первый'
                        if 'второй' in WinnerPin.ConvertibleTerms:  # Определяем к какому этажу относится команда
                            HouseLevel = 'второй'
                        for p in arduino.pins:
                            if p.output and 'свет' in p.ConvertibleTerms and HouseLevel in p.ConvertibleTerms and 'этаж' in p.ConvertibleTerms:
                                if p == WinnerPin:
                                    if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                        a = arduino.set_pin(p, 1)
                                    else:
                                        answer += f'{p.description} заблокирован для вас'
                                else:
                                    if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                        a = arduino.set_pin(p, 0)
                                    else:
                                        answer += f'{p.description} заблокирован для вас'
                        answer += f'Оставил включенным только {WinnerPin.description}\n'
                    else:
                        answer += AccessError()
            else:
                answer += AccessError()
        elif 'заблокируй' in cmd_list or 'заблокирую' in cmd_list:
            if "все" in cmd_list and "выключатели" in cmd_list:
                for p in arduino.pins:
                    if not p.output:
                        p.blocked = True;
                answer += f'Заблокировал все выключатели\n'
            elif telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                WinnerPin = arduino.FindByAuction(cmd_list, True)
                if WinnerPin == None:
                    answer += 'Не понятно, что нужно заблокировать. Уточни команду.\n'
                elif str(type(WinnerPin)) == "<class 'list'>":
                    for p in WinnerPin:
                        p.blocked = True
                        answer += f'Заблокировал {p.description}\n'
                else:
                    WinnerPin.blocked = True
                    answer += f'Заблокировал {WinnerPin.description}\n'
                arduino.write_pinstate(None)
            else:
                answer += AccessError()
        elif 'разблокируй' in cmd_list or 'разблокирую' in cmd_list:
            if "все" in cmd_list and "выключатели" in cmd_list:
                for p in arduino.pins:
                    if not p.output:
                        p.blocked = False;
                answer += f'Заблокировал все выключатели\n'
            elif telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                WinnerPin = arduino.FindByAuction(cmd_list, True)
                if WinnerPin == None:
                    answer += 'Не понятно, что нужно разблокировать. Уточни команду.\n'
                elif str(type(WinnerPin)) == "<class 'list'>":
                    for p in WinnerPin:
                        p.blocked = False
                        answer += f'Разблокировал {p.description}\n'
                else:
                    WinnerPin.blocked = False
                    answer += f'Разблокировал {WinnerPin.description}\n'
                arduino.write_pinstate(None)
            else:
                answer += AccessError()
        elif cmd.find('pinstate') > -1:
            if telegramuser != None and telegramuser.level <= 3 or telegramuser == None:
                try:
                    val = cmd.split(' ')[1]
                except:
                    val = -1
                pin = arduino.pin(val)
                if pin != None:
                    if pin.state:
                        answer = f'pin {pin.num} is ON\n'
                    else:
                        answer = f'pin {pin.num} is OFF\n'
                else:
                    answer = f"Can't find the pin with number {val}\n"
            else:
                answer += AccessError()
        elif cmd.find('loadconfig') > -1 or cmd.find('загрузи конфиг') > -1:
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                answer = arduino.LoadConfig(False)
            else:
                answer += AccessError()
        elif cmd.find('pinlist') > -1 or cmd.find('list pins') > -1 or cmd.find('listpins') > -1 or cmd.find(
                'список пинов') > -1 or cmd.find('пинлист') > -1:
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                answer += '*** Pin list: ***' + '\n'
                answer += 'Inputs:' + '\n'
                for p in arduino.pins:
                    if not p.output:
                        answer += f'   pin {p.num} ({p.name})'
                        if p.blocked:
                            answer += '(blocked)'
                        if len(p.binds) > 0:
                            answer += ' >>> '
                            k = 0
                            for b in p.binds:
                                if k != 0:
                                    answer += ','
                                answer += f' {b.num} ({b.description})'
                                k += 1
                        answer += '\n'
                answer += 'Outputs:' + '\n'
                for p in arduino.pins:
                    if p.output:
                        answer += f'   pin {p.num} ({p.name})'
                        if p.blocked:
                            answer += '(blocked)'
                        answer += '\n'
            else:
                answer += AccessError()
        elif cmd.startswith('bind '):
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                try:
                    val = cmd.split(' ')
                    bindto = arduino.pin(val[1])
                    if not bindto.output:
                        for i in range(2, len(val)):
                            addpin = arduino.pin(val[i])
                            if addpin.output:
                                if not addpin in bindto.binds:
                                    bindto.binds.append(addpin)
                                else:
                                    answer += f'pin {addpin.name} is already in {bindto.name}.binds' + '\n'
                            else:
                                answer += f'pin {addpin.name} is INPUT pin and connot binded to pin {bindto.name}\n'
                        answer += 'pins is binded!\n'
                        if arduino.SaveConfig() == None:
                            answer += 'config is saved\n'
                        else:
                            answer += 'error save config\n'
                    else:
                        answer += f'pin {bindto.name} is OUTPUT pin and you cant bind to it.\n'
                except:
                    answer += 'error bind pins\n'
            else:
                answer += AccessError()
        elif cmd.startswith('unbind '):
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                try:
                    val = cmd.split(' ')
                    bindto = arduino.pin(val[1])
                    if not bindto.output:
                        for i in range(2, len(val)):
                            bindto.binds.remove(arduino.pin(val[i]))
                        answer = 'pins is unbinded!\n'
                        if arduino.SaveConfig() == None:
                            answer += 'config is saved\n'
                        else:
                            answer += 'error save config\n'
                    else:
                        answer += f'pin {bindto.name} is OUTPUT pin and you cant bind to it.\n'
                except:
                    answer == 'error unbind pins\n'
            else:
                answer += AccessError()
        elif (cmd.find('print') > -1 and cmd.find('config') > -1) or (
                cmd.find('покажи') > -1 and cmd.find('конфиг') > -1):
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                f = open(arduino.config_path, 'r')
                try:
                    answer += f.read()
                    f.close()
                except:
                    answer += 'не могу прочесть конфиг\n'
            else:
                answer += AccessError()
        elif cmd == 'state' or cmd == 'status' or 'статус' in cmd_list:
            if telegramuser != None and telegramuser.level <= 3 or telegramuser == None:
                uptime = gf.difference_between_date(StartTime, datetime.now())
                answer += 'ver. '+version+'   '
                answer += f'uptime {uptime}\n'
                if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                    answer += 'Включенный свет:\n'
                    k = 0
                    for p in arduino.pins:
                        if p.output and 'свет' in p.ConvertibleTerms and p.state:
                            if k > 0:
                                answer += ' ,'
                            answer += f'{p.description}'
                            k += 1
                    if k == 0:
                        answer += 'весь свет выключен\n'
                    answer += '\n'
                answer += '\n'

                answer += "Насосы "
                pumpsPin = arduino.pin("насосы")
                if pumpsPin is not None:
                    if pumpsPin.state:
                        answer += "включены"
                    else:
                        answer += "ВЫКЛЮЧЕНЫ"
                else:
                    answer += "<не могу найти пин насосов  по description 'насосы'>"
                answer += '\n'
                ACNet = 'есть'
                if not arduino.ACCExist:
                    ACNet = 'НЕТ'
                answer += f'Напряжение в сети {ACNet}\n'
                answer += f'Напряжение аккумулятора {arduino.DCVol} V ({arduino.DCVoltageInPercent} %)\n'
            else:
                answer += AccessError()
        elif cmd == 'exit':
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                print('bye...')
                sys.exeit()
            else:
                answer += AccessError()
        else:
            answer += 'неизвестная команда\n'

    if message != None:
        TelegrammAnswerQueue.put((message, answer))  # Поместили сообщение в оцередь на обработку
    return answer


def ReglamentWork():
    global ReglamentWorkTimer
    if ReglamentWorkTimer <= 0:
        if datetime.now().hour >= 19 or datetime.now().hour <= 6:  # включим свет на улице
            if not arduino.LastSetStateOutDoorLight or arduino.LastSetStateOutDoorLight == None:
                arduino.set_pin(arduino.OutDoorLightPin, 1)
                arduino.LastSetStateOutDoorLight = True
        else:
            if arduino.LastSetStateOutDoorLight or arduino.LastSetStateOutDoorLight == None:
                arduino.set_pin(arduino.OutDoorLightPin, 0)
                arduino.LastSetStateOutDoorLight = False

        # Сообщим, что пропало напряжение на входе
        if not arduino.ACCExist and not arduino.ACAlertSended:
            for user in telegram_users:
                if user.level == 0:
                    # if True or user.level == 0 or user.level == 3:
                    SendToTelegramId(user.ID, 'Отключилось напряжение на входе в дом!\n')
            arduino.ACAlertSended = True
        elif arduino.ACCExist and arduino.ACAlertSended:
            for user in telegram_users:
                # if True or user.level == 0 or user.level == 3:
                if user.level == 0:
                    SendToTelegramId(user.ID, 'Ура! Появилось напряжение на входе в дом!\n')
            arduino.ACAlertSended = False

        # Сообщить, что напряжение аккумулятора низкое
        if arduino.DCVoltageInPercent <= 20 and not arduino.DCVolLowAlertSended:
            for user in telegram_users:
                if True or user.level == 0 or user.level == 3:
                    SendToTelegramId(user.ID, 'Напряжение аккумулятора ниже 20% !!! Электричество скоро отключится.\n')
            arduino.DCVolLowAlertSended = True

        # Реакция пинов на разряд аккумулятора без входного напряжения
        if not arduino.ACCExist:
            for p in arduino.pins:
                if p.output and not p.bcod_reaction and arduino.DCVoltageInPercent <= p.bcod:
                    arduino.set_pin(p, 0)
                    print(f'Отключил {p.description} по разряду аккумулятора')
                    p.bcod_reaction = True
                    for user in telegram_users:
                        if user.level <= 1:
                            SendToTelegramId(user.ID, f'Отключил {p.description} по разряду аккумулятора\n')
        else:
            for p in arduino.pins:
                if p.output and p.bcod_reaction and arduino.DCVoltageInPercent > p.bcod:
                    p.bcod_reaction = False
                    arduino.set_pin(p, p.prevstate)  # Вернем состояние пинов на последнее

        ReglamentWorkTimer = 100
    else:
        ReglamentWorkTimer -= 1


# ****** MAIN ******
if __name__ == "__main__":
    # init watchdog
    watchdog = class_watchdog.CWatchDog('/dev/ttyACM0')
    WDThread = threading.Thread(target=PingWatchdog, args=(watchdog,), daemon=True)
    WDThread.start()

    # init arduino
    arduino = class_arduino.Arduino(path + arduino_config_name, path + arduino_pinstate, NotImportantWords)
    arduino.LoadConfig(telegram_users)

    # Start keyboart queue thread
    inputQueue = queue.Queue()
    inputThread = threading.Thread(target=read_kbd_input, args=(inputQueue,), daemon=True)
    inputThread.start()

    # Start Telegram bot thread
    TelegramBotThread = threading.Thread(target=TelegramBot, args=(), daemon=True)
    TelegramBotThread.start()

    TelegrammAnswerQueue = queue.Queue()

    # Main loop dunction
    ReglamentWorkTimer = 100
    while True:
        if arduino.initialized:
            if (inputQueue.qsize() > 0):
                queue_typle = inputQueue.get()
                input_str = queue_typle[0]
                user = queue_typle[1]
                message = queue_typle[2]
                answer = CommandProcessing(input_str, user, message)
                print(answer)
            arduino.check_input_pins()
            ReglamentWork()
        else:
            arduino.initialize()
        sleep(0.02)
