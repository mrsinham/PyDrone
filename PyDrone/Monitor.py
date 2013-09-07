import logging, threading
from Probe import ProbeLauncher
from time import time

####################### Scheduler 

class Scheduler(threading.Thread):
    def __init__(self, sName, aListOfProbes, oProbeEvent):
        threading.Thread.__init__(self)
        self.name = sName
        self.oProbeEvent = oProbeEvent
        self.aListOfProbes = aListOfProbes
        self.bRunning = True
        self._stopevent = threading.Event()
    def run(self):
        while not self._stopevent.isSet():
            for sEachGroup in self.aListOfProbes.keys():
                for oEachProbe in self.aListOfProbes[sEachGroup]:
                    if False == oEachProbe.running  and (None == oEachProbe.lastCheck or (oEachProbe.lastCheck+oEachProbe.checkEvery) < time()):
                        oEngine = ProbeLauncher(self.oProbeEvent)
                        oEngine.sendProbe(oEachProbe)
            self._stopevent.wait(0.5)
    def stop(self):
        logging.info('stopping scheduler')
        self._stopevent.set()