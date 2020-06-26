import sys
from time import sleep
sys.path.append('../')

from modules.class_com import CommunicationServer

class TestTCPServer(CommunicationServer):

    def handler(self, client_address, data):
        # client_address - адрес клиента
        # data - очищенные данные - только строка
        return 'отправляем эту строку клиенту в ответ на любые данные'

if __name__ == '__main__':
    server = TestTCPServer('root', '192.168.18.3', 8586)
    server.start()
    while True:
        sleep(1)