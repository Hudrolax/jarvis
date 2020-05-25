import sys
sys.path.append('../')

from time import sleep
import threading
from modules.class_com import CommunicationClient

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

def send():
    client = CommunicationClient('test', '192.168.18.3', 8586)
    answer = client.send_with_name('test_message')
    print(answer)

if __name__ == '__main__':
    for k in range(10):
        send()
