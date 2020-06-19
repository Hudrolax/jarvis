import sys
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

    @staticmethod
    def set_debug():
        LaserTCPServer.logger.setLevel(logging.DEBUG)
        print(f'set DEBUG level in {LaserTCPServer.logger.name} logger')

    @staticmethod
    def set_warning():
        LaserTCPServer.logger.setLevel(logging.WARNING)
        print(f'set WARNING level in {LaserTCPServer.logger.name} logger')

    @staticmethod
    def set_info():
        LaserTCPServer.logger.setLevel(logging.INFO)
        print(f'set INFO level in {LaserTCPServer.logger.name} logger')

    def __init__(self, ip:str, port:int, jarvis:bool=False):
        super().__init__(ip, port)
        from modules.class_laser import Laser
        self._name = 'laser_server'
        self.laser = Laser(x_min=20, x_max=150, y_min=0, y_max=179)
        self.laser.parent = self
        self.jarvis = jarvis
        if not jarvis:
            import queue
            output_queue = queue.Queue()
            from modules.class_keyboard_hook import KeyBoardHook
            self.key_hook = KeyBoardHook(self, output_queue)

    @property
    def name(self):
        return self._name

    def handler(self, client_address, data):
        # client_address - адрес клиента
        # data - очищенные данные - только строка
        if self.laser.translate_data_to_laser:
            answer = f'{self.laser.x} {self.laser.y} {self.laser.laser_state_int}'
        else:
            answer = 'none'
        return answer+'\r'

if __name__ == '__main__':
    server = LaserTCPServer('root', '192.168.18.3', 8586, jarvis=False)
    server.start()
    while True:
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