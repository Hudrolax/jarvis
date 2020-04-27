from serial import Serial, SerialException
from serial.serialutil import *


def detect_java_comm(names):
    """try given list of modules and return that imports"""
    for name in names:
        try:
            mod = my_import(name)
            mod.SerialPort
            return mod
        except (ImportError, AttributeError):
            pass
    raise ImportError("No Java Communications API implementation found")


# Java Communications API implementations
# http://mho.republika.pl/java/comm/

comm = detect_java_comm([
    'javax.comm',  # Sun/IBM
    'gnu.io',      # RXTX
])

def device(portnumber):
    """Turn a port number into a device name"""
    enum = comm.CommPortIdentifier.getPortIdentifiers()
    ports = []
    while enum.hasMoreElements():
        el = enum.nextElement()
        if el.getPortType() == comm.CommPortIdentifier.PORT_SERIAL:
            ports.append(el)
    return ports[portnumber].getName()

class JarvisSerial(Serial):
     def open(self):
        """\
        Open port with current settings. This may throw a SerialException
        if the port cannot be opened.
        """
        if self._port is None:
            raise SerialException("Port must be configured before it can be used.")
        if self.is_open:
            raise SerialException("Port is already open.")
        if type(self._port) == type(''):      # strings are taken directly
            portId = comm.CommPortIdentifier.getPortIdentifier(self._port)
        else:
            portId = comm.CommPortIdentifier.getPortIdentifier(device(self._port))     # numbers are transformed to a comport id obj
        try:
            self.sPort = portId.open("python serial module", 10)
        except Exception as msg:
            self.sPort = None
            raise SerialException("Could not open port: %s" % msg)
        # self._reconfigurePort()
        self._instream = self.sPort.getInputStream()
        self._outstream = self.sPort.getOutputStream()
        self.is_open = True