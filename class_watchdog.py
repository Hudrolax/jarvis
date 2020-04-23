import serial


class CWatchDog:
    def __init__(self, port):
        self.port = port  # порт подключения вотчдога
        print('Try connect to WatchDog at port ' + self.port)
        self.serial = serial.Serial(self.port, 9600, timeout=1)  # change ACM number as found from ls /dev/tty/ACM*
        self.serial.flushInput()
        self.serial.flushOutput()
        self.serial.baudrate = 9600
        self.serial.timeout = 1
        self.serial.write_timeout = 1

    @staticmethod
    def send_to_serial(_s_port, s):
        try:
            _s_port.write(bytes(s, 'utf-8'))
        except:
            print('Write error to port ' + _s_port)

    def ping(self):
        CWatchDog.send_to_serial(self.serial, '~U')  # Отправка команды "я в норме" на вотчдог
