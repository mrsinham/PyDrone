import argparse, logging, os, yaml
from PyDrone.Probe import Probe, ProbeBuilder,ProbeMonitor
from PyDrone.Web import WebLauncher
from PyDrone.Event import ProbeEvent
from PyDrone.Monitor import Scheduler
from PyDrone.Notify import Mail as MailNotifier


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
        self.oLogger = logging.getLogger('pydrone')
        if oArguments.conf is None:
            oParser.print_help()
            exit(1)
        if not os.path.isfile(oArguments.conf):
            print "Cant find the configuration file\n"
            oParser.print_help()
            exit(1)
        else:
            sConfigurationFile = oArguments.conf
            self.oLogger.info('reading configuration file '+os.getcwd() + '/'+ sConfigurationFile)
            return sConfigurationFile

    def __startWebServer(self):
        oWebLauncher = WebLauncher(self.sRootPath, self.oConfiguration, self.aListOfProbes, self.oProbeEvent)
        oWebLauncher.start()

    def __startMonitor(self):
        self.oScheduler = Scheduler('MainScheduler', self.aListOfProbes, self.oProbeEvent)
        self.oScheduler.start()

    def __startMailNotifier(self):
        self.oMailNotifier = MailNotifier(self.oConfiguration)
        self.oProbeEvent.addListener(self.oMailNotifier)
        self.oMailNotifier.start()


    def start(self):
        sLoggingFormat = '%(asctime)-15s [%(name)s] %(message)s - %(levelname)s'
        sConfigurationFile = self.__parseCmdLine(sLoggingFormat)
        self.oLogger.info('starting')
        oStream = file(sConfigurationFile, 'r')
        self.oConfiguration = yaml.load(oStream)

        oProbeBuilder = ProbeBuilder()
        self.aListOfProbes = oProbeBuilder.buildProbesFromConfiguration(self.oConfiguration)
        self.__startMonitor()
        self.__startMailNotifier()
        try:
            self.__startWebServer()
        except (__builtins__.Exception, __builtins__.SystemExit) as e:
            self.oLogger.error(e)
        except KeyboardInterrupt as e:
            self.oLogger.info('user stopping')
        except SystemExit as e:
            self.oLogger.info('system says to halt')
        finally:
            self.oLogger.info('shutdown..')
            self.oScheduler.stop()
            self.oMailNotifier.stop()

__author__ = 'Julien Lefevre'

if __name__ == '__main__':
    oPyDrone = PyDrone()
    oPyDrone.start()