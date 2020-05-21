from class_com import CommunicationClient
from gfunctions import JPrint
from gfunctions import JList
from time import sleep
from config import *
from config import *
list = JList
jprint = JPrint.jprint
import logging
import threading
import psutil
import subprocess

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

    @staticmethod
    def start_miner():
        subprocess.Popen(MINER_PATH + MINER_START_FILE)
        sleep(10)

    @staticmethod
    def kill_miner():
        warning = Jarvis_Satellite_client.logger.warning
        for proc in psutil.process_iter():
            for miner_exe in MINER_EXE_LIST:
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
        self._runned = True

    def _ping(self):
        debug = Jarvis_Satellite_client.logger.debug
        while self._runned:
            answer = self.send_with_name('ping')
            debug(f'answer is "{answer}"')
            sleep(2)

    def _handler(self):
        debug = Jarvis_Satellite_client.logger.debug
        info = Jarvis_Satellite_client.logger.info
        while self._runned:
            if self.miner_is_runned():
                debug(f'send "miner_is_runned"')
                answer = self.send_with_name('miner_is_runned')
                debug(f'answer is "{answer}"')
                if answer == 'stop_miner':
                    info('get stop_miner command')
                    self.kill_miner()
            else:
                debug(f'send "miner_is_not_runned"')
                answer = self.send_with_name('miner_is_not_runned')
                debug(f'answer is "{answer}"')
                if answer == 'start_miner':
                    info('get start_miner command')
                    self.start_miner()
            sleep(1)



if __name__ == '__main__':
    tcp_client = Jarvis_Satellite_client('zeon', SATELLITE_IP, SATELLITE_PORT)
    tcp_client.start()

    while True:
        # do something
        sleep(1)