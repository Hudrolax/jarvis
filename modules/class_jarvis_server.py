from .class_com import CommunicationServer
import logging
import threading
from time import sleep
from datetime import datetime

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s (%(levelname)s) %(asctime)s: %(message)s'
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO
#LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')

class Miner():
    logger = logging.getLogger('Miner')
    logger.setLevel(logging.DEBUG)
    RESET_ONLINE_TIMER = 60

    def __init__(self, name:str, instant_off_by_poweroff, shutdown_threshold:tuple):
        if not isinstance(name, str):
            raise Exception('miner name is not "str"')
        self._name = name
        self._runned = False
        self._online = False
        self._online_reset_timer = Miner.RESET_ONLINE_TIMER
        self._online_reset_thread = threading.Thread(target=self._reset_online_timer, args=(), daemon=True)
        self._online_reset_thread.start()
        self._start_it = False
        self._stop_it = False
        self._bcod_reaction = False
        self.instant_off_by_poweroff = instant_off_by_poweroff
        self.shutdown_threshold = shutdown_threshold
        
    @property
    def online(self):
        return self._online
    
    @online.setter
    def online(self, val):
        if isinstance(val, bool):
            self._online = val
        else:
            raise TypeError(f'Miner class ERROR: "online" is {type(val)}, but "bool" expected')

    def online_text(self):
        if self.online:
            return 'online'
        else:
            return 'offline'

    @property
    def bcod_reaction(self):
        return self._bcod_reaction

    @bcod_reaction.setter
    def bcod_reaction(self, val):
        if isinstance(val, bool):
            self._bcod_reaction= val
        else:
            raise TypeError(f'Miner class ERROR: "bcod_reaction" is {type(val)}, but "bool" expected')

    @property
    def runned(self):
        return self._runned

    @runned.setter
    def runned(self, val):
        if isinstance(val, bool):
            self._runned = val
        else:
            raise TypeError(f'Miner class ERROR: "runned" is {type(val)}, but "bool" expected')

    def runned_text(self):
        if self.runned:
            return 'on'
        else:
            return 'off'

    @property
    def name(self):
        return self._name

    @property
    def start_it(self):
        return self._start_it

    @start_it.setter
    def start_it(self, val):
        if isinstance(val, bool):
            self._start_it = val
        else:
            raise TypeError('start_it bool expected')

    @property
    def stop_it(self):
        return self._stop_it

    @stop_it.setter
    def stop_it(self, val):
        if isinstance(val, bool):
            self._stop_it = val
        else:
            raise TypeError('stop_it bool expected')

    def __str__(self):
        return self._name
    
    def _reset_online_timer(self):
        while True:
            sleep(1)
            if self._online_reset_timer > 0:
                self._online_reset_timer -= 1
            else:
                self._online_reset_timer = Miner.RESET_ONLINE_TIMER
                self.online = False

    def it_is_online(self):
        self.online = True
        self._online_reset_timer = Miner.RESET_ONLINE_TIMER

    def start(self):
        self._start_it = True
        self._stop_it = False

    def stop(self):
        self._start_it = False
        self._stop_it = True


class Jarvis_Satellite_Server(CommunicationServer):
    logger = logging.getLogger('Jarvis_Satellite_Server')
    logger.setLevel(logging.INFO)

    def __init__(self, jarvis, ip:str ='127.0.0.1', port:int = 8585):
        super().__init__(ip, port)
        self.jarvis = jarvis
        self._name = 'satellite_server'
        self._miners = []
        self.shutdown_thresold_action_timer = datetime.now()

    @property
    def miners(self):
        return self._miners

    def shutdown_threshold_action(self):
        info = Jarvis_Satellite_Server.logger.info
        for miner in self.miners:
            if miner.shutdown_threshold[0] > 0:
                if miner.runned and self.jarvis.sensors.ac_voltage_input < miner.shutdown_threshold[0]:
                    info(f'miner {miner} stopped by shutdown_threshold')
                    miner.stop()
                    if self.jarvis.sensors.sonoff1.logger.level == logging.DEBUG:
                        self.jarvis.bot.send_message_to_admin(f'miner {miner} stopped by shutdown_threshold')
                elif not miner.runned and self.jarvis.sensors.ac_voltage_input > miner.shutdown_threshold[1] and  (datetime.now() - self.shutdown_thresold_action_timer).total_seconds() > 300:
                    info(f'miner {miner} startded by shutdown_threshold')
                    miner.start()
                    if self.jarvis.sensors.sonoff1.logger.level == logging.DEBUG:
                        self.jarvis.bot.send_message_to_admin(f'miner {miner} started by shutdown_threshold')
                    self.shutdown_thresold_action_timer = datetime.now()

    def stop_miners(self, bcod_reaction = False, bot=None):
        info = Jarvis_Satellite_Server.logger.info
        for miner in self.miners:
            if miner.instant_off_by_poweroff and miner.runned:
                miner.stop()
                if bcod_reaction and not miner.bcod_reaction:
                    miner.bcod_reaction = True
                    info(f"miner {miner.name} (bcod_reaction = {bcod_reaction}) is runned. Let's stop it.")
                    if bot is not None:
                        self.jarvis.bot.send_message_to_admin(f'Выключил miner "{miner.name}"')

    def start_miners(self, bcod_reaction = False, bot=None):
        info = Jarvis_Satellite_Server.logger.info
        for miner in self.miners:
            if not miner.runned:
                if not bcod_reaction or bcod_reaction and miner.bcod_reaction:
                    miner.start()
                    miner.bcod_reaction = False
                    info(f"miner {miner.name} (bcod_reaction = {bcod_reaction}) is not runned. Let's start it.")
                    if bot is not None:
                        self.jarvis.bot.send_message_to_admin(f'Включил miner "{miner.name}"')

    def _find_miner(self, miner):
        for m in self._miners:
            if isinstance(miner, Miner):
                if m.name == miner.name:
                    return m
            elif isinstance(miner, str):
                if m.name == miner:
                    return m
        return None

    def add_miner(self, name, instant_off_by_poweroff, shutdown_threshold = (0, 0)):
        if self._find_miner(name) is None:
            self._miners.append(Miner(name, instant_off_by_poweroff, shutdown_threshold))

    def handler(self, client_address, data):
        # client_address - адрес клиента
        # data - очищенные данные - только строка
        debug = Jarvis_Satellite_Server.logger.debug
        info = Jarvis_Satellite_Server.logger.info
        answer = 'none'
        # <<обработчик данных
        data = data.split(':')
        if len(data) != 2:
            return None
        name = data[0]
        message = data[1]
        debug(f'get "{message}" from {name}')
        if name.find('wemos') > -1: # подключается wemos
            answer = 'ok'
        else: # подключается satellite
            if message == 'ping':
                miner = self._find_miner(name)
                if miner is not None:
                    miner.it_is_online()
                answer = 'ok'
            elif message == 'miner_is_runned':
                miner = self._find_miner(name)
                if miner is not None:
                    debug('miner is runned')
                    miner.runned = True
                    miner.start_it = False
                    if miner.stop_it:
                        answer = 'stop_miner'
            elif message == 'miner_is_not_runned':
                miner = self._find_miner(name)
                if miner is not None:
                    debug("miner is not runned")
                    miner.runned = False
                    miner.stop_it = False
                    if miner.start_it:
                        answer = 'start_miner'
        return answer

if __name__ == '__main__':
    pass

    print(isinstance(27.1, float))

    # from time import sleep
    #
    # server = Jarvis_Satellite_Server(name='Jarvis')
    # server.add_miner('serverx')
    # server.add_miner('zeon')
    # server.add_miner('tekilla')
    #
    # server.start()
    #
    # while True:
    #     sleep(10)
    #     server.stop_miners()
    #     sleep(10)
    #     server.start_miners()
    # server.stop()