import serial
from gfunctions import JPrint
import threading

class CWatchDog(JPrint):
    def __init__(self, port):
        self.port = port  # порт подключения вотчдога
        self.jprint('Try connect to WatchDog at port ' + self.port)
        self._serial = serial.Serial(self.port, 9600, timeout=1)  # change ACM number as found from ls /dev/tty/ACM*
        self._serial.flushInput()
        self._serial.flushOutput()
        self._serial.baudrate = 9600
        self._serial.timeout = 1
        self._serial.write_timeout = 1
        self._pinging_started = False
        self._watchdog_thread = threading.Thread(target=self._ping, args=(), daemon=True)

    @staticmethod
    def _send_to_serial(_s_port, s):
        try:
            _s_port.write(bytes(s, 'utf-8'))
        except:
            CWatchDog.jprint('Write error to port ' + _s_port)

    def _ping(self):
        from time import sleep
        while self._pinging_started:
            CWatchDog._send_to_serial(self._serial, '~U')  # Отправка команды "я в норме" на вотчдог
            sleep(3)

    def start_ping(self):
         # Start watchdog thread
        if not self._pinging_started:
            self._pinging_started = True
            self._watchdog_thread.start()
            return True
        else:
            return False

    def stop_ping(self):
        self._pinging_started = False