import logging

###################### Event
class ProbeEvent:

    def __init__(self):
        self.aListener = set()

    def addListener(self, oListener):
        self.aListener.add(oListener)

    def removeListener(self, oListener):
        self.aListener.remove(oListener)

    def pushProbeEvent(self, oProbe):
        for oEachListener in self.aListener:
            logging.info('push to listener')
            oEachListener.sendUpdate(oProbe)