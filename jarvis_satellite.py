from class_com import CommunicationClient
from gfunctions import JPrint
from gfunctions import JList
from time import sleep
list = JList
jprint = JPrint.jprint
import logging
import threading
import psutil

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s - %(levelname)s - %(message)s'
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO
#LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL)
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

class Jarvis_Satellite_client(CommunicationClient):
    logger = logging.getLogger('jarvis satellite')

    def __init__(self, *args):
        super().__init__(*args)
        Jarvis_Satellite_client.logger.info('start jarvis satellite')
        self._runned = False
        self.thread = threading.Thread(target=self.handler, args=(), daemon=True)

    def run(self):
        self._runned = True
        self.thread.start()

    def stop(self):
        self._runned = True

    def ping(self):
        return self.send_with_name('ping')

    def handler(self):
        while self._runned:
            answer = self.ping()
            sleep(0.1)



if __name__ == '__main__':
    tcp_client = Jarvis_Satellite_client('serverx','127.0.0.1',8585)
    answer = tcp_client.send_with_name('ping')
    print(answer)

