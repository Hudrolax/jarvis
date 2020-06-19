from modules.class_rectangle import Rectangle
from time import sleep
import threading
import logging
from config import *
from datetime import datetime, timedelta
import random

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s (%(levelname)s) %(asctime)s: %(message)s'
# LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.WARNING
# LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL,
                        datefmt='%d.%m.%y %H:%M:%S')
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')

class Laser(Rectangle):
    logger = logging.getLogger('laser')
    logger.setLevel(logging.WARNING)

    @staticmethod
    def set_debug():
        Laser.logger.setLevel(logging.WARNING)
        print(f'set DEBUG level in {Laser.logger.name} logger')

    @staticmethod
    def set_warning():
        Laser.logger.setLevel(logging.WARNING)
        print(f'set WARNING level in {Laser.logger.name} logger')

    @staticmethod
    def set_info():
        Laser.logger.setLevel(logging.INFO)
        print(f'set INFO level in {Laser.logger.name} logger')

    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class GameCoordinate:
        def __init__(self, x, y, x_speed, y_speed):
            self.x = int(x)
            self.y = int(y)
            self.x_speed = int(x_speed)
            self.y_speed = int(y_speed)

        def __str__(self):
            return f'(x={self.x}, y={self.y}, x_speed={self.x_speed}, y_speed={self.y_speed})'

    def __init__(self, laser_server, x_min:int=20, x_max:int=150, y_min:int=0, y_max:int=179):
        self.parking_point = self.Point(92, 0)
        super().__init__(x_min, x_max, y_min, y_max, self.parking_point.x, self.parking_point.y)
        self._name = 'laser'
        self.laser_server = laser_server
        self._laser = False
        self._game_mode = False
        self._game_coords = []
        self._game_coords_loaded = False
        self.game_runned = False
        self.games_amount = 2
        self._game_time_range_sec = [30, 120]
        self._game_stop_time = datetime.now()
        self._game_thread = threading.Thread(target=self.game, args=(), daemon=True)
        self._game_thread.start()

    @property
    def name(self):
        return self._name

    @property
    def game_time_range_sec(self):
        return [self._game_time_range_sec[0], self._game_time_range_sec[1]]

    @game_time_range_sec.setter
    def game_time_range_sec(self, val):
        if isinstance(val, list) or isinstance(val, tuple):
            self._game_time_range_sec[0] = val[0]
            self._game_time_range_sec[1] = val[1]

    @property
    def laser(self):
        return self._laser

    def laser_on(self):
        self._laser = True
        self.add_translate_command()

    def laser_off(self):
        self._laser = False
        self.add_translate_command()

    @property
    def laser_state_str(self):
        if self._laser:
            return 'ON'
        else:
            return 'OFF'

    @property
    def laser_state_int(self):
        if self._laser:
            return 1
        else:
            return 0

    @property
    def game_coords(self):
        return self._game_coords

    @property
    def game_mode(self):
        return self._game_mode

    @game_mode.setter
    def game_mode(self, val):
        if isinstance(val, bool):
            self._game_mode = val
        else:
            raise TypeError('game_mode type error')

    def rev_laser(self):
        self._laser = not self._laser
        self.add_translate_command()
        self.logger.info(f'laser {self.laser_state_str}')


    def homing(self):
        self.logger.debug('start homing')
        self.laser_off()
        self._game_mode = False
        while self.game_runned:
            sleep(0.1)
        self.logger.debug('start moving axis for homing')
        self.move_axis_to_coord(self.parking_point.x, self.parking_point.y, 2, 2)
        print(f'laser homed. Laser is {self.laser}')

    def rev_game_mode(self):
        self._game_mode = not self._game_mode
        if self._game_mode:
            self.start_game()
        else:
            self.stop_game()

    def start_game(self):
        self.game_mode = True
        _game_time = random.randint(self.game_time_range_sec[0], self.game_time_range_sec[1])
        self.logger.info(f'Game time is {_game_time} sec.')
        self._game_stop_time = datetime.now() + timedelta(seconds=_game_time)
        self.load_game_coordinates()
        self.laser_on()
        self.logger.info('game mode ON')
        return _game_time

    def stop_game(self):
        self.game_mode = False
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
            self.add_translate_command()
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
        self.add_translate_command()
        sleep(0.01)

    def add_translate_command(self):
        self.laser_server.translate_queue.put((self.x, self.y, self.laser_state_int))

    def load_game_coordinates(self):
        self._game_coords = []
        for i in range(0, self.games_amount):
            new_coord_array = []
            try:
                file = open(f'{GAME_FILE_PATH}{GAME_FILE_NAME}{i}{GAME_FILE_EXTENSION}', "r")
                lines = file.readlines()
                file.close()
            except FileNotFoundError:
                raise FileNotFoundError(f'file {GAME_FILE_PATH}{GAME_FILE_NAME}i{GAME_FILE_EXTENSION} not found')
            except IOError:
                raise IOError('IOError')

            for line in lines:
                if line[0].isdigit():
                    line = line.replace('\n', '')
                    line = line.replace(' ', '')
                    _coord_array = line.split(',')
                    try:
                        new_coord_array.append(self.GameCoordinate(_coord_array[0], _coord_array[1], _coord_array[2], _coord_array[3]))
                    except IndexError:
                        self.logger.error(f'Wrong data format in file {GAME_FILE_PATH}{GAME_FILE_NAME}{i}{GAME_FILE_EXTENSION}: {line} (need format: <X, Y, x_speed, y_speed>)')
                        raise IndexError()
            self.logger.info(f'game from {GAME_FILE_PATH}{GAME_FILE_NAME}{i}{GAME_FILE_EXTENSION} loaded')
            self._game_coords.append(new_coord_array)
        self._game_coords_loaded = True

    def game(self):
        while True:
            if self.game_mode and self._game_coords_loaded:
                self.game_runned = True
                _game_number = random.randint(0, self.games_amount-1)
                self.logger.debug(f'play game number {_game_number}')
                coord_array = self._game_coords[_game_number]
                for coord in coord_array:
                    if not self.game_mode:
                        self.game_runned = False
                        break
                    self.move_axis_to_coord(coord.x, coord.y, coord.x_speed, coord.y_speed)
                    self.logger.info(f'GAME: move to {coord.x}, {coord.y} speed {coord.x_speed}, {coord.y_speed}')
                    if self.logger.level == logging.DEBUG:
                        print('sleep 1 sec (because DEBUG level)')
                        sleep(1)
                if datetime.now() > self._game_stop_time:
                    self.logger.info('Stop game mode by timer.')
                    self.game_mode = False
                    self.stop_game()
            else:
                self.game_runned = False
            sleep(0.001)

if __name__ == '__main__':
    rect = Laser()
    rect.load_game_coordinates()
    for coord in rect.game_coords:
        print(coord)
