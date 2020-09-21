import sys
sys.path.append('../')
from config import *
from time import sleep
from datetime import datetime
import threading
import queue
import modules.class_arduino as class_arduino
import modules.class_watchdog as class_watchdog
from modules.gfunctions import JPrint
jprint = JPrint.jprint
from modules.telegram_bot import TelegramBot
from modules.class_command_processing import CommandProcessing
from modules.class_jarvis_server import Jarvis_Satellite_Server
from modules.laser_server import LaserTCPServer
from modules.class_sensors import Sensors
import logging

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s (%(levelname)s) %(asctime)s: %(message)s'
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')

class Jarvis:
    logger = logging.getLogger('jarvis')
    logger.setLevel(logging.INFO)

    def __init__(self):
        # init telegram bot
        self.bot = TelegramBot(self, path=JARVIS_PATH, list_file=GOOD_PROXY_LIST, token=API_TOKEN,
                          threaded=False)  # Конструктор бота

        self.runned = True
        self.sensors = Sensors(self)
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
        self.satellite_server = Jarvis_Satellite_Server(self, ip='0.0.0.0', port=SATELLITE_PORT)
        self.satellite_server.add_miner('zeon', instant_off_by_poweroff=True, shutdown_threshold=(160, 180))
        self.satellite_server.add_miner('serverx', instant_off_by_poweroff=True, shutdown_threshold=(160, 170), shutdown_no_ac_sec=600)
        self.satellite_server.add_miner('tekilla', instant_off_by_poweroff=True)
        self.satellite_server.add_miner('LK_rig1', instant_off_by_poweroff=False, shutdown_threshold=(160, 170))
        self.satellite_server.add_miner('LK_rig2', instant_off_by_poweroff=False, shutdown_threshold=(160, 170))
        self.satellite_server.add_miner('LK_rig4', instant_off_by_poweroff=False, shutdown_threshold=(160, 170))
        self.satellite_server.add_miner('LK_rig10', instant_off_by_poweroff=False, shutdown_threshold=(160, 170))
        self.satellite_server.start()
        self.logger.info('start satellite server')

        # laser turret server
        self.laser_turret = LaserTCPServer('0.0.0.0', 8586, jarvis=True)
        self.laser_turret.start()

        self.command_processing = CommandProcessing(self)

        # self.arduino_loop_thread = threading.Thread(target=self.arduino_loop, args=(), daemon=True)
        # self.arduino_loop_thread.start()
        # self.logger.info('start arduino_loop thread')

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
        """
        Регламентные задания, выполняются по времени или по событию
        """
        #управление освещением на улице
        self._outdoor_light_work()

        # Сообщим, что пропало напряжение на входе
        if not self.arduino.ac_exist and not self.arduino.ac_alert_sended:
            self.bot.send_message_to_admin('Отключилось напряжение на входе в дом!')
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
            # Отключаем пины по уровню разряда, если они включены
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

        # включение / отключение майнеров по входному напряжению
        #self.satellite_server.shutdown_threshold_action()
        # отключение питания сателлитов если нету электричества некоторое время
        self.satellite_server.shutdown_by_ac_loss_timer()
        # сигнализация в коридоре
        self.satellite_server.arduino_sensors.alert_func()

    def _outdoor_light_work(self):
        """
        управление освещением на улице
        """
        if self.satellite_server.arduino_sensors.outside_lamp_on():  # включим свет на улице
            if not self.arduino.last_set_status_outdoor_light or self.arduino.last_set_status_outdoor_light == None:
                self.arduino.set_pin(self.arduino.outdoor_light_pin, 1)
                self.arduino.last_set_status_outdoor_light = True
        elif self.satellite_server.arduino_sensors.outside_lamp_off():
            if self.arduino.last_set_status_outdoor_light or self.arduino.last_set_status_outdoor_light == None:
                self.arduino.set_pin(self.arduino.outdoor_light_pin, 0)
                self.arduino.last_set_status_outdoor_light = False

    def check_inputs_pins(self):
        self.arduino.check_input_pins()

    def arduino_loop(self):
        while self.runned:
            if self.arduino.initialized:
                self.check_inputs_pins()
                self.reglament_work()
            sleep(0.01)

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
                    jprint(answer)
                self.check_inputs_pins()
                self.reglament_work()
            else:
                self.arduino.initialize()
            sleep(0.02)
        self.satellite_server.stop()
        self.bot.stop()
        sleep(2)  # wait for stop threads