import keyboard
import logging
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

class KeyBoardHook:
    logger = logging.getLogger('keyboard_hook')

    # При создании объекта хука в него помещается очередь, в которую будет помещаться нажатая клавиша
    def __init__(self, laser_server, queue):
        self.queue = queue
        self._laser_server = laser_server
        keyboard.hook(self.pressed_keys)
        keyboard.add_hotkey('ctrl+shift+h', self.rev_hook_state)
        self._hook_on = False
        print('Keyboard hook is init. Translate is OFF.')
        print('Press "ctrl+shift+h" key to translate ON/OFF')

    @property
    def hook_on(self):
        return self._hook_on

    @hook_on.setter
    def hook_on(self, val):
        if isinstance(val, bool):
            self._hook_on = val
        else:
            raise TypeError(f'hook_on type error. Need bool but get {type(val)}')

    @property
    def laser_server(self):
        return self._laser_server

    def rev_hook_state(self):
        self._hook_on = not self._hook_on
        if self._hook_on:
            self.laser_server.laser.translate_data_to_laser = True
            self.logger.info('keyboard hook is ON')
        else:
            self.laser_server.laser.translate_data_to_laser = False
            self.logger.info('keyboard hook is OFF')

    def translate(self, key):
        self.queue.put(key)

    def pressed_keys(self, event):
        if self._hook_on:
            if event.event_type == 'down':
                self.translate(event.name)

class DriveKayboardHook(KeyBoardHook):
    def __init__(self):
        super().__init__(None)
        self.up = False
        self.down = False
        self.left = False
        self.right = False

    def pressed_keys(self, event):
        if self._hook_on:
            _pressed = False
            if event.event_type == 'down':
                _pressed = True

            if event.name == 'up':
                self.up = _pressed
            elif event.name == 'down':
                self.down = _pressed
            elif event.name == 'left':
                self.left = _pressed
            elif event.name == 'right':
                self.right = _pressed
            else:
                if _pressed:
                    self.translate(event.name)