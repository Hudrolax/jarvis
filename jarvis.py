# Sergey Nazarov 17.05.2020
from config import *
from time import sleep
from datetime import datetime
import threading
import queue
import class_arduino
import class_watchdog
from gfunctions import JPrint
from telegram_bot import TelegramBot
from class_command_processing import CommandProcessing
from class_jarvis_server import Jarvis_Satellite_Server
import logging

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s (%(levelname)s) %(asctime)s: %(message)s'
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')

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
        # Отключаем пины по уровню разряда, если ни включены
        for p in arduino.pins:
            if p.output and p.state and not p.bcod_reaction and arduino.DCVoltageInPercent <= p.bcod:
                arduino.set_pin(p, 0)
                jprint(f'Отключил {p.description} по разряду аккумулятора')
                p.bcod_reaction = True
                for user in bot.get_users():
                    if user.level <= 1:
                        bot.add_to_queue(user.id, f'Отключил {p.description} по разряду аккумулятора\n')
        # Отключаем майнеры, если они включены
        satellite_server.stop_miners(bcod_reaction=True)
        for user in bot.get_users():
            if user.level <= 0:
                bot.add_to_queue(user.id, f'Отключил все майнеры по разряду аккумулятора\n')
    else:
        # Включаем пины, если отключали их по уровню разряда
        for p in arduino.pins:
            if p.output and p.bcod_reaction:
                p.bcod_reaction = False
                if not p.state:
                    jprint(f'Включил {p.description} обратно')
                    arduino.set_pin(p, 1)  # Вернем состояние пинов на последнее
                    for user in bot.get_users():
                        if user.level <= 1:
                            bot.add_to_queue(user.id, f'Включил {p.description} обратно\n')
        # Включаем майнеры, если мы их отключали
        satellite_server.start_miners(bcod_reaction=True)
        for user in bot.get_users():
            if user.level <= 0:
                bot.add_to_queue(user.id, f'Включил майнеры обратно\n')

# ****** MAIN ******
if __name__ == "__main__":
    logger = logging.getLogger('main')
    logger.setLevel(logging.INFO)

    logger.info('Start jarvis')

    # init watchdog
    watchdog = class_watchdog.CWatchDog('/dev/ttyACM0')
    watchdog.start_ping()
    logger.info('init watchdog')

    # init arduino
    arduino = class_arduino.Arduino(JARVIS_PATH + ARDUINO_CONFIG_NAME, JARVIS_PATH + ARDUINO_PINSTATE_FILENAME,
                                    NOT_IMPORTANT_WORDS)
    arduino.load_config(bot)
    logger.info('init arduino and load config')

    # Start keyboart queue thread
    input_queue = queue.Queue()
    inputThread = threading.Thread(target=read_kbd_input, args=(input_queue,), daemon=True)
    inputThread.start()
    logger.info('start keyboard thread')

    # Start Telegram bot
    bot.start()
    logger.info('start telegram bot')

    telegram_answer_queue = queue.Queue()

    command_processing = CommandProcessing(arduino, telegram_answer_queue)

    #start satellite server
    satellite_server = Jarvis_Satellite_Server(name='Jarvis', ip=SATELLITE_IP, port=SATELLITE_PORT)
    satellite_server.add_miner('zeon')
    satellite_server.start()
    logger.info('start satellite server')

    # Main loop dunction
    while True:
        if arduino.initialized:
            if (input_queue.qsize() > 0):
                queue_typle = input_queue.get()
                input_str = queue_typle[0]
                user = queue_typle[1]
                message = queue_typle[2]
                answer = command_processing.command_processing(input_str, user, message, bot)
                jprint(answer)
            arduino.check_input_pins()
            reglament_work()
        else:
            arduino.initialize()
        sleep(0.02)
