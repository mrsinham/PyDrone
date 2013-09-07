import argparse, logging, os, yaml
from PyDrone.Probe import Probe, ProbeBuilder,ProbeLauncher
from PyDrone.Web import WebLauncher
from PyDrone.Event import ProbeEvent
from PyDrone.Monitor import Scheduler


class PyDrone:
    def __init__(self):
        self.sRootPath = os.path.dirname(__file__)
        self.oConfiguration = None
        self.aListOfProbes = None
        self.oProbeEvent = ProbeEvent()

    def __parseCmdLine(self, sLoggingFormat):
        oParser = argparse.ArgumentParser(description='Python drone : monitor your applications')
        oParser.add_argument('--conf', help='Configuraton file path')
        oArguments = oParser.parse_args()
        logging.basicConfig(level=logging.INFO, format=sLoggingFormat)
        if oArguments.conf is None:
            oParser.print_help()
            exit(1)
        if not os.path.isfile(oArguments.conf):
            print "Cant find the configuration file\n"
            oParser.print_help()
            exit(1)
        else:
            sConfigurationFile = oArguments.conf
        return sConfigurationFile

    def __startWebServer(self):
        oWebLauncher = WebLauncher(self.sRootPath, self.oConfiguration, self.aListOfProbes, self.oProbeEvent)
        oWebLauncher.start()

    def __startMonitor(self):
        self.oScheduler = Scheduler('MainScheduler', self.aListOfProbes, self.oProbeEvent)
        self.oScheduler.start()

    def start(self):
        sLoggingFormat = '%(asctime)-15s %(message)s'
        sConfigurationFile = self.__parseCmdLine(sLoggingFormat)
        oStream = file(sConfigurationFile, 'r')
        self.oConfiguration = yaml.load(oStream)

        oProbeBuilder = ProbeBuilder()
        self.aListOfProbes = oProbeBuilder.buildProbesFromConfiguration(self.oConfiguration)
        self.__startMonitor()
        try:
            self.__startWebServer()
        except (__builtins__.Exception, __builtins__.KeyboardInterrupt, __builtins__.SystemExit) as e:
            logging.error(e.message)
            logging.info('Shutdown server')
            self.oScheduler.stop()

__author__ = 'Julien Lefevre'

if __name__ == '__main__':
    oPyDrone = PyDrone()
    oPyDrone.start()