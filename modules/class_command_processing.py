import logging
import copy
from builtins import isinstance

from .gfunctions import JPrint
from .gfunctions import difference_between_date
from .gfunctions import VERSION
from datetime import datetime
jprint = JPrint.jprint

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s (%(levelname)s) %(asctime)s: %(message)s'
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d/%m/%y %H:%M:%S')
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d/%m/%y %H:%M:%S')

# Command processing class
class CommandProcessing:
    logger = logging.getLogger('Command processing')
    logger.setLevel(LOG_LEVEL)

    @staticmethod
    def set_info():
        CommandProcessing.logger.setLevel(logging.INFO)
        jprint('set INFO level in CommandProcessiong logger')

    @staticmethod
    def set_debug():
        CommandProcessing.logger.setLevel(logging.DEBUG)
        jprint('set DEBUG level in CommandProcessiong logger')

    @staticmethod
    def set_warning():
        CommandProcessing.logger.setLevel(logging.WARNING)
        jprint('set WARNING level in CommandProcessiong logger')

    def __init__(self, jarvis):
        self._name = 'command_processing'
        self.jarvis = jarvis
        self.START_TIME = datetime.now()
        self.modules = [self, jarvis.arduino, jarvis.bot, jarvis.satellite_server, jarvis.laser_turret, jarvis.laser_turret.laser, jarvis.sensors.sonoff1]
        # set info logger level by default
        for module in self.modules:
            module.set_info()
        self.logger.info('Set INFO logger level for all modules by default.')

    @property
    def name(self):
        return self._name

    def get_access_error(self):
        return 'У вас нет доступа к этой команде'

    def command_processing(self, cmd, telegramuser, message):
        get_access_error = self.get_access_error
        info = CommandProcessing.logger.info
        debug = CommandProcessing.logger.debug
        warning = CommandProcessing.logger.warning
        error = CommandProcessing.logger.error

        cmd = cmd.lower()
        print_lst = f'first command: {cmd}'
        if telegramuser != None:
            print_lst += f' from {telegramuser.name}'
        debug(print_lst)
        global_cmd_list = cmd.split(' ')
        cmdlist_by_and = cmd.split(' и ')
        answer = ''
        for list_by_and in cmdlist_by_and:
            cmd_list = list_by_and.split(' ')

            if 'включи' not in cmd_list and 'включи' in global_cmd_list:
                cmd_list.append('включи')
            elif ('выключи' not in cmd_list and 'выключи' in global_cmd_list) or (
                    'отключи' not in cmd_list and 'отключи' in global_cmd_list):
                cmd_list.append('выключи')
            elif 'заблокируй' not in cmd_list and 'заблокируй' in global_cmd_list:
                cmd_list.append('заблокируй')
            elif 'разблокируй' not in cmd_list and 'разблокируй' in global_cmd_list:
                cmd_list.append('разблокируй')

            if ('свет' not in cmd_list and 'свет' in global_cmd_list) or (
                    'освещение' not in cmd_list and 'освещение' in global_cmd_list):
                cmd_list.append('свет')
            debug(f'cmd in loop: {cmd_list}')

            if 'включи' in cmd_list or 'on' in cmd_list:
                if 'свет' in cmd_list and ('везде' in cmd_list or 'доме' in cmd_list or 'дома' in cmd_list):
                    if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                        for p in self.jarvis.arduino.pins:
                            if p.output and 'свет' in p.convertible_terms and 'дом' in p.convertible_terms:
                                if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                    self.jarvis.arduino.set_pin(p, 1)
                                    jprint(f'Включил свет в {p.description}')
                                else:
                                    answer += f'{p.description} заблокирован для вас'
                        answer += 'Включил свет везде.'
                    else:
                        answer += get_access_error()
                elif 'свет' in cmd_list and ('первом' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                    if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                        for p in self.jarvis.arduino.pins:
                            if 'свет' in p.convertible_terms and 'первый' in p.convertible_terms and (
                                    'этаж' in p.convertible_terms or 'этаже' in p.convertible_terms) and p.output:
                                if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                    self.jarvis.arduino.set_pin(p, 1)
                                    jprint(f'Включил свет в {p.description}')
                                else:
                                    answer += f'{p.description} заблокирован для вас'
                        answer += 'Включил свет на первом этаже.'
                    else:
                        answer += get_access_error()
                elif 'свет' in cmd_list and ('втором' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                    if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                        for p in self.jarvis.arduino.pins:
                            if 'свет' in p.convertible_terms and 'втором' in p.convertible_terms and (
                                    'этаж' in p.convertible_terms or 'этаже' in p.convertible_terms) and p.output:
                                if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                    self.jarvis.arduino.set_pin(p, 1)
                                    jprint(f'Включил свет в {p.description}')
                                else:
                                    answer += f'{p.description} заблокирован для вас'
                        answer += 'Включил свет на втором этаже.'
                    else:
                        answer += get_access_error()
                elif 'охранный' in cmd_list and 'режим' in cmd_list:
                    if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                        answer += self.jarvis.satellite_server.arduino_sensors.on_guard_mode()
                    else:
                        answer += get_access_error()
                else:
                    # elif 'свет' in cmd_list:
                    if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                        # Добавим личный флаг пользователя
                        findlist = copy.deepcopy(cmd_list)
                        if telegramuser != None:
                            findlist.append(telegramuser.name)
                        WinnerPin = self.jarvis.arduino.find_by_auction(findlist)
                        if WinnerPin == None:
                            answer += 'Не понятно, что нужно включить. Уточни команду.'
                        elif str(type(WinnerPin)) == "<class 'list'>":
                            if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                                for p in WinnerPin:
                                    if p.output:
                                        if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                            a = self.jarvis.arduino.set_pin(p, 1)
                                            if a == True:
                                                answer += f'{p.description} включен'
                                            elif a == False:
                                                answer += f'{p.description} выключен'
                                            else:
                                                answer += 'Ошибка передачи данных'
                                        else:
                                            answer += f'{p.description} заблокирован для вас'
                            else:
                                answer += get_access_error()
                        else:
                            if telegramuser != None and telegramuser.level <= 1 or telegramuser == None or (
                                    telegramuser != None and telegramuser.name in WinnerPin.convertible_terms):
                                if telegramuser != None and telegramuser.level <= 0 and WinnerPin.blocked or telegramuser == None or not WinnerPin.blocked:
                                    a = self.jarvis.arduino.set_pin(WinnerPin, 1)
                                    if a == True:
                                        answer += f'{WinnerPin.description} включен'
                                    elif a == False:
                                        answer += f'{WinnerPin.description} выключен'
                                    else:
                                        answer += 'Ошибка передачи данных'
                                else:
                                    answer += f'{WinnerPin.description} заблокирован для вас'
                            else:
                                answer += get_access_error()
                    else:
                        answer += get_access_error()
            elif 'выключи' in cmd_list or 'отключи' in cmd_list or 'off' in cmd_list:
                if 'свет' in cmd_list and ('везде' in cmd_list or 'доме' in cmd_list or 'дома' in cmd_list):
                    if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                        for p in self.jarvis.arduino.pins:
                            if p.output and 'свет' in p.convertible_terms and 'дом' in p.convertible_terms:
                                if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                    self.jarvis.arduino.set_pin(p, 0)
                                    jprint(f'Выключил свет в {p.description}')
                                else:
                                    answer += f'{p.description} заблокирован для вас'
                        answer += 'Выключил свет везде.'
                    else:
                        answer += get_access_error()
                elif 'свет' in cmd_list and ('первом' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                    if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                        for p in self.jarvis.arduino.pins:
                            if 'свет' in p.convertible_terms and 'первом' in p.convertible_terms and (
                                    'этаж' in p.convertible_terms or 'этаже' in p.convertible_terms) and p.output:
                                if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                    self.jarvis.arduino.set_pin(p, 0)
                                    jprint(f'Выключил свет в {p.description}')
                                else:
                                    answer += f'{p.description} заблокирован для вас'
                        answer += 'Выключил свет на первом этаже.'
                    else:
                        answer += get_access_error()
                elif 'свет' in cmd_list and ('втором' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                    if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                        for p in self.jarvis.arduino.pins:
                            if 'свет' in p.convertible_terms and 'втором' in p.convertible_terms and (
                                    'этаж' in p.convertible_terms or 'этаже' in p.convertible_terms) and p.output:
                                if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                    self.jarvis.arduino.set_pin(p, 0)
                                    jprint(f'Выключил свет в {p.description}')
                                else:
                                    answer += f'{p.description} заблокирован для вас'
                        answer += 'Выключил свет на втором этаже.'
                    else:
                        answer += get_access_error()
                elif 'лазер' in cmd_list:
                    self.jarvis.laser_turret.laser.laser_on = False
                    self.jarvis.laser_turret.laser.stop_game()
                    answer = 'ок'
                elif 'охранный' in cmd_list and 'режим' in cmd_list:
                    if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                        answer += self.jarvis.satellite_server.arduino_sensors.off_guard_mode()
                    else:
                        answer += get_access_error()
                else:
                    # elif 'свет' in cmd_list:
                    if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                        findlist = copy.deepcopy(cmd_list)
                        if telegramuser != None:
                            findlist.append(telegramuser.name)
                        WinnerPin = self.jarvis.arduino.find_by_auction(findlist)
                        if WinnerPin == None:
                            answer += 'Не понятно, что нужно выключить. Уточни команду.'
                        elif isinstance(WinnerPin, list):
                            if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                                for p in WinnerPin:
                                    if p.output:
                                        if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                            a = self.jarvis.arduino.set_pin(p, 0)
                                            if a == True:
                                                answer += f'{p.description} включен'
                                            elif a == False:
                                                answer += f'{p.description} выключен'
                                            else:
                                                answer += 'Ошибка передачи данных'
                                        else:
                                            answer += f'{p.description} заблокирован для вас'
                            else:
                                answer += get_access_error()
                        else:
                            if telegramuser != None and telegramuser.level <= 1 or telegramuser == None or (
                                    telegramuser != None and telegramuser.name in WinnerPin.convertible_terms):
                                if telegramuser != None and telegramuser.level <= 0 and WinnerPin.blocked or telegramuser == None or not WinnerPin.blocked:
                                    a = self.jarvis.arduino.set_pin(WinnerPin, 0)
                                    if a == True:
                                        answer += f'{WinnerPin.description} включен'
                                    elif a == False:
                                        answer += f'{WinnerPin.description} выключен'
                                    else:
                                        answer += 'Ошибка передачи данных'
                                else:
                                    answer += f'{WinnerPin.description} заблокирован для вас'
                            else:
                                answer += get_access_error()
                    else:
                        answer += get_access_error()
            elif ('верни' in cmd_list and (
                    'было' in cmd_list or 'обратно' in cmd_list)) or 'пошутил' in cmd_list or 'шутка' in cmd_list:
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in self.jarvis.arduino.pins:
                        if (datetime.now() - p.last_rev_time).total_seconds() <= 30:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                a = self.jarvis.arduino.set_pin(p, p.prevstate)  # prev pin state
                                jprint(f'pin {p.num} is {a}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Вернул все как было'
                else:
                    answer += get_access_error()
            elif 'оставь' in cmd_list and 'свет' in cmd_list:
                if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                    WinnerPin = self.jarvis.arduino.find_by_auction(cmd_list)
                    if WinnerPin == None:
                        answer += 'Не понятно, что нужно оставить включенным. Уточни команду.'
                    elif str(type(WinnerPin)) == "<class 'list'>":
                        if ('кухне' in cmd_list or 'кухня' in cmd_list) and len(WinnerPin) == 2:
                            if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                                for p in self.jarvis.arduino.pins:
                                    if p.output and p in WinnerPin:
                                        if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                            self.jarvis.arduino.set_pin(p, 1)
                                        else:
                                            answer += f'{p.description} заблокирован для вас'
                                    elif p.output and 'свет' in p.convertible_terms and 'первый' in p.convertible_terms and 'этаж' in p.convertible_terms:
                                        if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                            self.jarvis.arduino.set_pin(p, 0)
                                        else:
                                            answer += f'{p.description} заблокирован для вас'
                                answer += 'Оставил включенным только свет на кухне.'
                            else:
                                answer += get_access_error()
                        else:
                            answer += 'Я нашел более одного объекта для оставления:'
                            for w in WinnerPin:
                                answer += f'{w.description}\n'
                            answer += 'Нужно уточнить, что конкретно оставить.'
                    else:
                        if telegramuser != None and telegramuser.level <= 1 or telegramuser == None or (
                                telegramuser != None and telegramuser.name in WinnerPin.convertible_terms):
                            HouseLevel = 'первый'
                            if 'второй' in WinnerPin.convertible_terms:  # Определяем к какому этажу относится команда
                                HouseLevel = 'второй'
                            for p in self.jarvis.arduino.pins:
                                if p.output and 'свет' in p.convertible_terms and HouseLevel in p.convertible_terms and 'этаж' in p.convertible_terms:
                                    if p == WinnerPin:
                                        if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                            a = self.jarvis.arduino.set_pin(p, 1)
                                        else:
                                            answer += f'{p.description} заблокирован для вас'
                                    else:
                                        if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                            a = self.jarvis.arduino.set_pin(p, 0)
                                        else:
                                            answer += f'{p.description} заблокирован для вас'
                            answer += f'Оставил включенным только {WinnerPin.description}'
                        else:
                            answer += get_access_error()
                else:
                    answer += get_access_error()
            elif 'заблокируй' in cmd_list or 'заблокирую' in cmd_list:
                if "все" in cmd_list and "выключатели" in cmd_list:
                    for p in self.jarvis.arduino.pins:
                        if not p.output:
                            p.blocked = True
                    answer += f'Заблокировал все выключатели'
                elif telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                    WinnerPin = self.jarvis.arduino.find_by_auction(cmd_list, True)
                    if WinnerPin == None:
                        answer += 'Не понятно, что нужно заблокировать. Уточни команду.'
                    elif str(type(WinnerPin)) == "<class 'list'>":
                        for p in WinnerPin:
                            p.blocked = True
                            answer += f'Заблокировал {p.description}'
                    else:
                        WinnerPin.blocked = True
                        answer += f'Заблокировал {WinnerPin.description}'
                    self.jarvis.arduino.write_pinstate(None)
                else:
                    answer += get_access_error()
            elif 'разблокируй' in cmd_list or 'разблокирую' in cmd_list:
                if "все" in cmd_list and "выключатели" in cmd_list:
                    for p in self.jarvis.arduino.pins:
                        if not p.output:
                            p.blocked = False
                    answer += f'Заблокировал все выключатели'
                elif telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                    WinnerPin = self.jarvis.arduino.find_by_auction(cmd_list, True)
                    if WinnerPin == None:
                        answer += 'Не понятно, что нужно разблокировать. Уточни команду.'
                    elif str(type(WinnerPin)) == "<class 'list'>":
                        for p in WinnerPin:
                            p.blocked = False
                            answer += f'Разблокировал {p.description}'
                    else:
                        WinnerPin.blocked = False
                        answer += f'Разблокировал {WinnerPin.description}'
                    self.jarvis.arduino.write_pinstate(None)
                else:
                    answer += get_access_error()
            elif cmd.find('pinstate') > -1:
                if telegramuser != None and telegramuser.level <= 3 or telegramuser == None:
                    try:
                        val = cmd.split(' ')[1]
                    except:
                        val = -1
                    pin = self.jarvis.arduino.find_pin(val)
                    if pin != None:
                        if pin.state:
                            answer = f'pin {pin.num} is ON'
                        else:
                            answer = f'pin {pin.num} is OFF'
                    else:
                        answer = f"Can't find the pin with number {val}"
                else:
                    answer += get_access_error()
            elif cmd.find('loadconfig') > -1 or cmd.find('загрузи конфиг') > -1:
                if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                    answer = self.jarvis.arduino.load_config(self.jarvis.bot)
                else:
                    answer += get_access_error()
            elif cmd.find('pinlist') > -1 or cmd.find('list pins') > -1 or cmd.find('listpins') > -1 or cmd.find(
                    'список пинов') > -1 or cmd.find('пинлист') > -1:
                if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                    answer += '*** Pin list: ***\n'
                    answer += 'Inputs:\n'
                    for p in self.jarvis.arduino.pins:
                        if not p.output:
                            answer += f'   pin {p.num} ({p.name})'
                            if p.blocked:
                                answer += '(blocked)'
                            if len(p.binds) > 0:
                                answer += ' >>> '
                                k = 0
                                for b in p.binds:
                                    if k != 0:
                                        answer += ','
                                    answer += f' {b.num} ({b.description})'
                                    k += 1
                    answer += 'Outputs:\n'
                    for p in self.jarvis.arduino.pins:
                        if p.output:
                            answer += f'   pin {p.num} ({p.name})'
                            if p.blocked:
                                answer += '(blocked)'
                else:
                    answer += get_access_error()
            elif cmd.startswith('bind '):
                if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                    try:
                        val = cmd.split(' ')
                        bindto = self.jarvis.arduino.find_pin(val[1])
                        if not bindto.output:
                            for i in range(2, len(val)):
                                addpin = self.jarvis.arduino.find_pin(val[i])
                                if addpin.output:
                                    if not addpin in bindto.binds:
                                        bindto.binds.append(addpin)
                                    else:
                                        answer += f'pin {addpin.name} is already in {bindto.name}.binds'
                                else:
                                    answer += f'pin {addpin.name} is INPUT pin and connot binded to pin {bindto.name}'
                            answer += 'pins is binded!'
                            if self.jarvis.arduino.save_config() == None:
                                answer += 'config is saved'
                            else:
                                answer += 'error save config'
                        else:
                            answer += f'pin {bindto.name} is OUTPUT pin and you cant bind to it.'
                    except:
                        answer += 'error bind pins'
                else:
                    answer += get_access_error()
            elif cmd.startswith('unbind '):
                if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                    try:
                        val = cmd.split(' ')
                        bindto = self.jarvis.arduino.find_pin(val[1])
                        if not bindto.output:
                            for i in range(2, len(val)):
                                bindto.binds.remove(self.jarvis.arduino.find_pin(val[i]))
                            answer = 'pins is unbinded!'
                            if self.jarvis.arduino.save_config() == None:
                                answer += 'config is saved'
                            else:
                                answer += 'error save config'
                        else:
                            answer += f'pin {bindto.name} is OUTPUT pin and you cant bind to it.'
                    except:
                        answer = 'error unbind pins'
                else:
                    answer += get_access_error()
            elif (cmd.find('print') > -1 and cmd.find('config') > -1) or (
                    cmd.find('покажи') > -1 and cmd.find('конфиг') > -1):
                if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                    f = open(self.jarvis.arduino.config_path, 'r')
                    try:
                        answer += f.read()
                        f.close()
                    except:
                        answer += 'не могу прочесть конфиг'
                else:
                    answer += get_access_error()
            elif cmd == 'state' or cmd == 'status' or 'статус' in cmd_list:
                answer += self.status_cmd(cmd_list, telegramuser, message)
            elif 'риги' in cmd_list or 'rigs' in cmd_list:
                if telegramuser != None and telegramuser.level == 0 or telegramuser == None:
                    answer += 'риги:\n'
                    for miner in self.jarvis.satellite_server.miners:
                        answer += miner.name + f'({miner.runned_text()}) st {miner.shutdown_threshold[0]}/{miner.shutdown_threshold[1]}V\n'

                    answer += '\n'
                    # инфа по напряжениям
                    answer += f'Напряжение в сети {self.jarvis.arduino.ac_exist_str} ({self.jarvis.sensors.ac_voltage_input}V)'
                else:
                    answer += get_access_error()
            elif cmd == 'exit':
                if telegramuser is None:  # выходить можно только из консоли
                    jprint('bye...')
                    self.jarvis.runned = False
                else:
                    answer += get_access_error()
            elif cmd.find('запусти') > -1 and cmd.find('майнинг') > -1:
                self.jarvis.satellite_server.start_miners()
                answer += 'запустил майнинг'
            elif (cmd.find('останови') > -1 or cmd.find('заверши') > -1 or cmd.find('выключи') > -1 or
                  cmd.find('выруби') > -1) and cmd.find('майнинг') > -1:
                self.jarvis.satellite_server.stop_miners()
                answer = 'остановил майнинг'
            elif 'info' in cmd_list:
                if len(cmd_list) == 1:
                    for module in self.modules:
                        module.set_info()
                elif len(cmd_list) == 2:
                    for module in self.modules:
                        if module.name == cmd_list[1]:
                            module.set_info()
                else:
                    self.logger.error('DEBUG command is wrong format, <debug <modulename>')
            elif 'debug' in cmd_list:
                if len(cmd_list) == 1:
                    for module in self.modules:
                        module.set_debug()
                elif len(cmd_list) == 2:
                    for module in self.modules:
                        if module.name == cmd_list[1]:
                            module.set_debug()
                else:
                    self.logger.error('DEBUG command is wrong format, <debug <modulename>')
            elif 'warning' in cmd_list:
                if len(cmd_list) == 1:
                    for module in self.modules:
                        module.set_warning()
                elif len(cmd_list) == 2:
                    for module in self.modules:
                        if module.name == cmd_list[1]:
                            module.set_warning()
                else:
                    self.logger.error('WARNING command is wrong format, <debug <modulename>')
            elif cmd == 'reload laser' or cmd == 'reload_laser':
                answer += 'reload laser'
            elif cmd == 'homing':
                self.jarvis.laser_turret.laser.stop_game()
                answer += 'ok'
            elif cmd == 'coords':
                print(f'{self.jarvis.laser_turret.laser.x}, {self.jarvis.laser_turret.laser.y}')
                answer += 'ok'
            elif (cmd.find('поигра') > -1 or cmd.find('развлек') > -1) and cmd.find('кот') > -1:
                if not self.jarvis.laser_turret.laser.game_mode:
                    _game_time = 0
                    for _cm in cmd_list:
                        try:
                            _game_time = int(_cm)
                        except:
                            pass
                    _game_time = self.jarvis.laser_turret.laser.start_game(_game_time)
                    answer = f'сейчас развлечем шерстяную жопу на целых {_game_time} секунд'
                else:
                    answer = 'кажется шерстяная жопа уже развлекается...'
            elif 'стоп' in cmd_list or 'хватит' in cmd_list or 'остановись' in cmd_list:
                if self.jarvis.laser_turret.laser.game_mode:
                    self.jarvis.laser_turret.laser.stop_game()
                    answer = 'ок'
                else:
                    answer = 'ок'
            else:
                answer += 'неизвестная команда\n'

        if message != None:
            self.jarvis.telegram_answer_queue.put((message, answer))  # Поместили сообщение в оцередь на обработку
        return answer + '\n'

    def status_cmd(self, cmd_list, telegramuser, message):
        answer = ''
        if telegramuser != None and telegramuser.level <= 3 or telegramuser == None:
            uptime = difference_between_date(self.START_TIME, datetime.now())
            answer += 'ver. ' + VERSION + '   '
            answer += f'uptime {uptime}\n'
            answer += f'outside temp. {self.jarvis.satellite_server.arduino_sensors.temp_outside}C\n'
            if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                    answer += f'move time {self.jarvis.satellite_server.arduino_sensors.last_move_time_str()} /' \
                              f'({self.jarvis.satellite_server.arduino_sensors.last_move_time_sec()} sec. ago)\n'
                if self.jarvis.satellite_server.arduino_sensors.guard_mode:
                    answer += f'ОХРАННЫЙ РЕЖИМ включен\n'
                answer += 'Включенный свет:\n'
                k = 0
                for p in self.jarvis.arduino.pins:
                    if p.output and 'свет' in p.convertible_terms and p.state:
                        if k > 0:
                            answer += ' ,'
                        answer += f'{p.description}'
                        k += 1
                if k == 0:
                    answer += 'весь свет выключен\n'
                answer += '\n'

            # инфа по насосам
            answer += "Насосы "
            pumpsPin = self.jarvis.arduino.find_pin("насосы")
            if pumpsPin is not None:
                if pumpsPin.state:
                    answer += "включены"
                else:
                    answer += "ВЫКЛЮЧЕНЫ"
                answer += '\n'
            else:
                answer += "<не могу найти пин насосов  по description 'насосы'>"

            answer += '\n'
            # инфа по напряжениям
            answer += f'Напряжение в сети {self.jarvis.arduino.ac_exist_str} ({self.jarvis.sensors.ac_voltage_input}V)\n'
            answer += f'Напряжение аккумулятора {self.jarvis.arduino.dc_value} V ({self.jarvis.arduino.dc_voltage_in_percent} %)'
        else:
            answer += self.get_access_error()