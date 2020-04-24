from datetime import datetime
from time import sleep
import serial
import gfunctions as gf
from class_pins import Pins
import telegram_bot


class Arduino:
    def __init__(self, config_path: str, pinstate_file: str, not_important_words: str):
        self.port = ''
        self.initialized = False
        self.pins = []
        self.config_path = config_path
        self.pinstate_file = pinstate_file
        self.DCVolArray = [27 for i in range(20)]
        self.DCVol = 27
        self.DCVolLowAlertSended = False
        self.DCVoltageInPercent = 100
        self.DCCheckTimer = 0
        self.ACCExist = True
        self.ACAlertSended = False
        self.ACNonExistStartTimer = datetime.now()
        self.OutDoorLightPin = 0
        self.LastSetStateOutDoorLight = None
        self.__not_important_words = not_important_words

    def pin(self, __pin):
        for p in self.pins:
            if str(type(__pin)) == "<class 'str'>":
                __pin = __pin.lower()
                if p.name.lower() == __pin or str(p.num) == __pin or p.description.lower() == __pin:
                    return p
            elif str(type(__pin)) == "<class 'int'>":
                if p.num == __pin:
                    return p
        raise RuntimeError(f'Не найден пин {__pin}')

    def set_pin(self, _pin, __state):
        if str(type(_pin)) == "<class 'list'>":
            print("Error (set_pin): _pin is <class 'list'>")
            return None
        if __state:
            __state = 1
        elif not __state:
            __state = 0
        if str(type(_pin)) == "<class 'int'>":
            p = self.pin(_pin)
        elif str(type(_pin)) == "<class 'str'>":
            _pin = int(_pin)
            p = self.pin(_pin)
        else:
            p = _pin
            _pin = _pin.num
        try:
            p.prevstate = p.state
        except:
            print(p)

        answer = None
        if __state == 1:
            while answer != 3001 or answer is None:
                answer = self.write('P', _pin, __state)
                # print(f'set_pin get answer {answer}')
        elif __state == 0:
            while answer != 3000 or answer is None:
                answer = self.write('P', _pin, __state)
                # print(f'set_pin get answer {answer}')
        else:
            while answer != 3001 and answer != 3000 or answer is None:
                answer = self.write('P', _pin, __state)
                # print(f'set_pin get answer {answer}')

        if answer is not None:
            p.LastRevTime = datetime.now()
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
                if self.write('S', p.num, 0) == 2001:
                    p.state = True
                else:
                    p.state = False
                if allpins:
                    p.prevstate = p.state
                self.PinReaction(p)
        if self.DCCheckTimer <= 0:
            val = self.write('A', 1, 0)
            voltage_now = round(gf.map_func(val, 0, 1023, 0, 40.1), 2)
            self.DCVolArray.pop(0)
            self.DCVolArray.append(voltage_now)
            self.DCVol = round(gf.array_ma(self.DCVolArray), 2)
            percent = round(gf.map_func(self.DCVol, 22, 27, 0, 100), 0)
            if percent > 100:
                percent = 100
            elif percent < 0:
                percent = 0
            self.DCVoltageInPercent = percent
            if self.DCVoltageInPercent == 100:
                self.DCVolLowAlertSended = False

            acc_exist = val = self.write('A', 0, 0)
            # print(acc_exist)
            if acc_exist > 500:
                self.ACCExist = True
            else:
                if self.ACCExist:
                    self.ACNonExistStartTimer = datetime.now()
                self.ACCExist = False
            # print(self.ACCExist)
            self.DCCheckTimer = 50
        else:
            self.DCCheckTimer -= 1

    def PinReaction(self, p):
        # p - swich (S-pin)
        # b - bind (DG-pin)
        if p.state != p.prevstate:
            for b in p.binds:
                if not p.blocked and not b.blocked:
                    print(f'im set pin {b.description} to {p.state} by PinReaction in {datetime.now().strftime("%X")}')
                    self.set_pin(b.num, p.state)
                    p.LastRevTime = datetime.now()
                    b.LastRevTime = datetime.now()

    def write(self, cmd, val1, val2):
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
            print('error save pinstate')

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
            print('pinstate is loaded')
        except:
            print('error load pinstate')

    def initialize(self):
        while not self.initialized:
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                comport = p.device
                print('Try to find Arduino in ' + comport)
                self.port = serial.Serial(comport, 57600, timeout=1)  # change ACM number as found from ls /dev/tty/ACM*
                self.port.reset_output_buffer()
                self.port.reset_input_buffer()
                self.port.baudrate = 57600
                self.port.timeout = 1
                self.port.write_timeout = 1
                sleep(3)
                a = self.write('I', 666, 1)
                # print(a)
                if (a == 666):
                    self.initialized = True
                    self.check_input_pins(True)
                    break
            if not self.initialized:
                print('I have not found the Arduino...')
                print("Sorry, but i can't work whithout Arduino subcontroller :(")
                # print("I'm have to try to find it after one second pause")
            else:
                print('Arduino is initialized on port ' + comport)
                self.load_pinstate()

    def LoadConfig(self, _telegram_users, first_load=True):
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

                _CT = []
                if len(line) > 5:
                    for i in range(6, len(line)):
                        _CT.append(line[i])
                if not self.pin(_num) in self.pins:
                    self.pins.append(Pins(_output, int(_num), _BCOD, _name, _description, _CT))
            elif line[0] == 'bind':
                _pin = self.pin(line[1])
                if _pin is not None:
                    for i in range(2, len(line)):
                        _pin2 = self.pin(line[i])
                        if _pin2 is not None:
                            if _pin2 not in _pin.binds:
                                _pin.binds.append(_pin2)
            elif line[0] == 'telegram_user':
                _telegram_users.append(telegram_bot.TelegramUserClass(line[1], line[2], int(line[3])))

            __answer = 'config loaded!'
            lightpin = self.FindByAuction('свет на улице')
            if str(type(lightpin)) != "<class 'list'>" and lightpin is not None:
                self.OutDoorLightPin = self.FindByAuction('свет на улице')
            else:
                print('Не могу подобрать пин уличного освещения!')
        print(__answer)
        return __answer

    def SaveConfig(self, _telegram_users):
        try:
            f = open(self.config_path, 'w')
            f.write(
                '# pin line: pin <arduino pin number> <name> <input/output> <description> <blocked> convertible terms' + '\n')
            f.write('# Inputs:' + '\n')
            for p in self.pins:
                if not p.output:
                    ct = ''
                    for c in p.ConvertibleTerms:
                        ct += f' {c}'
                    f.write(f'pin {p.num} {p.name} input {p.description} {p.BCOD}{ct}' + '\n')
            f.write('\n')
            f.write('# Outputs:' + '\n')
            for p in self.pins:
                if p.output:
                    ct = ''
                    for c in p.ConvertibleTerms:
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
            for u in _telegram_users:
                f.write(f'telegram_user {u.name} {u.ID}' + '\n')

            answer = None
        except:
            answer = 'error save config'
        return answer

    def FindByAuction(self, cmd, allpins=False):
        if str(type(cmd)) != "<class 'list'>":
            cmd = str(cmd)
            _wordlist = cmd.split(' ')
        else:
            _wordlist = cmd
        wordlist = []
        for w in _wordlist:
            if w not in __not_important_words:
                wordlist.append(w)
        PinAuction = []
        for p in self.pins:
            if p.output or allpins:  # добавляем выходы в аукцион
                ct_all = []
                for c in p.ConvertibleTerms:
                    ct_all.append(c)
                ct_all.append(p.description)
                ct_all.append(str(p.num))
                ct_all.append(p.name.lower())
                PinAuction.append([p.num, ct_all, 0])

        for word in wordlist:
            for PA in PinAuction:
                includes = 0;
                # print(f'count points for {PA[0]}')
                for ct in PA[1]:
                    if ct.lower() == word:
                        PA[2] += 2
                        # print(f'word = {word} 2 points')
                    elif ct.lower().find(word) > -1:
                        PA[2] += 1
                        # print(f'word find {word} 1 point')

        MaxIncludes = 0;
        Winners = []
        for PA in PinAuction:
            if PA[2] > MaxIncludes:
                MaxIncludes = PA[2]

        if MaxIncludes > 0:
            for PA in PinAuction:
                if PA[2] == MaxIncludes:
                    Winners.append(self.pin(PA[0]))

        if len(Winners) == 1:
            print(f'winner is {Winners[0].description}')
            print(f'winner get {MaxIncludes} points')
            return Winners[0]
        elif len(Winners) > 1:
            print('Winners more than one')
            print(f'its get {MaxIncludes} points')
            return Winners
        else:
            print('winner not found')
            return None
