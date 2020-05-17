# Sergey Nazarov 17.05.2020
from config import *
import sys
from time import sleep
from datetime import datetime
import threading
import queue
import copy
import class_arduino
import class_watchdog
import gfunctions as gf
from gfunctions import JPrint
from telegram_bot import TelegramBot

jprint = JPrint.jprint

# init telegram bot
bot = TelegramBot(path=JARVIS_PATH, list_file=GOOD_PROXY_LIST, token=API_TOKEN, threaded=False)  # Конструктор бота


# Function of input in thread
def read_kbd_input(__input_queue):
    while True:
        # Receive keyboard input from user.
        try:
            input_str = input()
            jprint('Enter command: ' + input_str)
            __input_queue.put((input_str, None, None))
        except:
            continue


# Telegram bot
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global input_queue
    global telegram_answer_queue

    _user = None
    for user in bot.users:
        if str(message.from_user.id) == user.id:
            _user = user
            break
    if message.text == "привет":
        bot.reply_to(message, "Привет, чем я могу тебе помочь?")
    elif message.text == "/help" or message.text == "help":
        if _user is not None:
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
        if _user is not None:
            input_queue.put((message.text, _user, message))  # Поместили сообщение в оцередь на обработку
            __answe_wait_time = 10
            while __answe_wait_time > 0:
                if (telegram_answer_queue.qsize() > 0):
                    queue_typle = telegram_answer_queue.get()
                    get_message = queue_typle[0]
                    answer = queue_typle[1]
                    if get_message == message:
                        bot.reply_to(message, answer)
                        break
                    else:
                        telegram_answer_queue.put((get_message, answer))

                __answe_wait_time -= 1
                sleep(1)
        else:
            bot.reply_to(message, "Кто ты чудовище?")


@bot.message_handler(content_types=["sticker", 'document'])
def handle_docs_audio(message):
    _user = None
    for user in bot.users:
        if str(message.from_user.id) == user.id:
            _user = user
            break
    if _user != None:
        if message.content_type == 'sticker':
            # Получим id Стикера
            sticker_id = message.sticker.file_id
            bot.send_message(message.from_user.id, str(sticker_id))
        elif message.content_type == 'document':
            if message.document.file_name == 'config.txt':
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                with open(arduino.config_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                test_config = arduino.load_config(False)
                if test_config == 'config loaded!':
                    bot.reply_to(message, "конфиг загрузил и применил")
                else:
                    bot.reply_to(message, "почему-то не вышло загрузить конфиг")
            else:
                bot.send_message(message.from_user.id, 'Не знаю что за файл такой ты мне шлешь. Мне нужен config.txt.')
    else:
        bot.reply_to(message, "Кто ты чудовище?")


def get_access_error():
    return 'У вас нет доступа к этой команде\n'


# Command processing module
def command_processing(cmd, telegramuser, message):
    global telegram_answer_queue
    cmd = cmd.lower()
    print_lst = f'first command: {cmd}'
    if telegramuser != None:
        print_lst += f' from {telegramuser.name}'
    jprint(print_lst)
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
        jprint(f'cmd in loop: {cmd_list}')

        if 'включи' in cmd_list or 'on' in cmd_list:
            if 'свет' in cmd_list and ('везде' in cmd_list or 'доме' in cmd_list or 'дома' in cmd_list):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if p.output and 'свет' in p.ConvertibleTerms and 'дом' in p.ConvertibleTerms:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.set_pin(p, 1)
                                jprint(f'Включил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Включил свет везде.\n'
                else:
                    answer += get_access_error()
            elif 'свет' in cmd_list and ('первом' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if 'свет' in p.ConvertibleTerms and 'первый' in p.ConvertibleTerms and (
                                'этаж' in p.ConvertibleTerms or 'этаже' in p.ConvertibleTerms) and p.output:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.set_pin(p, 1)
                                jprint(f'Включил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Включил свет на первом этаже.\n'
                else:
                    answer += get_access_error()
            elif 'свет' in cmd_list and ('втором' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if 'свет' in p.ConvertibleTerms and 'втором' in p.ConvertibleTerms and (
                                'этаж' in p.ConvertibleTerms or 'этаже' in p.ConvertibleTerms) and p.output:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.set_pin(p, 1)
                                jprint(f'Включил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Включил свет на втором этаже.\n'
                else:
                    answer += get_access_error()
            else:
                # elif 'свет' in cmd_list:
                if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                    # Добавим личный флаг пользователя
                    findlist = copy.deepcopy(cmd_list)
                    if telegramuser != None:
                        findlist.append(telegramuser.name)
                    WinnerPin = arduino.find_by_auction(findlist)
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
                            answer += get_access_error()
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
                            answer += get_access_error()
                else:
                    answer += get_access_error()
        elif 'выключи' in cmd_list or 'отключи' in cmd_list or 'off' in cmd_list:
            if 'свет' in cmd_list and ('везде' in cmd_list or 'доме' in cmd_list or 'дома' in cmd_list):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if p.output and 'свет' in p.ConvertibleTerms and 'дом' in p.ConvertibleTerms:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.set_pin(p, 0)
                                jprint(f'Выключил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Выключил свет везде.\n'
                else:
                    answer += get_access_error()
            elif 'свет' in cmd_list and ('первом' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if 'свет' in p.ConvertibleTerms and 'первом' in p.ConvertibleTerms and (
                                'этаж' in p.ConvertibleTerms or 'этаже' in p.ConvertibleTerms) and p.output:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.set_pin(p, 0)
                                jprint(f'Выключил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Выключил свет на первом этаже.\n'
                else:
                    answer += get_access_error()
            elif 'свет' in cmd_list and ('втором' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if 'свет' in p.ConvertibleTerms and 'втором' in p.ConvertibleTerms and (
                                'этаж' in p.ConvertibleTerms or 'этаже' in p.ConvertibleTerms) and p.output:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.set_pin(p, 0)
                                jprint(f'Выключил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Выключил свет на втором этаже.\n'
                else:
                    answer += get_access_error()
            else:
                # elif 'свет' in cmd_list:
                if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                    findlist = copy.deepcopy(cmd_list)
                    if telegramuser != None:
                        findlist.append(telegramuser.name)
                    WinnerPin = arduino.find_by_auction(findlist)
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
                            answer += get_access_error()
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
                            answer += get_access_error()
                else:
                    answer += get_access_error()
        elif ('верни' in cmd_list and (
                'было' in cmd_list or 'обратно' in cmd_list)) or 'пошутил' in cmd_list or 'шутка' in cmd_list:
            if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                for p in arduino.pins:
                    if (datetime.now() - p.LastRevTime).total_seconds() <= 30:
                        if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                            a = arduino.set_pin(p, p.prevstate)  # prev pin state
                            jprint(f'pin {p.num} is {a}')
                        else:
                            answer += f'{p.description} заблокирован для вас'
                answer += 'Вернул все как было\n'
            else:
                answer += get_access_error()
        elif 'оставь' in cmd_list and 'свет' in cmd_list:
            if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                WinnerPin = arduino.find_by_auction(cmd_list)
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
                            answer += get_access_error()
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
                        answer += get_access_error()
            else:
                answer += get_access_error()
        elif 'заблокируй' in cmd_list or 'заблокирую' in cmd_list:
            if "все" in cmd_list and "выключатели" in cmd_list:
                for p in arduino.pins:
                    if not p.output:
                        p.blocked = True
                answer += f'Заблокировал все выключатели\n'
            elif telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                WinnerPin = arduino.find_by_auction(cmd_list, True)
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
                answer += get_access_error()
        elif 'разблокируй' in cmd_list or 'разблокирую' in cmd_list:
            if "все" in cmd_list and "выключатели" in cmd_list:
                for p in arduino.pins:
                    if not p.output:
                        p.blocked = False
                answer += f'Заблокировал все выключатели\n'
            elif telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                WinnerPin = arduino.find_by_auction(cmd_list, True)
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
                answer += get_access_error()
        elif cmd.find('pinstate') > -1:
            if telegramuser != None and telegramuser.level <= 3 or telegramuser == None:
                try:
                    val = cmd.split(' ')[1]
                except:
                    val = -1
                pin = arduino.find_pin(val)
                if pin != None:
                    if pin.state:
                        answer = f'pin {pin.num} is ON\n'
                    else:
                        answer = f'pin {pin.num} is OFF\n'
                else:
                    answer = f"Can't find the pin with number {val}\n"
            else:
                answer += get_access_error()
        elif cmd.find('loadconfig') > -1 or cmd.find('загрузи конфиг') > -1:
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                answer = arduino.load_config(False)
            else:
                answer += get_access_error()
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
                answer += get_access_error()
        elif cmd.startswith('bind '):
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                try:
                    val = cmd.split(' ')
                    bindto = arduino.find_pin(val[1])
                    if not bindto.output:
                        for i in range(2, len(val)):
                            addpin = arduino.find_pin(val[i])
                            if addpin.output:
                                if not addpin in bindto.binds:
                                    bindto.binds.append(addpin)
                                else:
                                    answer += f'pin {addpin.name} is already in {bindto.name}.binds' + '\n'
                            else:
                                answer += f'pin {addpin.name} is INPUT pin and connot binded to pin {bindto.name}\n'
                        answer += 'pins is binded!\n'
                        if arduino.save_config() == None:
                            answer += 'config is saved\n'
                        else:
                            answer += 'error save config\n'
                    else:
                        answer += f'pin {bindto.name} is OUTPUT pin and you cant bind to it.\n'
                except:
                    answer += 'error bind pins\n'
            else:
                answer += get_access_error()
        elif cmd.startswith('unbind '):
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                try:
                    val = cmd.split(' ')
                    bindto = arduino.find_pin(val[1])
                    if not bindto.output:
                        for i in range(2, len(val)):
                            bindto.binds.remove(arduino.find_pin(val[i]))
                        answer = 'pins is unbinded!\n'
                        if arduino.save_config() == None:
                            answer += 'config is saved\n'
                        else:
                            answer += 'error save config\n'
                    else:
                        answer += f'pin {bindto.name} is OUTPUT pin and you cant bind to it.\n'
                except:
                    answer = 'error unbind pins\n'
            else:
                answer += get_access_error()
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
                answer += get_access_error()
        elif cmd == 'state' or cmd == 'status' or 'статус' in cmd_list:
            if telegramuser != None and telegramuser.level <= 3 or telegramuser == None:
                uptime = gf.difference_between_date(start_time, datetime.now())
                answer += 'ver. ' + VERSION + '   '
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
                pumpsPin = arduino.find_pin("насосы")
                if pumpsPin is not None:
                    if pumpsPin.state:
                        answer += "включены"
                    else:
                        answer += "ВЫКЛЮЧЕНЫ"
                else:
                    answer += "<не могу найти пин насосов  по description 'насосы'>"
                answer += '\n'
                ACNet = 'есть'
                if not arduino.ac_exist:
                    ACNet = 'НЕТ'
                answer += f'Напряжение в сети {ACNet}\n'
                answer += f'Напряжение аккумулятора {arduino.DCVol} V ({arduino.DCVoltageInPercent} %)\n'
            else:
                answer += get_access_error()
        elif cmd == 'exit':
            if telegramuser is None: # выходить можно только из консоли
                jprint('bye...')
                sys.exit()
            else:
                answer += get_access_error()
        elif cmd == 'debug':
            arduino.debug()
        elif cmd == 'warning':
            arduino.warning()
        else:
            answer += 'неизвестная команда\n'

    if message != None:
        telegram_answer_queue.put((message, answer))  # Поместили сообщение в оцередь на обработку
    return answer


def reglament_work():
    if datetime.now().hour >= 19 or datetime.now().hour <= 6:  # включим свет на улице
        if not arduino.LastSetStateOutDoorLight or arduino.LastSetStateOutDoorLight == None:
            arduino.set_pin(arduino.OutDoorLightPin, 1)
            arduino.LastSetStateOutDoorLight = True
    else:
        if arduino.LastSetStateOutDoorLight or arduino.LastSetStateOutDoorLight == None:
            arduino.set_pin(arduino.OutDoorLightPin, 0)
            arduino.LastSetStateOutDoorLight = False

    # Сообщим, что пропало напряжение на входе
    if not arduino.ac_exist and not arduino.ACAlertSended:
        for user in bot.get_users():
            if user.level == 0:
                # if True or user.level == 0 or user.level == 3:
                bot.add_to_queue(user.id, 'Отключилось напряжение на входе в дом!\n')
        arduino.ACAlertSended = True
    elif arduino.ac_exist and arduino.ACAlertSended:
        for user in bot.get_users():
            # if True or user.level == 0 or user.level == 3:
            if user.level == 0:
                _message = 'Ура! Появилось напряжение на входе в дом!\n'
                _message += f'Электричества не было {arduino.time_without_ac(in_str=True)}'

                bot.add_to_queue(user.id, _message)
        arduino.ACAlertSended = False

    # Сообщить, что напряжение аккумулятора низкое
    if arduino.DCVoltageInPercent <= 20 and not arduino.DCVolLowAlertSended:
        for user in bot.get_users():
            if True or user.level == 0 or user.level == 3:
                bot.add_to_queue(user.id,
                                        'Напряжение аккумулятора ниже 20% !!! Электричество скоро отключится.\n')
        arduino.DCVolLowAlertSended = True

    # Реакция пинов на разряд аккумулятора без входного напряжения
    if not arduino.ac_exist:
        for p in arduino.pins:
            if p.output and not p.bcod_reaction and arduino.DCVoltageInPercent <= p.bcod:
                arduino.set_pin(p, 0)
                jprint(f'Отключил {p.description} по разряду аккумулятора')
                p.bcod_reaction = True
                for user in bot.get_users():
                    if user.level <= 1:
                        bot.add_to_queue(user.id, f'Отключил {p.description} по разряду аккумулятора\n')
    else:
        for p in arduino.pins:
            if p.output and p.bcod_reaction and arduino.DCVoltageInPercent > p.bcod:
                p.bcod_reaction = False
                arduino.set_pin(p, p.prevstate)  # Вернем состояние пинов на последнее

# ****** MAIN ******
if __name__ == "__main__":
    start_time = datetime.now()

    # init watchdog
    watchdog = class_watchdog.CWatchDog('/dev/ttyACM0')
    watchdog.start_ping()

    # init arduino
    arduino = class_arduino.Arduino(JARVIS_PATH + ARDUINO_CONFIG_NAME, JARVIS_PATH + ARDUINO_PINSTATE_FILENAME,
                                    NOT_IMPORTANT_WORDS)
    arduino.load_config(bot)

    # Start keyboart queue thread
    input_queue = queue.Queue()
    inputThread = threading.Thread(target=read_kbd_input, args=(input_queue,), daemon=True)
    inputThread.start()

    # Start Telegram bot
    bot.start()

    telegram_answer_queue = queue.Queue()

    # Main loop dunction
    while True:
        if arduino.initialized:
            if (input_queue.qsize() > 0):
                queue_typle = input_queue.get()
                input_str = queue_typle[0]
                user = queue_typle[1]
                message = queue_typle[2]
                answer = command_processing(input_str, user, message)
                jprint(answer)
            arduino.check_input_pins()
            reglament_work()
        else:
            arduino.initialize()
        sleep(0.02)
