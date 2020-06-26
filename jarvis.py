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

    def __init__(self):
        # init telegram bot
        self.bot = TelegramBot(path=JARVIS_PATH, list_file=GOOD_PROXY_LIST, token=API_TOKEN,
                          threaded=False)  # Конструктор бота

        self.runned = True
        self.logger.info('Start jarvis')

        # init watchdog
        self.watchdog = class_watchdog.CWatchDog('/dev/ttyACM0')
        self.watchdog.start_ping()
        self.logger.info('init watchdog')

        # init arduino
        self.arduino = class_arduino.Arduino(JARVIS_PATH + ARDUINO_CONFIG_NAME, JARVIS_PATH + ARDUINO_PINSTATE_FILENAME,
                                               NOT_IMPORTANT_WORDS)
        self.arduino.load_config(self.bot)
        self.logger.info('init arduino and load config')

        # Start keyboart queue thread
        self.input_queue = queue.Queue()

        self.inputThread = threading.Thread(target=self.read_kbd_input, args=(), daemon=True)
        self.inputThread.start()
        self.logger.info('start keyboard thread')

        # Start Telegram bot
        self.bot.start()
        self.logger.info('start telegram bot')

        self.telegram_answer_queue = queue.Queue()

        # start satellite server
        self.satellite_server = Jarvis_Satellite_Server(ip='0.0.0.0', port=SATELLITE_PORT)
        self.satellite_server.add_miner('zeon')
        self.satellite_server.add_miner('serverx')
        self.satellite_server.add_miner('tekilla')
        self.satellite_server.start()
        self.logger.info('start satellite server')

        # laser turret server
        self.laser_turret = LaserTCPServer('0.0.0.0', 8586, jarvis=True)
        self.laser_turret.start()

        self.command_processing = CommandProcessing(self.arduino, self.telegram_answer_queue, self.bot,
                                                      self.satellite_server, self.laser_turret)

    # Function of input in thread
    def read_kbd_input(self):
        while self.runned:
            # Receive keyboard input from user.
            try:
                input_str = input()
                jprint('Enter command: ' + input_str)
                self.input_queue.put((input_str, None, None))
            except:
                continue

    def reglament_work(self):
        if (datetime.now().month >= 10 and datetime.now().month <= 4 and
            (datetime.now().hour >= 19 or datetime.now().hour <= 6)) or \
                (datetime.now().month < 10 and datetime.now().month > 4 and
                 (datetime.now().hour >= 20 or datetime.now().hour <= 5)):  # включим свет на улице
            if not self.arduino.LastSetStateOutDoorLight or self.arduino.LastSetStateOutDoorLight == None:
                self.arduino.set_pin(self.arduino.OutDoorLightPin, 1)
                self.arduino.LastSetStateOutDoorLight = True
        else:
            if self.arduino.LastSetStateOutDoorLight or self.arduino.LastSetStateOutDoorLight == None:
                self.arduino.set_pin(self.arduino.OutDoorLightPin, 0)
                self.arduino.LastSetStateOutDoorLight = False

        # Сообщим, что пропало напряжение на входе
        if not self.arduino.ac_exist and not self.arduino.ac_alert_sended:
            for user in self.bot.get_users():
                if user.level == 0:
                    # if True or user.level == 0 or user.level == 3:
                    self.bot.add_to_queue(user.id, 'Отключилось напряжение на входе в дом!\n')
            self.arduino.ac_alert_sended = True
        elif self.arduino.ac_exist and self.arduino.ac_alert_sended:
            for user in self.bot.get_users():
                # if True or user.level == 0 or user.level == 3:
                if user.level == 0:
                    _message = 'Ура! Появилось напряжение на входе в дом!\n'
                    _message += f'Электричества не было {self.arduino.time_without_ac(in_str=True)}'

                    self.bot.add_to_queue(user.id, _message)
            self.arduino.ac_alert_sended = False

        # Сообщить, что напряжение аккумулятора низкое
        if self.arduino.dc_voltage_in_percent <= 20 and not self.arduino.dc_low_alert_sended:
            for user in self.bot.get_users():
                if True or user.level == 0 or user.level == 3:
                    self.bot.add_to_queue(user.id,
                                     'Напряжение аккумулятора ниже 20% !!! Электричество скоро отключится.\n')
            self.arduino.dc_low_alert_sended = True

        # Реакция пинов на разряд аккумулятора без входного напряжения
        if not self.arduino.ac_exist:
            # Отключаем пины по уровню разряда, если ни включены
            for p in self.arduino.pins:
                if p.output and p.state and not p.bcod_reaction and self.arduino.dc_voltage_in_percent <= p.bcod:
                    self.arduino.set_pin(p, 0)
                    jprint(f'Отключил {p.description} по разряду аккумулятора')
                    p.bcod_reaction = True
                    for user in self.bot.get_users():
                        if user.level <= 1:
                            self.bot.add_to_queue(user.id, f'Отключил {p.description} по разряду аккумулятора\n')
            # Отключаем майнеры, если они включены
            self.satellite_server.stop_miners(bcod_reaction=True, bot=self.bot)
        else:
            # Включаем пины, если отключали их по уровню разряда
            for p in self.arduino.pins:
                if p.output and p.bcod_reaction:
                    p.bcod_reaction = False
                    if not p.state:
                        jprint(f'Включил {p.description} обратно')
                        self.arduino.set_pin(p, 1)  # Вернем состояние пинов на последнее
                        for user in self.bot.get_users():
                            if user.level <= 1:
                                self.bot.add_to_queue(user.id, f'Включил {p.description} обратно\n')
            # Включаем майнеры, если мы их отключали
            self.satellite_server.start_miners(bcod_reaction=True, bot=self.bot)

    def main_loop(self):
        # Main loop dunction
        while self.runned:
            if self.arduino.initialized:
                if (self.input_queue.qsize() > 0):
                    queue_typle = self.input_queue.get()
                    input_str = queue_typle[0]
                    user = queue_typle[1]
                    message = queue_typle[2]
                    answer = self.command_processing.command_processing(input_str, user, message)
                    # if answer == 'reload laser\n':
                    #     LaserTCPServer = reload(LaserTCPServer)
                    jprint(answer)
                self.arduino.check_input_pins()
                self.reglament_work()
            else:
                self.arduino.initialize()
            sleep(0.02)
        self.satellite_server.stop()
        self.bot.stop()
        sleep(2)  # wait for stop threads

jarvis = Jarvis()
 # Telegram bot
@jarvis.bot.message_handler(content_types=['text'])
def get_text_messages(message):
    _user = None
    for user in jarvis.bot.users:
        if str(message.from_user.id) == user.id:
            _user = user
            break
    if message.text == "привет":
        jarvis.bot.reply_to(message, "Привет, чем я могу тебе помочь?")
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

            jarvis.bot.reply_to(message, helpmessage)
        else:
            jarvis.bot.reply_to(message, "Кто ты чудовище?")
    elif message.text == 'getmyid':
        jarvis.bot.reply_to(message, "Ваш ID: %s" % message.from_user.id)
    elif message.text == 'getconfig':
        if _user != None:
            doc = open(jarvis.arduino.config_path, 'rb')
            jarvis.bot.send_document(message.from_user.id, doc)
        else:
            jarvis.bot.reply_to(message, "Кто ты чудовище?")
    else:
        if _user is not None:
            jarvis.input_queue.put((message.text, _user, message))  # Поместили сообщение в оцередь на обработку
            __answe_wait_time = 5
            while __answe_wait_time > 0:
                if (jarvis.telegram_answer_queue.qsize() > 0):
                    queue_typle = jarvis.telegram_answer_queue.get()
                    get_message = queue_typle[0]
                    answer = queue_typle[1]
                    if get_message == message:
                        jarvis.bot.reply_to(message, answer)
                        break
                    else:
                        jarvis.telegram_answer_queue.put((get_message, answer))

                __answe_wait_time -= 1
                sleep(1)
        else:
            Jarvis.bot.reply_to(message, "Кто ты чудовище?")

@jarvis.bot.message_handler(content_types=["sticker", 'document'])
def handle_docs_audio(message):
    _user = None
    for user in jarvis.bot.users:
        if str(message.from_user.id) == user.id:
            _user = user
            break
    if _user != None:
        if message.content_type == 'sticker':
            # Получим id Стикера
            sticker_id = message.sticker.file_id
            jarvis.bot.send_message(message.from_user.id, str(sticker_id))
        elif message.content_type == 'document':
            if message.document.file_name == 'config.txt':
                file_info = jarvis.bot.get_file(message.document.file_id)
                downloaded_file = jarvis.bot.download_file(file_info.file_path)
                with open(jarvis.arduino.config_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                test_config = jarvis.arduino.load_config(False)
                if test_config == 'config loaded!':
                    jarvis.bot.reply_to(message, "конфиг загрузил и применил")
                else:
                    jarvis.bot.reply_to(message, "почему-то не вышло загрузить конфиг")
            else:
                jarvis.bot.send_message(message.from_user.id,
                                 'Не знаю что за файл такой ты мне шлешь. Мне нужен config.txt.')
    else:
        jarvis.bot.reply_to(message, "Кто ты чудовище?")

# ****** MAIN ******
if __name__ == "__main__":
    jarvis = Jarvis()
    jarvis.main_loop()