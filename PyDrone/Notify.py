from Probe import Probe
import threading
import logging
import smtplib
from email.mime.text import MIMEText
from pprint import pprint

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
        self.__parseConfiguration()

    def run(self):
        logging.info('Starting email notifier')
        while not self._stopevent.isSet():
            self.sendReport()
            self.aProbeUpdate = {}
            self._stopevent.wait(self.sendEvery)

    def stop(self):
        logging.info('Stopping email notifier')
        self._stopevent.set()

    def __parseConfiguration(self):

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
        pprint(self.aToEmailPerGroup)


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
            logging.info('[EMAIL] Nothing to push')
            return


        for sGroup, aGroupOfReport in self.aProbeUpdate.iteritems():

            logging.info('parsing  probe')
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


            aMessage = MIMEText(sBody)
            aMessage['Subject'] = sSubject
            aMessage['From'] = self.sFromEmailAddress
            #aMessage['To'] = aEmail

            sSmtpUrl = self.sSmtpHost + ':' + str(self.iSmtpPort)
            logging.info(sSmtpUrl)
            oSender = smtplib.SMTP(sSmtpUrl)
            if self.bSmtpUseSsl:
                oSender.starttls()

            if self.sSmtpLogin is not None and self.sSmtpPass is not None:
                oSender.login(self.sSmtpLogin, self.sSmtpPass)
            logging.info('Sending email')

            pprint(self.sFromEmailAddress)
            pprint(aEmail)
            pprint(aMessage.as_string())
            oSender.sendmail(self.sFromEmailAddress, aEmail, aMessage.as_string())


    def transformProbeIntoReport(self, oProbe):
        assert isinstance(oProbe, Probe)
        aReport = {'lastCode': oProbe.lastCode, 'server': oProbe.server}
        return aReport



