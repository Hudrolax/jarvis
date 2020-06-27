import requests
import logging
from time import sleep

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s (%(levelname)s) %(asctime)s: %(message)s'
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO
#LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')

class Sonoff:
    logger = logging.getLogger('sonoff')

    @staticmethod
    def set_debug():
        Sonoff.logger.setLevel(logging.DEBUG)
        print(f'set DEBUG level in {Sonoff.logger.name} logger')

    @staticmethod
    def set_warning():
        Sonoff.logger.setLevel(logging.WARNING)
        print(f'set WARNING level in {Sonoff.logger.name} logger')

    @staticmethod
    def set_info():
        Sonoff.logger.setLevel(logging.INFO)
        print(f'set INFO level in {Sonoff.logger.name} logger')

    def __init__(self, name, password:str, ip, port:int = 80):
        self.name = name
        self.ip = ip
        self.port = port
        self.password = password
        self.relay_state = False
        self.voltage = 0
        self.currency = 0
        self.power = 0

    @property
    def rel_str(self):
        if self.relay_state:
            return 'on'
        else:
            return 'off'

    def update_info(self):
        try:
            self.logger.debug(f'try to request to http://{self.ip}:{self.port}/get_control?info=1&auth={self.password}')
            content = requests.get(f'http://{self.ip}:{self.port}/get_control?info=1&auth={self.password}').content.decode()
        except:
            self.logger.error(f'request error to http://{self.ip}:{self.port}/get_control?info=1&auth={self.password}')
            sleep(10)
            return

        try:
            data = content.split(',')
            for element in data:
                element = element.strip(' ')
                el_data = element.split(' ')
                if el_data[0] == 'RelayStatus:':
                    if el_data[1] == 'On':
                        self.relay_state = True
                    else:
                        self.relay_state = False
                elif el_data[0] == 'Voltage:':
                    self.voltage = float(el_data[1])
                elif el_data[0] == 'Currency:':
                    self.currency = float(el_data[1])
                elif el_data[0] == 'Power:':
                    self.power = float(el_data[1])
        except:
            self.logger.error('sonoff answer pasre error')
            sleep(10)
            return


    def __str__(self):
        return f'({self.name}, rel {self.rel_str}, voltage {self.voltage}, current {self.currency}, power {self.power})'

if __name__ == '__main__':
    son1 = Sonoff('son1', '7950295', '192.168.18.102')
    son1.update_info()
    print(son1)