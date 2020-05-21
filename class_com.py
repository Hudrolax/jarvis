from gfunctions import *
import socket
import logging
import threading

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s (%(levelname)s) %(asctime)s: %(message)s'
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO
#LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')


class CommunicationServer():
    def __init__(self, name:str='root', ip:str='127.0.0.1', port:int = 8585):
        if not isinstance(name, str):
            raise Exception("CommunicationServer init error. 'name' is not 'str' type.")
        self.name = name
        self.logger = logging.getLogger(f'Comm server {self.name}')

        if not isinstance(ip, str):
            self.logger.critical("init error. 'ip' is not 'str' type.")
            raise Exception("init error. 'ip' is not 'str' type.")
        if not isinstance(port, int):
            self.logger.critical("init error. 'port' is not 'int' type.")
            raise Exception("init error. 'port' is not 'int' type.")

        self._own_server_adress = (ip, port)
        self._started = False
        self.thread = threading.Thread(target=self._tcp_server, args=(), daemon=True)

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
        self.thread.start()

    def stop(self):
        self._started = False

    def handler(self, client, data):
        #self.logger.debug('call handler')
        return 'None'

    def _tcp_server(self): # hendler take client:str and data:str parameters
        debug = self.logger.debug
        info = self.logger.info
        server_socket = socket.socket()
        server_socket.bind(self._own_server_adress)
        server_socket.listen(1)
        info('server is started')
        while self._started:
            connection, client_address = server_socket.accept()
            debug(f"new connection from {client_address}")
            data = clear_str(connection.recv(1024).decode("utf-8"))
            self.logger.debug(f"received data: {data}")
            # отправляем данные обработчику и получает ответ
            answer = self.handler(client=client_address, data=data)

            debug(f'answer is "{answer}"')
            if answer is not None:
                debug(f'send an answer to {client_address}')
                connection.send(bytes(answer, encoding='utf-8'))
            connection.close()
            debug(f'connection from {client_address} closed')

class CommunicationClient():
    def __init__(self, name:str, ip:str='127.0.0.1', port:int=8585):
        self.logger = logging.getLogger('Comm client')
        if not isinstance(ip, str):
            self.logger.critical("init error. 'ip' is not 'str' type.")
            raise Exception("init error. 'ip' is not 'str' type.")
        self._ip = ip
        if not isinstance(port, int):
            self.logger.critical("init error. 'port' is not 'int' type.")
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
        answer = None
        try:
            sock = socket.create_connection((self._ip, self._port), 10)
            sock.sendall(bytes(message, encoding='utf-8'))
            #answer = sock.recv(1024)
            answer = clear_str(sock.recv(1024).decode('utf-8'))
        except:
            self.logger.error(f'error connection to {self._ip}')
        finally:
            try:
                sock.close()
            except:
                pass
        return answer

    def send_with_name(self, message):
        return self.send(f'{self.name}:{message}')