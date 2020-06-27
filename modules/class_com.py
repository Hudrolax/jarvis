import sys

sys.path.append('../')
from socket import *
import logging
import threading
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

class CommunicationServer:
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

    def __init__(self, ip:str, port):
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
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

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
            while True:
                data = connection.recv(1024)
                if not data:
                    break
                else:
                    data = data.decode()
                    debug(f"received data: {data}")
                    # << Оборачиваемая функция
                    answer = self.handler(client_address, data)
                    # >> Оборачиваемая функция
                    debug(f'answer is "{answer}"')
                    # connection.send(answer.encode('ascii'))
                    connection.sendall(answer.encode())
        except ConnectionResetError:
            self.logger.warning(f'Error with recieve data from {client_address}')
            return
        except UnicodeDecodeError:
            self.logger.warning(f'Error with decode data from {client_address}')
            return
        except TimeoutError:
            self.logger.warning(f'Time out recieve from {client_address}')
            return
        except AttributeError:
            self.logger.warning(f"Can't encode answer {answer}")
            return

        finally:
            pass
            # connection.close()
            # debug(f'connection from {client_address} closed')

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
                pass
                error(f"Can't bind {self.ip}:{self.port}")
            sleep(5)
        else:
            return None
        self.server_socket.listen(20)
        info(f'server "{self.name}" is started on {self.ip}:{self.port}')
        while self._started:
            try:
                connection, client_address = self.server_socket.accept()
            except Exception:
                debug(f'connection timeout')
                continue
            debug(f"new connection from {client_address}")
            handle_thread = threading.Thread(target=self.handler_wrapper, args=(connection, client_address), daemon=True)
            handle_thread.start()

        self.server_socket.close()

class CommunicationClient:
    logger = logging.getLogger('Comm client')

    def __init__(self, name:str, ip:str, port:int):
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
        self.connect()
        # self.sock.settimeout(5)

    @property
    def name(self):
        return self._name

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    def connect(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((self.ip, self.port))
        except OSError:
            _sleeptime = 10
            self.logger.error(f'connection error to {self._ip}:{self.port}. Sleep {_sleeptime} sec.')
            sleep(_sleeptime)

    def close(self):
        self.sock.close()

    def send(self, message):
        answer = 'none'
        attempt = 10
        while attempt > 0:
            try:
                self.logger.debug('try to send')
                self.sock.sendall(str.encode(message))
                self.logger.debug('try to get answer')
                answer = self.sock.recv(1024).decode()
                break
            except OSError:
                attempt -= 1
                self.logger.warning(f'send error to {self._ip}:{self.port}. Try to reconnect to server.')
                self.connect()

        return answer

    def send_with_name(self, message):
        return self.send(f'{self.name}:{message}')

if __name__ == '__main__':
    client = CommunicationClient('test', '192.168.18.3', 8586)
    client.logger.setLevel(logging.DEBUG)
    print(client.send('ping'))
    print(client.send('ping'))