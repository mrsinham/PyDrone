from urlparse import urlparse, urlunparse
import urllib2
import json
from time import time
import datetime
import logging
import base64

############# Probe #################
class Probe:
    def __init__(self):
        self.id = None
        self.name = None
        self.timeout = None
        self.executionTimeout = None
        self.server = None
        self.lastCheck = None
        self.lastCheckFormated = None
        self.lastCode = None
        self.lastMessage = None
        self.checkEvery = None # Check every, in sec
        self.lastContent = None
        self.lastApplications = []
        self.lastEnv = []
        self.running = False
        self.emailsToWarn = []
        self.login = None
        self.password = None

    def __str__(self):
        aDict = {
            'id': self.id,
            'name': self.name,
            'server': self.server,
            'lastCheck': self.lastCheck,
            'lastCheckFormated': self.lastCheckFormated,
            'lastCode': self.lastCode,
            'lastMessage': self.lastMessage,
            'lastApplications': self.lastApplications,
            'lastEnv': self.lastEnv
        }
        return json.dumps(aDict)

    def resetApplications(self):
        self.lastApplications = []

    def resetEnv(self):
        self.lastEnv = []

    def addApplication(self, iApplicationCode, sApplicationName, sApplicationResponse, aRequest={}):
        aApplication = {
            'code': iApplicationCode,
            'name': sApplicationName,
            'response': sApplicationResponse,
            'request': aRequest
        }
        self.lastApplications.append(aApplication)

    def addEnvironment(self, sEnvName, mEnvValue):
        aEnv = {'name': sEnvName, 'value': mEnvValue}
        self.lastEnv.append(aEnv)


class ProbeBuilder:
    def __init__(self):
        self.iCurrentId = 0

    def buildProbesFromConfiguration(self, oConfiguration):
        self.iCurrentId = 0
        if oConfiguration['probes'] is None:
            raise Exception("Unable to find the probes section")
        aProbes = {}
        for sKey, oEachProbe in oConfiguration['probes'].iteritems():
            sProbeName = sKey
            if sKey not in aProbes.keys():
                aProbes[sKey] = []
            assert isinstance(sProbeName, str)
            assert isinstance(oEachProbe['url'], str)
            assert isinstance(oEachProbe['checkEvery'], float)
            assert isinstance(oEachProbe['servers'], list)

            for sEachServer in oEachProbe['servers']:
                oProbe = Probe()
                oProbe.id = self.iCurrentId
                oProbe.name = sProbeName
                oProbe.url = oEachProbe['url']
                aProbeKeys = oEachProbe.keys()
                if 'timeout' in aProbeKeys:
                    oProbe.timeout = oEachProbe['timeout']
                if 'login' in aProbeKeys:
                    oProbe.login = oEachProbe['login']
                if 'password' in aProbeKeys:
                    oProbe.password = oEachProbe['password']

                oProbe.checkEvery = oEachProbe['checkEvery']
                oProbe.server = sEachServer
                aProbes[sKey].append(oProbe)
                self.iCurrentId += 1
        return aProbes


class ProbeMonitor:
    def __init__(self, oProbeEvent):
        self.oProbeEvent = oProbeEvent
        self.oLogger = logging.getLogger('pydrone.probe.monitor')

    def sendProbe(self, oProbe):
        assert isinstance(oProbe, Probe)
        oProbe.running = True
        # We have a probe now we build the url to call
        oUrl = urlparse(oProbe.url)
        sNewUrl = urlunparse((oUrl.scheme, oProbe.server, oUrl.path, '', oUrl.query, oUrl.fragment))

        oNewHttpRequest = urllib2.Request(sNewUrl, None, {'Host': oUrl.netloc})
        if oProbe.login is not None and oProbe.password is not None:
            base64string = base64.encodestring('%s:%s' % (oProbe.login, oProbe.password)).replace('\n', '')
            oNewHttpRequest.add_header("Authorization", "Basic %s" % base64string)
        iPreviousCode = oProbe.lastCode
        try:
            if oProbe.timeout is not None:
                iTimeout = oProbe.timeout
            else:
                iTimeout = 5
            oResponse = urllib2.urlopen(oNewHttpRequest, timeout=iTimeout)
            oProbe.lastContent = oResponse
            try:
                oProbeResult = json.load(oResponse)
                self.receiveProbe(oProbeResult, oProbe)
            except ValueError as e:
                self.oLogger.warning('No json info, skipping parsing')
        except urllib2.HTTPError as e:
            oProbe.lastCode = e.code
            oProbe.lastMessage = e.reason
        except urllib2.URLError as e:
            oProbe.lastCode = 500
            oProbe.lastMessage = e.reason
        oProbe.lastCheck = time()

        oProbe.lastCheckFormated = datetime.datetime.fromtimestamp(oProbe.lastCheck).strftime('%d-%m-%Y %H:%M:%S')
        oProbe.running = False
        self.oLogger.debug(
            'checking ' + oProbe.server + ' from group : ' + oProbe.name + ' and got ' + str(oProbe.lastCode))
        if iPreviousCode is not None and oProbe.lastCode != iPreviousCode:
            # push probe to the event handler
            self.oLogger.info('['+oProbe.name+'] '+oProbe.server + ' change of code from ' + str(iPreviousCode) + ' to ' + str(oProbe.lastCode))
            self.oProbeEvent.pushProbeEvent(oProbe)


    def receiveProbe(self, oProbeResult, oProbe):
        assert isinstance(oProbe, Probe)
        oProbe.resetApplications()
        oProbe.resetEnv()
        aKeys = oProbeResult.keys()
        if 'code' not in aKeys:
            raise Exception('Unable to find code in json return')
        oProbe.lastCode = oProbeResult['code']
        if 'response' not in aKeys:
            raise Exception('Unable to find response in json return')
        oProbe.lastMessage = oProbeResult['response']

        if 'applications' in aKeys:
            aApplications = oProbeResult['applications']
            for aEachApp in oProbeResult['applications']:
                aAppKeys = aEachApp.keys()
                if 'code' in aAppKeys and 'name' in aAppKeys and 'response' in aAppKeys:
                    if 'request' in aAppKeys:
                        aRequest = aEachApp['request']
                    else:
                        aRequest = {}
                    oProbe.addApplication(aEachApp['code'], aEachApp['name'], aEachApp['response'], aRequest)
        if 'environment' in aKeys:
            aEnv = oProbeResult['environment']
            for sEnvName, mValue in aEnv.iteritems():
                oProbe.addEnvironment(sEnvName, mValue)
