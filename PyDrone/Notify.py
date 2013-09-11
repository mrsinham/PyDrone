from Probe import Probe
import threading
import logging
import smtplib
from email.mime.text import MIMEText
from pprint import pprint
import socket

class Mail(threading.Thread):

    def __init__(self, aConfiguration):
        threading.Thread.__init__(self)
        self.aProbeUpdate = {}
        self.aConfiguration = aConfiguration
        self.sendEvery = 5
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
        self.__parseConfiguration()



    def run(self):
        logging.info('Starting email notifier')
        if len(self.aToEmailPerGroup) is 0:
            logging.info('No mail to warn, no need for email notifier, stopping it')
            self.stop()

        while not self._stopevent.isSet():
            self.sendReport()
            self.aProbeUpdate = {}
            self._stopevent.wait(self.sendEvery)

    def stop(self):
        logging.info('Stopping email notifier')
        self._stopevent.set()

    def __parseConfiguration(self):
        """
        Extract from the configuration the configuration for the mail notifier
        """
        if 'mail' not in self.aConfiguration.keys():
            logging.info('"mail" section is not present in configuration')
            return False
        aMailConfiguration = self.aConfiguration['mail']
        aMailKeys = aMailConfiguration.keys()
        if 'smtp' not in aMailKeys:
            self.sSmtpHost = 'localhost'
        else:
            self.sSmtpHost = aMailConfiguration['smtp']

        if 'smtp_port' in aMailKeys:
            self.iSmtpPort = aMailConfiguration['smtp_port']
        if 'login' in aMailKeys:
            self.sSmtpLogin = aMailConfiguration['login']
        if 'password' in aMailKeys:
            self.sSmtpPass = aMailConfiguration['password']
        if 'ssl' in aMailKeys:
            self.bSmtpUseSsl = bool(aMailConfiguration['ssl'])
        # probe part
        for sGroup, aGroupConfiguration in self.aConfiguration['probes'].iteritems():
            if 'emailsToWarn' in aGroupConfiguration:
                if sGroup not in self.aToEmailPerGroup:
                    self.aToEmailPerGroup[sGroup] = []
                self.aToEmailPerGroup[sGroup].extend(aGroupConfiguration['emailsToWarn'])

        if 'web' in self.aConfiguration.keys():
            if 'host' in self.aConfiguration['web'].keys():
                self.sBaseUrl = 'http://'+ self.aConfiguration['web']['host']
            else:
                self.sBaseUrl =  'http://'+socket.gethostname()
            if 'port' in self.aConfiguration['web'].keys() and self.aConfiguration['web']['port'] != 80:
                self.sBaseUrl += ':'+str(self.aConfiguration['web']['port'])


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
        """
        Sending report to the notified emails
        """

        if len(self.aProbeUpdate) is 0:
            return

        logging.info('[email] pushing waiting mails')

        for sGroup, aGroupOfReport in self.aProbeUpdate.iteritems():


            if sGroup not in self.aToEmailPerGroup.keys():
                logging.info('Update on group '+sGroup+ ' but no mail contact for it')
                continue
            aEmail = self.aToEmailPerGroup[sGroup]

            sSubject = "PyDrone report"
            sBody = ''
            sBody += 'For the group '+sGroup+"\n"
            for aReport in aGroupOfReport:
                sServerLine = 'Server '+aReport['server']+ ' switched to '+str(aReport['lastCode'])+"\n"
                sBody += sServerLine


            if self.sBaseUrl is not None:
                sBody += "\n\n"
                sBody += 'More info at '+self.sBaseUrl+"\n"

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
            logging.info('Sending email for group : '+sGroup)
            oSender.sendmail(self.sFromEmailAddress, aEmail, aMessage.as_string())


    def transformProbeIntoReport(self, oProbe):
        assert isinstance(oProbe, Probe)
        aReport = {'lastCode': oProbe.lastCode, 'server': oProbe.server}
        return aReport



