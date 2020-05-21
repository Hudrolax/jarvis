from class_com import CommunicationServer
import logging

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s - %(levelname)s - %(message)s'
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL)
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

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

    @property
    def stop_it(self):
        return self._stop_it

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
        info(f'get "{message}" from {name}')
        if message == 'ping':
            answer = 'ok'
        elif message == 'miner':
            miner = self._find_miner(name)
            if miner is not None:
                if miner.start_it:
                    answer = 'start_miner'
                elif miner.stop_it:
                    answer = 'stop_miner'
        elif message == 'miner_is_runned':
            miner = self._find_miner(name)
            if miner is not None:
                debug('miner is runned')
                miner.runned = True
        elif message == 'miner_is_not_runned':
            miner = self._find_miner(name)
            if miner is not None:
                debug("miner is not runned")
                miner.runned = False

        return answer

if __name__ == '__main__':
    from time import sleep

    server = Jarvis_Satellite_Server(name='Jarvis')
    server.add_miner('serverx')

    server.start()

    while True:
        sleep(0.1)
    server.stop()