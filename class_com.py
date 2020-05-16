from gfunctions import *
import socket
import logging
import threading

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s - %(levelname)s - %(message)s'
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL)
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)


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
        self.logger.info('call handler')
        pass

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
            answer = self.handler(client=client_address, data=data)
            debug(f'answer is {answer}')
            if answer is not None:
                debug(f'send an answer to {client_address}')
                connection.send(bytes(answer, encoding='UTF-8'))
            connection.close()

class CommunicationClient(GFunctions):
    def __init__(self, ip:str='127.0.0.1', port:int=8585):
        self.logger = logging.getLogger('Comm client')
        if not isinstance(ip, str):
            self.logger.critical("init error. 'ip' is not 'str' type.")
            raise Exception("init error. 'ip' is not 'str' type.")
        self._ip = ip
        if not isinstance(port, int):
            self.logger.critical("init error. 'port' is not 'int' type.")
            raise Exception("init error. 'port' is not 'int' type.")
        self._port = port

    def send(self, message):
        data = None
        try:
            sock = socket.create_connection((self._ip, self._port), 10)
            sock.sendall(bytes(message, encoding='UTF-8'))
            data = self.clear_str(sock.recv(1024).decode("utf-8"))
        except:
            self.logger.error(f'error connection to {self._ip}')
        finally:
            try:
                sock.close()
            except:
                pass
        return data


if __name__ == '__main__':
    from time import sleep
    class Serverx(CommunicationServer):
        def handler(self, client, data):
            return(f"принял сообщение от клиента {client}: {data}")

    server = Serverx(name='Serverx')
    server.start()

    client = CommunicationClient()
    answer = client.send('проверка')
    sleep(1)
    print(f'answer is: {answer}')
    server.stop()