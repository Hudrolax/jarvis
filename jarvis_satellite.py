import sys
sys.path.append('../')

from modules.class_com import CommunicationClient
from modules.gfunctions import JPrint
from modules.gfunctions import JList
from time import sleep
from config import *
import logging
import threading
import psutil
import subprocess

list = JList
jprint = JPrint.jprint

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s (%(levelname)s) %(asctime)s: %(message)s'
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO
#LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')

class Jarvis_Satellite_client(CommunicationClient):
    logger = logging.getLogger('jarvis satellite')
    logger.setLevel(logging.INFO)

    def __init__(self, *args):
        super().__init__(*args)
        Jarvis_Satellite_client.logger.info('start jarvis satellite')
        self._runned = False
        self._handler_thread = threading.Thread(target=self._handler, args=(), daemon=True)
        self._ping_thread = threading.Thread(target=self._ping, args=(), daemon=True)
        self._miner_is_runned = False

    @staticmethod
    def start_miner():
        subprocess.Popen(MINER_PATH + MINER_START_FILE)
        sleep(10)

    @staticmethod
    def kill_miner():
        warning = Jarvis_Satellite_client.logger.warning
        critical = Jarvis_Satellite_client.logger.critical
        try:
            list_to_kill = MINER_EXE_LIST
        except:
            error_message = 'Нет константы MINER_EXE_LIST типа List в config.py\n'
            error_message += 'нужно добавить:\n'
            error_message += 'MINER_EXE_LIST = []\n'
            error_message += 'MINER_EXE_LIST.append(<имя программы>)\n'
            critical(error_message)

        for proc in psutil.process_iter():
            for miner_exe in list_to_kill:
                if proc.name() == miner_exe:
                    try:
                        proc.kill()
                    except:
                        warning(f"can't kill the {proc.name()}")

    @staticmethod
    def kill_programms_to_instant_kill():
        warning = Jarvis_Satellite_client.logger.warning
        critical = Jarvis_Satellite_client.logger.critical
        try:
            list_to_kill = PROGRAMMS_TO_INSTANT_KILL
        except:
            error_message = 'Нет константы ROGRAMMS_TO_INSTANT_KILL типа List в config.py\n'
            error_message += 'нужно добавить:\n'
            error_message += 'PROGRAMMS_TO_INSTANT_KILL = []\n'
            error_message += 'PROGRAMMS_TO_INSTANT_KILL.append(<имя программы>)\n'
            critical(error_message)

        for proc in psutil.process_iter():
            for miner_exe in list_to_kill:
                if proc.name() == miner_exe:
                    try:
                        proc.kill()
                    except:
                        warning(f"can't kill the {proc.name()}")

    @staticmethod
    def miner_is_runned():
        for proc in psutil.process_iter():
            if proc.name() == MINER_EXE_LIST[0]:
                return True
        return False

    def start(self):
        self._runned = True
        self._handler_thread.start()
        self._ping_thread.start()

    def stop(self):
        self._runned = False
        self.stop()

    def _ping(self):
        debug = Jarvis_Satellite_client.logger.debug
        while self._runned:
            answer = self.send_with_name('ping')
            debug(f'answer is "{answer}"')
            sleep(2)

    def _handler(self):
        debug = Jarvis_Satellite_client.logger.debug
        info = Jarvis_Satellite_client.logger.info
        error = Jarvis_Satellite_client.logger.error
        while self._runned:
            try:
                if self.miner_is_runned():
                    if not self._miner_is_runned:
                        self._miner_is_runned = True
                        jprint('Miner was runned')
                    debug(f'send "miner_is_runned"')
                    answer = self.send_with_name('miner_is_runned')
                    debug(f'answer is "{answer}"')
                    if answer == 'stop_miner':
                        info('get stop_miner command')
                        self.kill_miner()
                else:
                    if self._miner_is_runned:
                        self._miner_is_runned = False
                        jprint('Miner was stopped')
                    debug(f'send "miner_is_not_runned"')
                    answer = self.send_with_name('miner_is_not_runned')
                    debug(f'answer is "{answer}"')
                    if answer == 'start_miner':
                        info('get start_miner command')
                        self.start_miner()
                self.kill_programms_to_instant_kill()
            except:
                error('i get some error in thread')
            sleep(1)


if __name__ == '__main__':
    if SATELLITE_NAME == '':
        raise Exception('SATELLITE_NAME is not exist')
    tcp_client = Jarvis_Satellite_client(SATELLITE_NAME, SATELLITE_IP, SATELLITE_PORT)
    # tcp_client = Jarvis_Satellite_client(SATELLITE_NAME, '192.168.18.3', 8586)
    tcp_client.start()
    # tcp_client.logger.setLevel(logging.DEBUG)

    while True:
        # do something
        sleep(10)