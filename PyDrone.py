import argparse, logging, os, yaml
from PyDrone.Probe import Probe, ProbeBuilder,ProbeMonitor
from PyDrone.Web import WebLauncher
from PyDrone.Event import ProbeEvent
from PyDrone.Monitor import Scheduler
from PyDrone.Notify import Mail as MailNotifier
import logging.handlers
import pprint


class PyDrone:
    def __init__(self):
        self.sRootPath = os.path.dirname(__file__)
        self.oConfiguration = None
        self.aListOfProbes = None
        self.oProbeEvent = ProbeEvent()


    def __parseCmdLine(self, sLoggingFormat):
        oParser = argparse.ArgumentParser(description='Python drone : monitor your applications')
        oParser.add_argument('--conf', help='Configuraton file path')
        oParser.add_argument('--debug', action="store_const", const=True, help='enable debug mode')
        oParser.add_argument('--log', help='log into file')
        oArguments = oParser.parse_args()
        #logging.basicConfig(level=logging.INFO, format=sLoggingFormat)

        if oArguments.conf is None:
            oParser.print_help()
            exit(1)
        if not os.path.isfile(oArguments.conf):
            print "Cant find the configuration file\n"
            oParser.print_help()
            exit(1)
        else:
            if oArguments.debug:
                logging.basicConfig(level=logging.DEBUG, format=sLoggingFormat)
            else:
                logging.basicConfig(level=logging.INFO, format=sLoggingFormat)

            self.oLogger = logging.getLogger('pydrone')
            if oArguments.log is not None:
                # log into file
                oFileHandler = logging.handlers.RotatingFileHandler(oArguments.log, maxBytes=20000, backupCount=20)
                oFileFormatter = logging.Formatter(sLoggingFormat)
                oFileHandler.setFormatter(oFileFormatter)
                self.oLogger.addHandler(oFileHandler)

            sConfigurationFile = oArguments.conf
            self.oLogger.debug('reading configuration file '+os.getcwd() + '/'+ sConfigurationFile)
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
        sLoggingFormat = '%(asctime)-15s - %(name)-20s - %(message)s - %(levelname)s'
        sConfigurationFile = self.__parseCmdLine(sLoggingFormat)
        self.oLogger.info('started')
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