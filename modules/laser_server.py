import sys
sys.path.append('../')
import queue
from modules.class_com import CommunicationServer
from modules.class_laser import Laser
from modules.class_keyboard_hook import KeyBoardHook
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


class LaserTCPServer(CommunicationServer):
    logger = logging.getLogger('tcp server')

    def __init__(self, key_hook, laser, *args):
        super().__init__(*args)
        self.laser = laser
        self.key_hook = key_hook

    def handler(self, client_address, data):
        # client_address - адрес клиента
        # data - очищенные данные - только строка

        # logging.info(data)
        self.laser.distance = data
        if (self.key_hook.queue.qsize() > 0):
            queue_str = self.key_hook.queue.get()
            if queue_str == 'l':
                self.laser.rev_laser()
            elif queue_str == 'g':
                self.laser.rev_game_mode()
            elif queue_str == 'h':
                self.laser.homing()
            elif queue_str == 'c':
                print(f'X{self.laser.x} Y{self.laser.y}')
            elif queue_str == 'd':
                print(f'distance = {self.laser.distance}')
            else:
                self.laser.move_axis(direction=queue_str, speed_x=2, speed_y=2)

        answer = f'{self.laser.x} {self.laser.y} {self.laser.laser_state_int}'
        return answer+'\r'

if __name__ == '__main__':
    output_queue = queue.Queue()
    key_hook = KeyBoardHook(output_queue)
    laser = Laser(x_min=20, x_max=150, y_min=0, y_max=179)

    server = LaserTCPServer(key_hook, laser, 'root', '192.168.18.3', 8585)
    server.start()
    while True:
        sleep(1)