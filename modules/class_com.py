from .gfunctions import *
import socket
import logging
import threading
from config import *
from time import sleep

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

    @staticmethod
    def set_debug():
        CommunicationServer.logger.setLevel(logging.DEBUG)
        print(f'set DEBUG level in {CommunicationServer.logger.name} logger')

    @staticmethod
    def set_warning():
        CommunicationServer.logger.setLevel(logging.WARNING)
        print(f'set WARNING level in {CommunicationServer.logger.name} logger')

    @staticmethod
    def set_info():
        CommunicationServer.logger.setLevel(logging.INFO)
        print(f'set INFO level in {CommunicationServer.logger.name} logger')

    def __init__(self, ip:str=SATELLITE_IP, port:int = SATELLITE_PORT):
        critical = CommunicationServer.logger.critical
        self._name = 'class_com'

        if not isinstance(ip, str):
            critical("init error. 'ip' is not 'str' type.")
            raise Exception("init error. 'ip' is not 'str' type.")
        if not isinstance(port, int):
            critical("init error. 'port' is not 'int' type.")
            raise Exception("init error. 'port' is not 'int' type.")

        self._own_server_adress = (ip, port)
        self._started = False
        self._thread = threading.Thread(target=self._tcp_server, args=(), daemon=True)
        self.server_socket = socket.socket()

    @property
    def name(self):
        return self._name

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
        self.server_socket.close()

    def handler_wrapper(self, connection, client_address):
        debug = self.logger.debug
        try:
            data = clear_str(connection.recv(1024).decode("utf-8"))

            logging.debug(f"received data: {data}")
            # << Оборачиваемая функция
            answer = self.handler(client_address, data)
            # >> Оборачиваемая функция

            debug(f'answer is "{answer}"')
            if answer is not None:
                debug(f'send an answer to {client_address}')
                connection.sendall(bytes(answer, encoding='utf-8'))
        except ConnectionResetError:
            self.logger.error(f'Error with recieve data from {client_address}')
            return
        except UnicodeDecodeError:
            self.logger.error(f'Error with decode UTF-8 data from {client_address}')
            return
        finally:
            connection.close()
            debug(f'connection from {client_address} closed')

    def handler(self, client_address, data):
        # client_address - адрес клиента
        # data - очищенные данные - только строка

        # <<обработчик данных
        answer = 'none'
        pass
        return answer
        # >>

    def _tcp_server(self): # hendler take client:str and data:str parameters
        debug = self.logger.debug
        info = self.logger.info
        error = self.logger.error
        while self._started:
            try:
                self.server_socket.bind(self._own_server_adress)
                break
            except:
                try:
                    self.server_socket.close()
                except:
                    pass
                error(f"Can't bind {self.ip}:{self.port}")
                Runned.runned = False
            sleep(1)
        else:
            return None
        self.server_socket.listen(1)
        info(f'server "{self.name}" is started on {self.ip}:{self.port}')
        while self._started:
            connection, client_address = self.server_socket.accept()
            debug(f"new connection from {client_address}")
            handle_thread = threading.Thread(target=self.handler_wrapper, args=(connection, client_address), daemon=True)
            handle_thread.start()

        self.server_socket.close()

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