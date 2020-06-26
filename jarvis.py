# Sergey Nazarov 17.05.2020
import sys
sys.path.append('../')
from importlib import reload
from config import *
from time import sleep
from datetime import datetime
import threading
import queue
import modules.class_arduino as class_arduino
import modules.class_watchdog as class_watchdog
from modules.gfunctions import JPrint
from modules.gfunctions import Runned
from modules.telegram_bot import TelegramBot
from modules.class_command_processing import CommandProcessing
from modules.class_jarvis_server import Jarvis_Satellite_Server
from modules.laser_server import LaserTCPServer
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

class Jarvis:
    logger = logging.getLogger('main')
    logger.setLevel(logging.INFO)

    # Function of input in thread
    def read_kbd_input(self):
        while self.runned.runned:
            # Receive keyboard input from user.
            try:
                input_str = input()
                jprint('Enter command: ' + input_str)
                self.input_queue.put((input_str, None, None))
            except:
                continue

    # init telegram bot
    runned = Runned
    runned.runned = True
    bot = TelegramBot(path=JARVIS_PATH, list_file=GOOD_PROXY_LIST, token=API_TOKEN,
                             threaded=False)  # Конструктор бота
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
    inputThread = threading.Thread(target=read_kbd_input, args=(), daemon=True)
    inputThread.start()
    logger.info('start keyboard thread')

    # Start Telegram bot
    bot.start()
    logger.info('start telegram bot')

    telegram_answer_queue = queue.Queue()

    # start satellite server
    satellite_server = Jarvis_Satellite_Server(ip='0.0.0.0', port=SATELLITE_PORT)
    satellite_server.add_miner('zeon')
    satellite_server.add_miner('serverx')
    satellite_server.add_miner('tekilla')
    satellite_server.start()
    logger.info('start satellite server')

    # laser turret server
    laser_turret = LaserTCPServer('0.0.0.0', 8586, jarvis=True)
    laser_turret.start()

    command_processing = CommandProcessing(arduino, telegram_answer_queue, bot,
                                                  satellite_server, laser_turret)


    # Telegram bot
    @bot.message_handler(content_types=['text'])
    def get_text_messages(self, message):

        _user = None
        for user in self.bot.users:
            if str(message.from_user.id) == user.id:
                _user = user
                break
        if message.text == "привет":
            Jarvis.bot.reply_to(message, "Привет, чем я могу тебе помочь?")
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

                Jarvis.bot.reply_to(message, helpmessage)
            else:
                Jarvis.bot.reply_to(message, "Кто ты чудовище?")
        elif message.text == 'getmyid':
            Jarvis.bot.reply_to(message, "Ваш ID: %s" % message.from_user.id)
        elif message.text == 'getconfig':
            if _user != None:
                doc = open(self.arduino.config_path, 'rb')
                Jarvis.bot.send_document(message.from_user.id, doc)
            else:
                Jarvis.bot.reply_to(message, "Кто ты чудовище?")
        else:
            if _user is not None:
                Jarvis.input_queue.put((message.text, _user, message))  # Поместили сообщение в оцередь на обработку
                __answe_wait_time = 5
                while __answe_wait_time > 0:
                    if (Jarvis.telegram_answer_queue.qsize() > 0):
                        queue_typle = Jarvis.telegram_answer_queue.get()
                        get_message = queue_typle[0]
                        answer = queue_typle[1]
                        if get_message == message:
                            Jarvis.bot.reply_to(message, answer)
                            break
                        else:
                            Jarvis.telegram_answer_queue.put((get_message, answer))

                    __answe_wait_time -= 1
                    sleep(1)
            else:
                Jarvis.bot.reply_to(message, "Кто ты чудовище?")

    @bot.message_handler(content_types=["sticker", 'document'])
    def handle_docs_audio(message):
        _user = None
        for user in Jarvis.bot.users:
            if str(message.from_user.id) == user.id:
                _user = user
                break
        if _user != None:
            if message.content_type == 'sticker':
                # Получим id Стикера
                sticker_id = message.sticker.file_id
                Jarvis.bot.send_message(message.from_user.id, str(sticker_id))
            elif message.content_type == 'document':
                if message.document.file_name == 'config.txt':
                    file_info = Jarvis.bot.get_file(message.document.file_id)
                    downloaded_file = Jarvis.bot.download_file(file_info.file_path)
                    with open(Jarvis.arduino.config_path, 'wb') as new_file:
                        new_file.write(downloaded_file)
                    test_config = Jarvis.arduino.load_config(False)
                    if test_config == 'config loaded!':
                        Jarvis.bot.reply_to(message, "конфиг загрузил и применил")
                    else:
                        Jarvis.bot.reply_to(message, "почему-то не вышло загрузить конфиг")
                else:
                    Jarvis.bot.send_message(message.from_user.id,
                                     'Не знаю что за файл такой ты мне шлешь. Мне нужен config.txt.')
        else:
            Jarvis.bot.reply_to(message, "Кто ты чудовище?")

    def reglament_work(self):
        if (datetime.now().month >= 10 and datetime.now().month <= 4 and
            (datetime.now().hour >= 19 or datetime.now().hour <= 6)) or \
                (datetime.now().month < 10 and datetime.now().month > 4 and
                 (datetime.now().hour >= 20 or datetime.now().hour <= 5)):  # включим свет на улице
            if not Jarvis.arduino.LastSetStateOutDoorLight or Jarvis.arduino.LastSetStateOutDoorLight == None:
                Jarvis.arduino.set_pin(Jarvis.arduino.OutDoorLightPin, 1)
                Jarvis.arduino.LastSetStateOutDoorLight = True
        else:
            if Jarvis.arduino.LastSetStateOutDoorLight or Jarvis.arduino.LastSetStateOutDoorLight == None:
                Jarvis.arduino.set_pin(Jarvis.arduino.OutDoorLightPin, 0)
                Jarvis.arduino.LastSetStateOutDoorLight = False

        # Сообщим, что пропало напряжение на входе
        if not Jarvis.arduino.ac_exist and not Jarvis.arduino.ac_alert_sended:
            for user in Jarvis.bot.get_users():
                if user.level == 0:
                    # if True or user.level == 0 or user.level == 3:
                    Jarvis.bot.add_to_queue(user.id, 'Отключилось напряжение на входе в дом!\n')
            Jarvis.arduino.ac_alert_sended = True
        elif Jarvis.arduino.ac_exist and Jarvis.arduino.ac_alert_sended:
            for user in Jarvis.bot.get_users():
                # if True or user.level == 0 or user.level == 3:
                if user.level == 0:
                    _message = 'Ура! Появилось напряжение на входе в дом!\n'
                    _message += f'Электричества не было {Jarvis.arduino.time_without_ac(in_str=True)}'

                    Jarvis.bot.add_to_queue(user.id, _message)
            Jarvis.arduino.ac_alert_sended = False

        # Сообщить, что напряжение аккумулятора низкое
        if Jarvis.arduino.dc_voltage_in_percent <= 20 and not Jarvis.arduino.dc_low_alert_sended:
            for user in Jarvis.bot.get_users():
                if True or user.level == 0 or user.level == 3:
                    Jarvis.bot.add_to_queue(user.id,
                                     'Напряжение аккумулятора ниже 20% !!! Электричество скоро отключится.\n')
            Jarvis.arduino.dc_low_alert_sended = True

        # Реакция пинов на разряд аккумулятора без входного напряжения
        if not Jarvis.arduino.ac_exist:
            # Отключаем пины по уровню разряда, если ни включены
            for p in Jarvis.arduino.pins:
                if p.output and p.state and not p.bcod_reaction and Jarvis.arduino.dc_voltage_in_percent <= p.bcod:
                    Jarvis.arduino.set_pin(p, 0)
                    jprint(f'Отключил {p.description} по разряду аккумулятора')
                    p.bcod_reaction = True
                    for user in Jarvis.bot.get_users():
                        if user.level <= 1:
                            Jarvis.bot.add_to_queue(user.id, f'Отключил {p.description} по разряду аккумулятора\n')
            # Отключаем майнеры, если они включены
            Jarvis.satellite_server.stop_miners(bcod_reaction=True, bot=Jarvis.bot)
        else:
            # Включаем пины, если отключали их по уровню разряда
            for p in Jarvis.arduino.pins:
                if p.output and p.bcod_reaction:
                    p.bcod_reaction = False
                    if not p.state:
                        jprint(f'Включил {p.description} обратно')
                        Jarvis.arduino.set_pin(p, 1)  # Вернем состояние пинов на последнее
                        for user in Jarvis.bot.get_users():
                            if user.level <= 1:
                                Jarvis.bot.add_to_queue(user.id, f'Включил {p.description} обратно\n')
            # Включаем майнеры, если мы их отключали
            Jarvis.satellite_server.start_miners(bcod_reaction=True, bot=Jarvis.bot)

    @staticmethod
    def main_loop():
        # Main loop dunction
        while Jarvis.runned.runned:
            if Jarvis.arduino.initialized:
                if (Jarvis.input_queue.qsize() > 0):
                    queue_typle = Jarvis.input_queue.get()
                    input_str = queue_typle[0]
                    user = queue_typle[1]
                    message = queue_typle[2]
                    answer = Jarvis.command_processing.command_processing(input_str, user, message)
                    if answer == 'reload laser\n':
                        LaserTCPServer = reload(LaserTCPServer)
                    jprint(answer)
                Jarvis.arduino.check_input_pins()
                Jarvis.reglament_work()
            else:
                Jarvis.arduino.initialize()
            sleep(0.02)
        Jarvis.satellite_server.stop()
        Jarvis.bot.stop()
        sleep(2)  # wait for stop threads

# ****** MAIN ******
if __name__ == "__main__":
    Jarvis.main_loop()