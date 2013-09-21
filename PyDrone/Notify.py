from Probe import Probe
import threading
import logging
import smtplib
from email.mime.text import MIMEText
from pprint import pprint
import socket
import json


class BufferNotifier(threading.Thread):

    def __init__(self, aConfiguration):
        threading.Thread.__init__(self)
        self.aProbeUpdate = {}
        self.aConfiguration = aConfiguration
        self.sendEvery = 2
        self.oLogger = logging.getLogger('pydrone').getChild('notify')

        self._stopevent = threading.Event()

    def run(self):
        self.oLogger.info('started')
        self.parseConfiguration()
        while not self._stopevent.isSet():
            self.sendReport()
            self.aProbeUpdate = {}
            self._stopevent.wait(self.sendEvery)

    def stop(self):
        self.oLogger.info('stopping')
        self._stopevent.set()

    def sendUpdate(self, oProbe):
        """
        oProbe Is a Probe object
        Everytime a notification about probe comes up, it ends here
        This method will store the probe report until its sending by email
        """

        assert isinstance(oProbe, Probe)
        if oProbe.name not in self.aProbeUpdate.keys():
            self.aProbeUpdate[oProbe.name] = []
        self.aProbeUpdate[oProbe.name].append(self.transformProbeIntoReport(oProbe))

    def sendReport(self):
        pass

    def sendReport(self):
        """
        Sending report to the notified emails
        """

        if len(self.aProbeUpdate) is 0:
            return

        self.oLogger.info('pushing waiting reports')

        for sGroup, aGroupOfReport in self.aProbeUpdate.iteritems():
            self.pushGroupReport(sGroup, aGroupOfReport)

    def pushGroupReport(self, sGroup, aGroupOfReport):
        pass

    def transformProbeIntoReport(self, oProbe):
        assert isinstance(oProbe, Probe)
        aReport = {
            'lastCode': oProbe.lastCode,
            'server': oProbe.server,
            'lastMessage': oProbe.lastMessage,
            'lastChecked': oProbe.lastCheckFormated,
            'lastApplicationsOnFail': []
        }
        for oEachApp in oProbe.lastApplications:
            if oEachApp['code'] is not 200:
                sAppFailed = 'App. ' + oEachApp['name'] + ' had code ' + str(oEachApp['code']) + ' with message ' +oEachApp['response']
                if len(oEachApp['request']) > 0:
                    sAppFailed += ' and request was '+json.dumps(oEachApp['request'])
                aReport['lastApplicationsOnFail'].append(sAppFailed)
        return aReport

    def parseConfiguration(self):
        # probe part
        for sGroup, aGroupConfiguration in self.aConfiguration['probes'].iteritems():
            self.parseProbeNotifyConfiguration(sGroup, aGroupConfiguration)

    def parseProbeNotifyConfiguration(self, sGroupName, aGroupeConfiguration):
        pass

class Mail(BufferNotifier):
    def __init__(self, aConfiguration):
        super(Mail, self).__init__(aConfiguration)
        self.sFromEmailAddress = 'notify@pydrone.com'
        self._stopevent = threading.Event()
        self.bActive = True
        self.sWebSiteUrl = None
        self.sSmtpHost = 'localhost'
        self.iSmtpPort = 25
        self.sSmtpLogin = None
        self.sSmtpPass = None
        self.bSmtpUseSsl = False
        self.aToEmailPerGroup = {}
        self.sBaseUrl = None
        self.oLogger = self.oLogger.getChild('mail')

    def run(self):
        super(Mail, self).run()

    def parseConfiguration(self):
        """
        Extract from the configuration the configuration for the mail notifier
        """
        super(Mail, self).parseConfiguration()
        if 'mail' not in self.aConfiguration.keys():
            self.oLogger.info('"mail" section is not present in configuration')
            return False
        aMailConfiguration = self.aConfiguration['mail']
        aMailKeys = aMailConfiguration.keys()

        # where is the mail server
        if 'smtp' not in aMailKeys:
            self.sSmtpHost = 'localhost'
        else:
            self.sSmtpHost = aMailConfiguration['smtp']

        if 'smtp_port' in aMailKeys:
            self.iSmtpPort = aMailConfiguration['smtp_port']

        # smtp authentification
        if 'login' in aMailKeys:
            self.sSmtpLogin = aMailConfiguration['login']
        if 'password' in aMailKeys:
            self.sSmtpPass = aMailConfiguration['password']
        if 'ssl' in aMailKeys:
            self.bSmtpUseSsl = bool(aMailConfiguration['ssl'])

        # when to send it
        if 'sendEvery' in aMailKeys:
            self.sendEvery = aMailConfiguration['sendEvery']
            self.oLogger.debug('sending every '+str(self.sendEvery) + 's')

        # where is the main interface ?
        if 'web' in self.aConfiguration.keys():
            if 'host' in self.aConfiguration['web'].keys():
                self.sBaseUrl = 'http://' + self.aConfiguration['web']['host']
            else:
                self.sBaseUrl = 'http://' + socket.gethostname()
            if 'port' in self.aConfiguration['web'].keys() and self.aConfiguration['web']['port'] != 80:
                self.sBaseUrl += ':' + str(self.aConfiguration['web']['port'])

        if len(self.aToEmailPerGroup) is 0:
            self.oLogger.info('No mail to warn, no need for email notifier, stopping it')
            self.stop()

    def parseProbeNotifyConfiguration(self, sGroupName, aGroupConfiguration):
        if 'emailsToWarn' in aGroupConfiguration:
            if sGroupName not in self.aToEmailPerGroup:
                self.aToEmailPerGroup[sGroupName] = []
            self.aToEmailPerGroup[sGroupName].extend(aGroupConfiguration['emailsToWarn'])


    def pushGroupReport(self, sGroup, aGroupOfReport):
        if sGroup not in self.aToEmailPerGroup.keys():
            self.oLogger.info('update on group ' + sGroup + ' but no mail contact for it')
            return
        aEmail = self.aToEmailPerGroup[sGroup]
        sSubject = "PyDrone update on : " + sGroup
        sBody = ''
        for aReport in aGroupOfReport:
            sServerLine = aReport['lastChecked'] + ' : Server ' + aReport['server'] + ' switched to ' + str(
                aReport['lastCode']) + " and message " + aReport['lastMessage'] + "\n"
            if len(aReport['lastApplicationsOnFail']) is not 0:
                for sEachAppReport in aReport['lastApplicationsOnFail']:
                    sServerLine += '=> ' + sEachAppReport + "\n"

            sBody += sServerLine + "\n\n"
        if self.sBaseUrl is not None:
            sBody += "\n\n"
            sBody += 'More info at ' + self.sBaseUrl + "\n"
        aMessage = MIMEText(sBody)
        aMessage['Subject'] = sSubject
        aMessage['From'] = self.sFromEmailAddress
        #aMessage['To'] = aEmail
        sSmtpUrl = self.sSmtpHost + ':' + str(self.iSmtpPort)
        oSender = smtplib.SMTP(sSmtpUrl)
        if self.bSmtpUseSsl:
            oSender.starttls()
        if self.sSmtpLogin is not None and self.sSmtpPass is not None:
            oSender.login(self.sSmtpLogin, self.sSmtpPass)
        self.oLogger.info('Sending email for group : ' + sGroup)
        try:
            oSender.sendmail(self.sFromEmailAddress, aEmail, aMessage.as_string())
        except Exception as e:
            self.oLogger.error('Unable to send mail : ' + e.message)


class NMA(BufferNotifier):
    """
    Notify my Android notifications
    http://www.notifymyandroid.com/
    """
    def __init__(self, aConfiguration):
        super(NMA, self).__init__(aConfiguration)
        self.aNmaByGroup = {}
        self.oLogger = self.oLogger.getChild('nma')

    def run(self):
        try:
            import pynma
            self.oLogger.info('rezjrzejrze')
            super(NMA, self).run()
        except ImportError:
            self.oLogger.info('No nma module available, stopping')
            self.stop()

    def parseConfiguration(self):
        super(NMA, self).parseConfiguration()
        if len(self.aNmaByGroup) is 0:
            self.oLogger.info('No nma to warn, stopping')
            self.stop()
            exit(0)


    def parseProbeNotifyConfiguration(self, sGroupName, aGroupConfiguration):
        if 'nmaToWarn' in aGroupConfiguration:
            if sGroupName not in self.aNmaByGroup:
                self.aNmaByGroup[sGroupName] = []
            self.aNmaByGroup[sGroupName].extend(aGroupConfiguration['nmaToWarn'])


    def pushGroupReport(self, sGroup, aGroupOfReport):
        sApplication = 'PyDrone'
        sEvent = 'Change'
        sMessage = 'in '+sGroup+' :'

        for aEachReport in aGroupOfReport:
            sMessage += aEachReport['server']+' is '+str(aEachReport['lastCode']) + " - "

        aNmaToWarn = self.aNmaByGroup[sGroup]
        import pynma
        oNma = pynma.PyNMA(aNmaToWarn)
        oNma.push(sApplication, sEvent, sMessage)








