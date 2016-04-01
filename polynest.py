#!/usr/bin/python
""" Nest Node Server for Polyglot 
      by Einstein.42(James Milne)
      milne.james@gmail.com"""

from polyglot.nodeserver_api import SimpleNodeServer, PolyglotConnector
from polynest_types import NestControl

VERSION = "0.2.1"


class NestNodeServer(SimpleNodeServer):
    """ Sonos Node Server """
    controller = []
    thermostats = []

    def setup(self):
        manifest = self.config.get('manifest',{})
        self.controller = NestControl(self,'nestcontrol','Nest Control', True, manifest)
        self.poly.LOGGER.info("FROM Poly ISYVER: " + self.poly.isyver)
        self.controller._discover()
        self.update_config()
        
    def poll(self):
        pass

    def long_poll(self):
        if len(self.thermostats) >= 1:
            for i in self.thermostats:
                i.update_info()        
        pass
        
def main():
    # Setup connection, node server, and nodes
    poly = PolyglotConnector()
    # Override shortpoll and longpoll timers to 5/30, once per second in unnessesary 
    nserver = NestNodeServer(poly, 5, 30)
    poly.connect()
    poly.wait_for_config()
    poly.LOGGER.info("Nest Interface version " + VERSION + " created. Initiating setup.")
    nserver.setup()
    poly.LOGGER.info("Setup completed. Running Server.")
    nserver.run()
    
if __name__ == "__main__":
    main()
