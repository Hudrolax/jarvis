from modules.class_rectangle import Rectangle
from time import sleep
import threading
import logging
from config import *

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

class Laser(Rectangle):
    logger = logging.getLogger('laser')
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class GameCorrdinate:
        def __init__(self, x, y, x_speed, y_speed):
            self.x = int(x)
            self.y = int(y)
            self.x_speed = int(x_speed)
            self.y_speed = int(y_speed)

        def __str__(self):
            return f'(x={self.x}, y={self.y}, x_speed={self.x_speed}, y_speed={self.y_speed})'

    def __init__(self, x_min:int=20, x_max:int=150, y_min:int=0, y_max:int=179):
        super().__init__(x_min, x_max, y_min, y_max)
        self._laser_on = False
        self._distance = 0
        self.parking_point = self.Point(92, 0)
        self._game_mode = False
        self._game_coords = []
        self._game_coords_loaded = False
        self.load_game_coordinates()
        self.game_runned = False
        self._game_thread = threading.Thread(target=self.game, args=(), daemon=True)
        self._game_thread.start()

    @property
    def laser_on(self):
        return self._laser_on

    @laser_on.setter
    def laser_on(self, val):
        if isinstance(val, bool):
            self._laser_on = val
        elif isinstance(val, int) or isinstance(val, float):
            self._laser_on = bool(val)
        elif isinstance(val, str):
            if val.lower() == 'on':
                self._laser_on = True
            elif val.lower() == 'off':
                self._laser_on = False
        else:
            self.logger.error(f'laser_on setter type error. Need bool, int, float or str, but got {type(val)}')

    @property
    def laser_state_str(self):
        if self._laser_on:
            return 'ON'
        else:
            return 'OFF'

    @property
    def laser_state_int(self):
        if self._laser_on:
            return 1
        else:
            return 0

    @property
    def game_coords(self):
        return self._game_coords

    @property
    def distance(self):
        return self._distance

    @distance.setter
    def distance(self, val):
        if isinstance(val, int) or isinstance(val, float):
            if val > 0:
                self._distance = val
        else:
            try:
                _val = int(val)
                if _val > 0:
                    self._distance = int(val)
            except TypeError:
                self.logger.warning(f'distance type error val={val} type is {type(val)}')

    @property
    def game_mode(self):
        return self._game_mode

    def rev_laser(self):
        self._laser_on = not self._laser_on
        self.logger.info(f'laser {self.laser_state_str}')


    def homing(self):
        self.logger.info('start homing')
        while self.game_runned:
            sleep(0.1)
        self.logger.info('start moving axis for homing')
        self.move_axis_to_coord(self.parking_point.x, self.parking_point.y, 2, 2)
        self.laser_on = False
        print(f'laser homed. Laser is {self.laser_on}')

    def rev_game_mode(self):
        self._game_mode = not self._game_mode
        if self._game_mode:
            self.logger.info('game mode ON')
        else:
            self.homing()
            self.logger.info('game mode OFF')

    def move_axis_to_coord(self, x, y, speed_x, speed_y):
        x = self.check_values(x, self._x_min, self._x_max)
        y = self.check_values(y, self._y_min, self._y_max)
        while (abs(self.x - x) >= speed_x or abs(self.y - y) >= speed_y):
            if self.x< x:
                self.x += speed_x
            elif self.x > x:
                self.x -= speed_x

            if self.y < y:
                self.y += speed_y
            elif self.y > y:
                self.y -= speed_y
            sleep(0.03)

    def move_axis(self, direction, speed_x, speed_y):
        if direction == 'up':
            self.y += speed_y
        elif direction == 'down':
            self.y -= speed_y
        elif direction == 'left':
            self.x += speed_x
        elif direction == 'right':
            self.x -= speed_x
        sleep(0.01)

    def load_game_coordinates(self):
        try:
            file = open(GAME_FILE, "r")
            lines = file.readlines()
            file.close()
        except FileNotFoundError:
            print('Not found')
        except IOError:
            print('Something else')

        for line in lines:
            if line[0].isdigit():
                line = line.replace('\n', '')
                line = line.replace(' ', '')
                coord_array = line.split(',')
                try:
                    self._game_coords.append(self.GameCorrdinate(coord_array[0], coord_array[1], coord_array[2], coord_array[3]))
                except IndexError:
                    self.logger.error(f'Wrong data format in file {GAME_FILE}: {line} (need format: <X, Y, x_speed, y_speed>)')
                    return
        self._game_coords_loaded = True

    def game(self):
        while True:
            if self.game_mode and self._game_coords_loaded:
                self.game_runned = True
                for coord in self._game_coords:
                    self.move_axis_to_coord(coord.x, coord.y, coord.x_speed, coord.y_speed)
                # self.logger.info('alive')
            else:
                self.game_runned = False
            sleep(0.001)

if __name__ == '__main__':
    rect = Laser()
    rect.load_game_coordinates()
    for coord in rect.game_coords:
        print(coord)
