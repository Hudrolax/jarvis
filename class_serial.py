from serial import Serial, SerialException
from serial.serialjava import *

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