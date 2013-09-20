import logging

###################### Event
class ProbeEvent:

    def __init__(self):
        self.aListener = set()
        self.oLogger = logging.getLogger('probe.event')

    def addListener(self, oListener):
        self.aListener.add(oListener)

    def removeListener(self, oListener):
        self.aListener.remove(oListener)

    def pushProbeEvent(self, oProbe):
        for oEachListener in self.aListener:
            self.oLogger.info('push to listener')
            oEachListener.sendUpdate(oProbe)