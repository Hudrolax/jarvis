from gfunctions import *
import socket
import logging
import threading
from config import *

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

class CommunicationServer():
    logger = logging.getLogger(f'Comm server')
    logger.setLevel(logging.INFO)

    def __init__(self, name:str='root', ip:str=SATELLITE_IP, port:int = SATELLITE_PORT):
        critical = CommunicationServer.logger.critical
        if not isinstance(name, str):
            raise Exception("CommunicationServer init error. 'name' is not 'str' type.")
        self.name = name

        if not isinstance(ip, str):
            critical("init error. 'ip' is not 'str' type.")
            raise Exception("init error. 'ip' is not 'str' type.")
        if not isinstance(port, int):
            critical("init error. 'port' is not 'int' type.")
            raise Exception("init error. 'port' is not 'int' type.")

        self._own_server_adress = (ip, port)
        self._started = False
        self._thread = threading.Thread(target=self._tcp_server, args=(), daemon=True)

    def __str__(self):
        return self.name

    @property
    def started(self):
        return self._started

    @property
    def ip(self):
        return self._own_server_adress[0]

    @property
    def port(self):
        return self._own_server_adress[1]

    def start(self):
        self._started = True
        self._thread.start()

    def stop(self):
        self._started = False

    def handler(self, client, data):
        #CommunicationServer.logger.debug('call handler')
        return 'None'

    def _tcp_server(self): # hendler take client:str and data:str parameters
        debug = CommunicationServer.logger.debug
        info = CommunicationServer.logger.info
        server_socket = socket.socket()
        while True:
            try:
                server_socket.bind(self._own_server_adress)
                break
            except:
                try:
                    server_socket.close()
                except:
                    pass
            raise Exception(f"Can't bind {self.ip}:{self.port}")
            sleep(1)
        server_socket.listen(1)
        info(f'server "{self.name}" is started on {self.ip}:{self.port}')
        while self._started:
            connection, client_address = server_socket.accept()
            debug(f"new connection from {client_address}")
            data = clear_str(connection.recv(1024).decode("utf-8"))
            debug(f"received data: {data}")
            # отправляем данные обработчику и получает ответ
            answer = self.handler(client=client_address, data=data)

            debug(f'answer is "{answer}"')
            if answer is not None:
                debug(f'send an answer to {client_address}')
                connection.send(bytes(answer, encoding='utf-8'))
            connection.close()
            debug(f'connection from {client_address} closed')
        server_socket.close()

class CommunicationClient():
    logger = logging.getLogger('Comm client')

    def __init__(self, name:str, ip:str='127.0.0.1', port:int=8585):
        critical = CommunicationClient.logger.critical
        if not isinstance(ip, str):
            critical("init error. 'ip' is not 'str' type.")
            raise Exception("init error. 'ip' is not 'str' type.")
        self._ip = ip
        if not isinstance(port, int):
            critical("init error. 'port' is not 'int' type.")
            raise Exception("init error. 'port' is not 'int' type.")
        self._port = port
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    def send(self, message):
        error = CommunicationClient.logger.error
        answer = None
        try:
            sock = socket.create_connection((self._ip, self._port), 10)
            sock.sendall(bytes(message, encoding='utf-8'))
            #answer = sock.recv(1024)
            answer = clear_str(sock.recv(1024).decode('utf-8'))
        except:
            error(f'error connection to {self._ip}:{self.port}')
        finally:
            try:
                sock.close()
            except:
                pass
        return answer

    def send_with_name(self, message):
        return self.send(f'{self.name}:{message}')