import sys
sys.path.append('../')
from modules.gfunctions import *
from modules.class_com import CommunicationServer
from socket import *
from time import sleep
import logging
import random

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s (%(levelname)s) %(asctime)s: %(message)s'
LOG_LEVEL = logging.DEBUG
# LOG_LEVEL = logging.INFO
# LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL,
                        datefmt='%d.%m.%y %H:%M:%S')
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')

info = logging.info
debug = logging.debug

class CommunicationServerTest():
    def __init__(self, ip:str='0.0.0.0', port:int = 8587):
        self._own_server_adress = (ip, port)
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.bind(self._own_server_adress)
        info('port binded')
        self.server_socket.listen(1)
        connection, client_address = self.server_socket.accept()
        info('get connection')
        while True:
            data = connection.recv(1024)
            if not data:
                break
            else:
                data = clear_str(data.decode())
                debug(f'recieved data: {data}')
                # << Оборачиваемая функция
                answer = self.handler(client_address, data)
                # >> Оборачиваемая функция
                connection.sendall(answer.encode())
                debug(f'send data: {answer}')
        connection.close()
        info(f'connection closed')
        self.server_socket.close()
        info(f'socket closed')

    def handler(self, client_address, data):
        pass

class LaserTCPServer(CommunicationServer):
    def __init__(self, port: int = 8587, jarvis: bool = False):
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
        super().__init__('0.0.0.0', port)

    def handler(self, client_address, data):
        x = random.randint(60, 65)
        answer = f'cmd={x} {60} 0'
        # if self.translate_queue.qsize() > 0:
        #     translate_data = self.translate_queue.get()
        #     answer = f'cmd={translate_data[0]} {translate_data[1]} {translate_data[2]}'
        # else:
        #     answer = 'none'
        return answer + '\r'

if __name__ == '__main__':
    server = LaserTCPServer(jarvis=True)
    server.start()
    while True:
        sleep(1)