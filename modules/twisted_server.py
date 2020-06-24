from twisted.internet import protocol, reactor, endpoints
import random
import logging
from time import sleep

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s (%(levelname)s) %(asctime)s: %(message)s'
LOG_LEVEL = logging.DEBUG
# LOG_LEVEL = logging.INFO
# LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL,
                        datefmt='%d.%m.%y %H:%M:%S')
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')

info = logging.info
debug = logging.debug

class Echo(protocol.Protocol):
    def dataReceived(self, data):
        debug(data.decode())
        x = random.randint(60, 65)
        answer = f'cmd={x} {60} 0#'
        # sleep(0.1)
        debug(f'write {answer}')
        self.transport.write(answer.encode())

class EchoFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Echo()

endpoints.serverFromString(reactor, "tcp:8587").listen(EchoFactory())
reactor.run()