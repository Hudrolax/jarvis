import sys
sys.path.append('../')

from modules.class_com import CommunicationServer
from time import sleep

import logging
WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s (%(levelname)s) %(asctime)s: %(message)s'
# LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO
# LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL,
                        datefmt='%d.%m.%y %H:%M:%S')
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')

if __name__ == '__main__':
    class TestTCPServer(CommunicationServer):
        def __init__(self, *args):
            super().__init__(*args)
            self.b = False

        def handler(self, client_address, data):
            # client_address - адрес клиента
            # data - очищенные данные - только строка
            data = data.split(':')
            if len(data) == 2:
                name = data[0]
                message = data[1]
                if name == 'test':
                    answer = 'ok'
                elif name == 'wemos1':
                    self.b = not self.b
                    if self.b:
                        answer = 'on\r'
                    else:
                        answer = 'off\r'
            else:
                answer = 'none'
            return answer


    server = TestTCPServer('root', '192.168.18.3', 8586)
    server.start()
    while True:
        sleep(1)