from Probe import Probe
import threading

class Mail(threading.Thread):

    def __init__(self, aConfiguration):
        self.aProbeUpdate = {}
        self.aConfiguration = aConfiguration

    def sendUpdate(self, oProbe):
        assert isinstance(oProbe, Probe)
        if oProbe.name not in self.aProbeUpdate.keys():
            self.aProbeUpdate[oProbe.name] = []
        self.aProbeUpdate[oProbe.name].append()

    def transformProbeIntoReport(self, oProbe):
        pass


