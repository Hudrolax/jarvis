import sys
sys.path.append('../')
import threading
from time import sleep
from modules.class_sonoff import Sonoff
from datetime import datetime

class ArduinoSensor:
    def __init__(self):
        self.temp_outside = 0
        self.moving_sensor = False
        self._last_moving_sensor_time = datetime.now()
        self._guard_mode = False
        self.button_pressed = False
        self._start_press_button = False
        self._button_pressed_time = datetime.now()
        self.light_sensor_outside = 0

    @property
    def guard_mode(self):
        return self._guard_mode

    @guard_mode.setter
    def guard_mode(self, val):
        if isinstance(val, bool):
            self._guard_mode = val
        else:
            raise TypeError(f'ArduinoSensor:guard_mode type error. Need bool my got {type(val)}')

    def last_move_time(self):
        return self._last_moving_sensor_time

    def last_move_time_str(self):
        return datetime.strftime(datetime.now(),"%d.%m.%y %H:%M:%S")

    def set_moving_sensor(self, val):
        if isinstance(val, bool):
            self.moving_sensor = val
            if val:
                self._last_moving_sensor_time = datetime.now()
        else:
            raise TypeError(f'set_moving_sensor type error')

    def guard_mode_to_send(self):
        if self.guard_mode:
            return 'g'
        else:
            return 'n'

    def on_guard_mode(self):
        self.guard_mode = True
        return "Охранный режим включен."

    def off_guard_mode(self):
        self.guard_mode = True
        return "Охранный режим отключен."

    def button_handler(self, button_pressed:bool):
        if button_pressed:
            if not self._start_press_button:
                self._start_press_button = True
                self._button_pressed_time = datetime.now()
            else:
                if (datetime.now() - self._button_pressed_time).total_seconds() >= 3:
                    self.guard_mode = not self.guard_mode
                    self._button_pressed_time = datetime.now()

        else:
            self._start_press_button = False

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
            sleep(1)

if __name__ == '__main__':
    print(datetime.strftime(datetime.now(),"%d.%m.%y %H:%M:%S"))