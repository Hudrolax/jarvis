from class_com import CommunicationClient
from gfunctions import JPrint
from gfunctions import JList
list = JList
jprint = JPrint.jprint
import logging
import threading
import psutil

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.DEBUG
#LOG_LEVEL = logging.WARNING


if __name__ == '__main__':
    logger = logging.getLogger('jarvis satellite')
    jprint('start jarvis satellite')
    tcp_client = CommunicationClient('serverx','127.0.0.1',8585)
    tcp_client.send('serverx:hello')
