import sys
from time import sleep

sys.path.append('../')
from modules.class_com import CommunicationServer

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
    logger = logging.getLogger('laser server')

    def __init__(self, ip: str, port: int, jarvis: bool = False):
        super().__init__(ip, port)
        from modules.class_laser import Laser
        self._name = 'laser_server'
        self.laser = Laser(self, x_min=20, x_max=150, y_min=0, y_max=179)
        self.jarvis = jarvis
        import queue
        self.translate_queue = queue.Queue()
        if not jarvis:
            from modules.class_keyboard_hook import KeyBoardHook
            output_queue = queue.Queue()
            self.key_hook = KeyBoardHook(self, output_queue)

    def handler(self, client_address, data):
        # client_address - адрес клиента
        # data - очищенные данные - только строка
        if self.translate_queue.qsize() > 0:
            translate_data = self.translate_queue.get()
            answer = f'cmd={translate_data[0]} {translate_data[1]} {translate_data[2]}'
        else:
            answer = 'none'
        return answer + '\r'


if __name__ == '__main__':
    server = LaserTCPServer('0.0.0.0', 8587, False)
    server.logger.setLevel(logging.DEBUG)
    server.start()
    server.laser.start_game()
    while True:
        pass
        if (server.key_hook.queue.qsize() > 0):
            queue_str = server.key_hook.queue.get()
            if queue_str == 'l':
                server.laser.rev_laser()
            elif queue_str == 'g':
                server.laser.rev_game_mode()
            elif queue_str == 'h':
                server.laser.homing()
            elif queue_str == 'c':
                print(f'X{server.laser.x} Y{server.laser.y}')
            else:
                server.laser.move_axis(direction=queue_str, speed_x=2, speed_y=2)
