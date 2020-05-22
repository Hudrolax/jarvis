from class_com import CommunicationServer
import logging

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

    def __init__(self, name:str):
        if not isinstance(name, str):
            raise Exception('miner name is not "str"')
        self._name = name
        self._runned = False
        self._start_it = False
        self._stop_it = False
        self._bcod_reaction = False

    @property
    def bcod_reaction(self):
        return self._bcod_reaction

    @bcod_reaction.setter
    def bcod_reaction(self, val):
        if isinstance(val, bool):
            self._bcod_reaction= val
        else:
            raise Exception(f'Miner class ERROR: "bcod_reaction" is {type(val)}, but "bool" expected')

    @property
    def runned(self):
        return self._runned

    @runned.setter
    def runned(self, runned):
        if isinstance(runned, bool):
            self._runned = runned
        else:
            raise Exception(f'Miner class ERROR: "runned" is {type(runned)}, but "bool" expected')

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
            raise Exception('start_it bool expected')

    @property
    def stop_it(self):
        return self._stop_it

    @stop_it.setter
    def stop_it(self, val):
        if isinstance(val, bool):
            self._stop_it = val
        else:
            raise Exception('stop_it bool expected')

    def __str__(self):
        return self._name

    def start(self):
        self._start_it = True
        self._stop_it = False

    def stop(self):
        self._start_it = False
        self._stop_it = True


class Jarvis_Satellite_Server(CommunicationServer):
    logger = logging.getLogger('Jarvis_Satellite_Server')
    logger.setLevel(logging.INFO)

    def __init__(self, name:str ='root', ip:str ='127.0.0.1', port:int = 8585):
        super().__init__(name, ip, port)
        self._miners = []

    @property
    def miners(self):
        return self._miners

    def stop_miners(self, bcod_reaction = False, bot=None):
        info = Jarvis_Satellite_Server.logger.info
        for miner in self.miners:
            if miner.runned:
                miner.stop()
                if bcod_reaction and not miner.bcod_reaction:
                    miner.bcod_reaction = True
                    info(f"miner {miner.name} (bcod_reaction = {bcod_reaction}) is runned. Let's stop it.")
                    if bot is not None:
                        for user in bot.get_users():
                            if user.level <= 0:
                                bot.add_to_queue(user.id, f'Выключил miner "{miner.name}"\n')

    def start_miners(self, bcod_reaction = False, bot=None):
        info = Jarvis_Satellite_Server.logger.info
        for miner in self.miners:
            if not miner.runned:
                if not bcod_reaction or bcod_reaction and miner.bcod_reaction:
                    miner.start()
                    miner.bcod_reaction = False
                    info(f"miner {miner.name} (bcod_reaction = {bcod_reaction}) is not runned. Let's start it.")
                    if bot is not None:
                        for user in bot.get_users():
                            if user.level <= 0:
                                bot.add_to_queue(user.id, f'Включил miner "{miner.name}"\n')

    def _find_miner(self, miner):
        for m in self._miners:
            if isinstance(miner, Miner):
                if m.name == miner.name:
                    return m
            elif isinstance(miner, str):
                if m.name == miner:
                    return m
        return None

    def add_miner(self, name):
        if self._find_miner(name) is None:
            self._miners.append(Miner(name))

    def handler(self, client, data):
        debug = Jarvis_Satellite_Server.logger.debug
        info = Jarvis_Satellite_Server.logger.info
        answer = 'None'
        data = data.split(':')
        if len(data) != 2:
            return None
        name = data[0]
        message = data[1]
        debug(f'get "{message}" from {name}')
        if message == 'ping':
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