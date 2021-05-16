import serial
import serial.tools.list_ports as lp
import logging

class COM_port:
    logger = logging.getLogger('COM_port')
    def __init__(self, name, PID, speed, timeout):
        self.name = name
        self.PID = PID
        self._speed = speed
        self._timeout = timeout
        self.initialized = False
        self.serial = None
        self.inicialize_com_port()

    def inicialize_com_port(self):
        if not self.initialized:
            try:
                self.serial.close()
            except:
                pass
            _ports = list(lp.comports())
            for _port in _ports:
                if _port.hwid.find(self.PID) > 0:
                    try:
                        self.serial = serial.Serial(_port.device, self._speed, timeout=self._timeout)
                        self.serial.write_timeout = 1
                        self.initialized = True
                        self.logger.info(f'COM-port {self.name} initialized in the port {_port.device} ({_port.description})')
                    except:
                        self.logger.error(f'Error initialize {self.name} in the port {_port.device} ({_port.description})')
            if not self.initialized:
                self.logger.critical(f'{self.name} initialize error!!! PID {self.PID} does not exist')
                raise Exception(f'{self.name} initialize error!!! PID {self.PID} does not exist')