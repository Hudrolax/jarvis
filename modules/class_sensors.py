import sys
sys.path.append('../')
import threading
from time import sleep
from modules.class_sonoff import Sonoff


class Sensors:
    def __init__(self, jarvis):
        self.jarvis = jarvis
        self.sonoff1 = Sonoff('sonoff1', '7950295', '192.168.18.103')
        self._update_thread = threading.Thread(target=self._update_thread_func, args=(), daemon=True)
        self._update_thread.start()
        self._ac_voltage_input = 0

    @property
    def ac_voltage_input(self):
        return self.sonoff1.voltage

    def _update_thread_func(self):
        while self.jarvis.runned:
            self.sonoff1.update_info()
            sleep(5)

if __name__ == '__main__':
    class TestJarvis:
        runned = True
    sens1 = Sensors(TestJarvis())
    sleep(1)
    print(sens1.sonoff1.voltage)