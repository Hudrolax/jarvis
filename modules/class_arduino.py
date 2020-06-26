from datetime import datetime
from time import sleep
import serial.tools.list_ports as lp
from . import gfunctions as gf
from .gfunctions import JPrint
jprint = JPrint.jprint
from .class_pins import Pins
import serial
import logging

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s (%(levelname)s) %(asctime)s: %(message)s'
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')

class Arduino(JPrint):
    logger = logging.getLogger('Arduino')
    logger.setLevel(LOG_LEVEL)

    def __init__(self, config_path: str, pinstate_file: str, not_important_words: str):
        self._name = 'arduino'
        self.port = None
        self.initialized = False
        self.pins = []
        self.config_path = config_path
        self.pinstate_file = pinstate_file
        self._dc_val_array = [27 for i in range(20)]
        self._dc_value = 27
        self._dc_low_alert_sended = False
        self._dc_voltage_in_percent = 100
        self._ac_exist = True
        self._ac_alert_sended = False
        self._ac_non_exist_start_timer = datetime.now()
        self.OutDoorLightPin = 0
        self.LastSetStateOutDoorLight = None
        self.__not_important_words = not_important_words

    @property
    def name(self):
        return self._name

    @property
    def ac_alert_sended(self):
        return self._ac_alert_sended

    @ac_alert_sended.setter
    def ac_alert_sended(self, val):
        if isinstance(val, bool):
            self._ac_alert_sended = val
        else:
            TypeError(f'Arduino exaption: ac_alert_sended unexpected {type(val)}, expected "bool"')

    @property
    def dc_voltage_in_percent(self):
        return self._dc_voltage_in_percent

    @property
    def dc_low_alert_sended(self):
        return self._dc_low_alert_sended

    @dc_low_alert_sended.setter
    def dc_low_alert_sended(self, val):
        if isinstance(val, bool):
            self._dc_low_alert_sended = val
        else:
            TypeError(f'Arduino exaption: dc_low_alert_sended unexpected {type(val)}, expected "bool"')

    @property
    def dc_value(self):
        return self._dc_value

    @dc_value.setter
    def dc_value(self, val):
        if isinstance(val, int) or isinstance(val, float):
            self._dc_value = val
        else:
            TypeError(f'Arduino exaption: dc_value unexpected {type(val)}, expected "int" or "float"')

    @staticmethod
    def set_info():
        Arduino.logger.setLevel(logging.INFO)
        jprint('set INFO level in Arduino logger')

    @staticmethod
    def set_debug():
        Arduino.logger.setLevel(logging.DEBUG)
        jprint('set DEBUG level in Arduino logger')

    @staticmethod
    def set_warning():
        Arduino.logger.setLevel(logging.WARNING)
        jprint('set WARNING level in Arduino logger')

    def find_pin(self, __pin):
        for p in self.pins:
            if str(type(__pin)) == "<class 'str'>":
                __pin = __pin.lower()
                if p.name.lower() == __pin or str(p.num) == __pin or p.description.lower() == __pin:
                    return p
            elif str(type(__pin)) == "<class 'int'>":
                if p.num == __pin:
                    return p
        return None

    def set_pin(self, _pin, __state):
        if str(type(_pin)) == "<class 'list'>":
            self.jprint("Error (set_pin): _pin is <class 'list'>")
            return None
        if __state:
            __state = 1
        elif not __state:
            __state = 0
        if str(type(_pin)) == "<class 'int'>":
            p = self.find_pin(_pin)
        elif str(type(_pin)) == "<class 'str'>":
            _pin = int(_pin)
            p = self.find_pin(_pin)
        else:
            p = _pin
            _pin = _pin.num
        try:
            p.prevstate = p.state
        except:
            self.jprint(p)

        answer = None
        if __state == 1:
            while answer != 3001 or answer is None:
                answer = self.write_to_port('P', _pin, __state)
                # self.jprint(f'set_pin get answer {answer}')
        elif __state == 0:
            while answer != 3000 or answer is None:
                answer = self.write_to_port('P', _pin, __state)
                # self.jprint(f'set_pin get answer {answer}')
        else:
            while answer != 3001 and answer != 3000 or answer is None:
                answer = self.write_to_port('P', _pin, __state)
                # self.jprint(f'set_pin get answer {answer}')

        if answer is not None:
            p.last_rev_time = datetime.now()
            if answer == 3001:
                p.state = True
            elif answer == 3000:
                p.state = False
            self.write_pinstate(p)
            return p.state
        else:
            return None

    def check_input_pins(self, allpins=False):
        for p in self.pins:
            if not p.output or allpins:
                # if True:
                p.prevstate = p.state
                if self.write_to_port('S', p.num, 0) == 2001:
                    p.state = True
                else:
                    p.state = False
                if allpins:
                    p.prevstate = p.state
                self.pin_reaction(p)

        val = self.write_to_port('A', 1, 0)
        voltage_now = round(gf.map_func(val, 0, 1023, 0, 40.1), 2)
        self._dc_val_array.pop(0)
        self._dc_val_array.append(voltage_now)
        self._dc_value = round(gf.array_ma(self._dc_val_array), 2)
        percent = round(gf.map_func(self._dc_value, 22, 27, 0, 100), 0)
        if percent > 100:
            percent = 100
        elif percent < 0:
            percent = 0
        self._dc_voltage_in_percent = percent
        if self._dc_voltage_in_percent == 100:
            self._dc_low_alert_sended = False

        val = self.write_to_port('A', 0, 0)
        if val > 600:
            if not self._ac_exist:
                Arduino.logger.debug('Включилось напряжение на входе')
                self._ac_exist = True
        else:
            if self._ac_exist:
                Arduino.logger.debug('Отключилось напряжение на входе')
                self._ac_non_exist_start_timer = datetime.now()
                self._ac_exist = False

    @property
    def ac_exist(self):
        return self._ac_exist

    @property
    def ac_exist_str(self, lang = 'ru'):
        if self._ac_exist:
            if lang == 'ru':
                return 'есть'
            elif lang == 'eng':
                return 'yes'
        else:
            if lang == 'ru':
                return 'НЕТ'
            elif lang == 'eng':
                return 'NO'

    def time_without_ac(self, in_str:bool = False):
        if in_str:
            return gf.difference_between_date(self._ac_non_exist_start_timer, datetime.now())
        else:
            return (datetime.now() - self._ac_non_exist_start_timer).total_seconds()

    def pin_reaction(self, p):
        # p - swich (S-pin)
        # b - bind (DG-pin)
        if p.state != p.prevstate:
            for b in p.binds:
                if not p.blocked and not b.blocked:
                    self.jprint(f'im set pin {b.description} to {p.state} by pin_reaction in {datetime.now().strftime("%X")}')
                    self.set_pin(b.num, p.state)
                    p.last_rev_time = datetime.now()
                    b.last_rev_time = datetime.now()

    def write_to_port(self, cmd, val1, val2):
        answer = None
        try:
            self.port.write((222).to_bytes(1, 'big'))  # header byte
            self.port.write((ord(cmd)).to_bytes(1, "big"))
            self.port.write((int(val1)).to_bytes(2, "big"))
            self.port.write((int(val2)).to_bytes(1, "big"))
            self.port.flush()
            sleep(0.001)
            # read answer
            answer = int.from_bytes(self.port.read(2), 'big')
        except:
            self.initialized = False
        return answer

    def write_pinstate(self, _pin):
        try:
            f = open(self.pinstate_file, 'w')
            for p in self.pins:
                f.write(f'{p.num} {p.state} {p.blocked}\n')
            f.close()
        except:
            self.jprint('error save pinstate')

    def load_pinstate(self):
        try:
            f = open(self.pinstate_file, 'r')
            lines = f.read().split('\n')
            f.close()
            for line in lines:
                s = line.split(' ')
                for p in self.pins:
                    if str(p.num) == s[0]:
                        if p.output:
                            if s[1].lower() == 'true':
                                p.state = True
                            else:
                                p.state = False
                            self.set_pin(p, p.state)
                        try:
                            if s[2].lower() == 'true':
                                p.blocked = True
                            else:
                                p.blocked = False
                        except:
                            pass
            self.jprint('pinstate is loaded')
        except:
            self.jprint('error load pinstate')

    def check_initialization(self):
        a = self.write_to_port('I', 666, 1)
        if a == 666:
            self.initialized = True
            self.check_input_pins(True)

    def prepare_serial(self):
        try:
            self.port.reset_output_buffer()
            self.port.reset_input_buffer()
            self.port.baudrate = 57600
            self.port.timeout = 1
            self.port.write_timeout = 1
            return True
        except:
            self.jprint("Can't load proporties to COM port")
            return False

    def _try_to_init(self):
        if self.prepare_serial():
            sleep(3)
            self.check_initialization()
            if self.initialized:
                return True
            return False

    def initialize(self):
        self.port = None
        ports = list(lp.comports())
        for p in ports:
            comport = p.device
            self.jprint('Try to find Arduino in ' + comport)
            self.port = serial.Serial(comport, 57600, timeout=1)
            if self._try_to_init(): break

        if not self.initialized:
            self.jprint('I have not found the Arduino...')
            self.jprint("Sorry, but i can't work whithout Arduino subcontroller :(")
            Arduino.logger.debug("I'm have to try to find it after one second pause")
            Arduino.logger.debug("can't load Arduino controller")
        else:
            self.jprint(f'Arduino is initialized on port {self.port.name}')
            self.load_pinstate()

    def load_config(self, bot):
        __answer = None
        self.pins = []
        try:
            with open(self.config_path) as f:
                file_text = f.read()
        except:
            raise RuntimeError("Can't load config")

        array = file_text.split('\n')
        for a in array:
            line = a.split(' ')
            if line[0] == 'pin':
                _num = line[1]
                _name = line[2]
                _output = False
                if line[3] == 'output':
                    _output = True
                _description = line[4]
                _BCOD = int(line[5])

                _ct = []
                if len(line) > 5:
                    for i in range(6, len(line)):
                        _ct.append(line[i])
                if self.find_pin(_num) not in self.pins:
                    self.pins.append(Pins(_output, int(_num), _BCOD, _name, _description, _ct))
            elif line[0] == 'bind':
                _pin = self.find_pin(line[1])
                if _pin is not None:
                    for i in range(2, len(line)):
                        _pin2 = self.find_pin(line[i])
                        if _pin2 is not None:
                            if _pin2 not in _pin.binds:
                                _pin.binds.append(_pin2)
            elif line[0] == 'telegram_user':
                bot.add_user(line[1], line[2], int(line[3]))

            __answer = 'config loaded!'
            lightpin = self.find_by_auction('свет на улице')
            if str(type(lightpin)) != "<class 'list'>" and lightpin is not None:
                self.OutDoorLightPin = self.find_by_auction('свет на улице')
            else:
                pass
                # self.jprint('Не могу подобрать пин уличного освещения!')
        self.jprint(__answer)
        return __answer

    def save_config(self, bot):
        try:
            f = open(self.config_path, 'w')
            f.write(
                '# pin line: pin <arduino pin number> <name> <input/output> <description> <blocked> convertible terms' + '\n')
            f.write('# Inputs:' + '\n')
            for p in self.pins:
                if not p.output:
                    ct = ''
                    for c in p.convertible_terms:
                        ct += f' {c}'
                    f.write(f'pin {p.num} {p.name} input {p.description} {p.BCOD}{ct}' + '\n')
            f.write('\n')
            f.write('# Outputs:' + '\n')
            for p in self.pins:
                if p.output:
                    ct = ''
                    for c in p.convertible_terms:
                        ct += f' {c}'
                    f.write(f'pin {p.num} {p.name} output {p.description} {p.BCOD}{ct}' + '\n')
            f.write('\n')
            f.write('# Bind line: bind <arduino pin number / name> <name> <arduino pin number / name> <...>' + '\n')
            for p in self.pins:
                if len(p.binds) > 0:
                    bindstr = ''
                    for b in p.binds:
                        bindstr += ' ' + str(b.num)
                    f.write(f'bind {p.num}' + bindstr + '\n')
            f.write('\n')
            f.write('# Telegram user line: telegram_user <name> <ID>' + '\n')
            for u in bot.get_users():
                f.write(f'telegram_user {u.name} {u.ID}' + '\n')

            answer = None
        except:
            answer = 'error save config'
        return answer

    def find_by_auction(self, cmd, allpins=False):
        if not isinstance(cmd, list):
            cmd = str(cmd)
            _wordlist = cmd.split(' ')
        else:
            _wordlist = cmd
        wordlist = []
        for w in _wordlist:
            if w not in self.__not_important_words:
                wordlist.append(w)
        _pin_auction = []
        for p in self.pins:
            if p.output or allpins:  # добавляем выходы в аукцион
                ct_all = []
                for c in p.convertible_terms:
                    ct_all.append(c)
                ct_all.append(p.description)
                ct_all.append(str(p.num))
                ct_all.append(p.name.lower())
                _pin_auction.append([p.num, ct_all, 0])

        for word in wordlist:
            for _pa in _pin_auction:
                Arduino.logger.debug(f'count points for {_pa[0]}')
                for ct in _pa[1]:
                    if ct.lower() == word:
                        _pa[2] += 2
                        Arduino.logger.debug(f'word = {word} 2 points')
                    elif ct.lower().find(word) > -1:
                        _pa[2] += 1
                        Arduino.logger.debug(f'word find {word} 1 point')

        _max_includes = 0
        _winners = []
        for _pa in _pin_auction:
            if _pa[2] > _max_includes:
                _max_includes = _pa[2]

        if _max_includes > 0:
            for _pa in _pin_auction:
                if _pa[2] == _max_includes:
                    _winners.append(self.find_pin(_pa[0]))

        if len(_winners) == 1:
            Arduino.logger.debug(f'winner is {_winners[0].description}')
            Arduino.logger.debug(f'winner get {_max_includes} points')
            return _winners[0]
        elif len(_winners) > 1:
            Arduino.logger.debug('_winners more than one')
            Arduino.logger.debug(f'its get {_max_includes} points')
            return _winners
        else:
            Arduino.logger.debug('winner not found')
            Arduino.logger.debug('winner not found')
            return None
