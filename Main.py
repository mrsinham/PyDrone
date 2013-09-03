import tornado.ioloop, os
import tornado.web
import argparse, yaml, logging, threading, urllib2, urllib
import json
from time import sleep, time, ctime
from pprint import pprint
from tornado import httpclient, websocket
from mako import exceptions
from mako.lookup import TemplateLookup
from urlparse import urlparse, urlunparse, urljoin

############# Probe #################
class Probe:
	
	def __init__(self):
		self.id = None
		self.name = None
		self.connectTimeout = None
		self.executionTimeout = None
		self.server = None
		self.lastCheck = None
		self.lastCode = None
		self.lastMessage = None
		self.checkEvery = None # Check every, in sec
		self.lastApplications = []
		self.lastEnv = []
	
	def resetApplications(self):
		self.lastApplications = []

	def resetEnv(self):
		self.lastEnv = []
	def addApplication(self, iApplicationCode, sApplicationName, sApplicationResponse):
		aApplication = { 'code': iApplicationCode, 'name': sApplicationName, 'response': sApplicationResponse}
		self.lastApplications.append(aApplication)
	def addEnvironment(self, sEnvName, mEnvValue):
		aEnv = {'name':sEnvName, 'value':mEnvValue}
		self.lastEnv.append(aEnv)

class ProbeBuilder:
	
	def __init__(self):
		self.iCurrentId = 0

	def buildProbesFromConfiguration(self, oConfiguration):
		self.iCurrentId = 0
		if oConfiguration['probes'] == None:
			raise Exception("Unable to find the probes section")
		aProbes = {}
		for sKey, oEachProbe in oConfiguration['probes'].iteritems():
			sProbeName = sKey
			if sKey not in aProbes.keys():
				aProbes[sKey] = []
			assert isinstance(sProbeName, str)
			assert isinstance(oEachProbe['url'], str)
			assert isinstance(oEachProbe['connectTimeout'], int)
			assert isinstance(oEachProbe['executionTimeout'], int)
			assert isinstance(oEachProbe['checkEvery'], float)
			assert isinstance(oEachProbe['servers'], list)
			
			for sEachServer in oEachProbe['servers']:
				oProbe = Probe()
				oProbe.id = self.iCurrentId
				oProbe.name = sProbeName
				oProbe.url = oEachProbe['url']
				oProbe.connectTimeout = oEachProbe['connectTimeout']
				oProbe.executionTimeout = oEachProbe['executionTimeout']
				oProbe.checkEvery = oEachProbe['checkEvery']
				oProbe.server = sEachServer
				aProbes[sKey].append(oProbe)
				self.iCurrentId+=1
			print sKey
		return aProbes

class ProbeLauncher:

	def __init__(self, oProbeEvent):
		self.oProbeEvent = oProbeEvent

	def sendProbe(self, oProbe):
		assert isinstance(oProbe, Probe)
		# We have a probe now we build the url to call
		oUrl = urlparse(oProbe.url)
		oUrlDict = oUrl._asdict()
		sNewUrl = urlunparse((oUrl.scheme, oProbe.server, oUrl.path, '', oUrl.query, oUrl.fragment))
		oNewHttpRequest = urllib2.Request(sNewUrl, None, {'Host': oUrl.netloc})
		iPreviousCode = oProbe.lastCode
		try:
			oResponse = urllib2.urlopen(oNewHttpRequest)
			#sResponse = oResponse.read()
			oProbeResult = json.load(oResponse)
			self.receiveProbe(oProbeResult, oProbe)
		except urllib2.HTTPError as e:
			oProbe.lastCode = e.code
			oProbe.lastMessage = e.reason
		except urllib2.URLError as e:
			oProbe.lastCode = 500
			oProbe.lastMessage = e.reason
		oProbe.lastCheck = time()
		logging.info('Checking server : '+oProbe.server+ ' and got '+ str(oProbe.lastCode))
		if oProbe.lastCode != iPreviousCode:
			# push probe to the event handler
			self.oProbeEvent.pushProbeEvent(oProbe)
		#oUrl.netloc = oProbe.server
		#sUrlToCall = urljoin(oProbe.url, oUrl.scheme + '://' + oProbe.server)
		#sUrlToCall = oUrl.scheme + '://' + oProbe.server + oUrl.path 
		#print sUrlToCall


	def receiveProbe(self, oProbeResult, oProbe):
		oProbe.resetApplications()
		oProbe.resetEnv()
		assert isinstance(oProbe, Probe)
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
					oProbe.addApplication(aEachApp['code'], aEachApp['name'], aEachApp['response'])
		if 'environment' in aKeys:
			aEnv = oProbeResult['environment']
			for sEnvName, mValue in aEnv.iteritems():
				oProbe.addEnvironment(sEnvName, mValue)
		
###################### Event
class ProbeEvent:
	
	def __init__(self):
		self.aListener = []

	def addListener(self, oListener):
		self.aListener.append(oListener)

	def pushProbeEvent(self, oProbe):
		for oEachListener in self.aListener:
			oEachListener.sendUpdate(oProbe)


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
				logging.info('Monitoring probe group : '+ sEachGroup)
				for oEachProbe in self.aListOfProbes[sEachGroup]:
					oEngine = ProbeLauncher(self.oProbeEvent)
					oEngine.sendProbe(oEachProbe)
			self._stopevent.wait(10)
	def stop(self):
		logging.info('stopping scheduler')
		self._stopevent.set()

	
############ Configuration parsing
oParser = argparse.ArgumentParser(description='Python drone : monitor your applications')
oParser.add_argument('--conf', help='Configuraton file path')
oArguments = oParser.parse_args()

sLoggingFormat = '%(asctime)-15s %(message)s'
logging.basicConfig(level=logging.INFO, format=sLoggingFormat)

if oArguments.conf == None:
	oParser.print_help()
	exit(1)
if False == os.path.isfile(oArguments.conf):
	print "Cant find the configuration file\n"
	oParser.print_help()
	exit(1)
else:
	sConfigurationFile = oArguments.conf

oStream = file(sConfigurationFile, 'r')
oConfiguration = yaml.load(oStream)

oProbeBuilder = ProbeBuilder()
aListOfProbes = oProbeBuilder.buildProbesFromConfiguration(oConfiguration)

oEvent = ProbeEvent()

oScheduler = Scheduler('Main', aListOfProbes, oEvent)
oScheduler.start()


############" Start of web server

root = os.path.dirname(__file__)
template_root = os.path.join(root, 'templates')
blacklist_templates = ('layouts',)

template_lookup = TemplateLookup(input_encoding='utf-8',
    output_encoding='utf-8',
    encoding_errors='replace',
    directories=[template_root])

def render_template(filename, **kwargs):
    if os.path.isdir(os.path.join(template_root, filename)):
        filename = os.path.join(filename, 'index.html')
    else:
        filename = '%s.html' % filename
    if any(filename.lstrip('/').startswith(p) for p in blacklist_templates):
        raise httpclient.HTTPError(404)
    try:
        return template_lookup.get_template(filename).render(**kwargs)
    except exceptions.TopLevelLookupException:
        raise httpclient.HTTPError(404)

class DefaultHandler(tornado.web.RequestHandler):
    def get_error_html(self, status_code, exception, **kwargs):
        if hasattr(exception, 'code'):
            self.set_status(exception.code)
            if exception.code == 500:
                return exceptions.html_error_template().render()
            return render_template(str(exception.code))
        return exceptions.html_error_template().render()



class MainHandler(DefaultHandler):

    def get(self):
        self.redirect('/monitor')

class Monitor(tornado.web.RequestHandler):
	def initialize(self, aProbeList):
		self.aProbeList = aProbeList
	def get(self):
        	self.write(render_template('monitor', aProbes=self.aProbeList))

class MonitorWebsocket(tornado.websocket.WebSocketHandler):
	waiters = set()

	def initialize(self, oEvent):
		oEvent.addListener(self)

	def open(self):
		MonitorWebsocket.waiters.add(self)

	def on_close(self):
		MonitorWebsocket.waiters.remove(self)
	
	def transformProbeInfoMessage(self, oProbe):
		assert isinstance(oProbe, Probe)
		return ''
	
	def sendUpdate(oProbe):
		for oEachWaiters in waiters:
			try:
				oEachWaiters.write_message(self.transformProbeIntoMessage(oProbe))
			except:
				logging.error('Unable to send probe update')			

	def on_message(self, sMessage):
		pass

try:
	oApplication = tornado.web.Application(
    		[
        	('/', MainHandler),
        	('/monitor', Monitor, dict(aProbeList=aListOfProbes)),
		('/socket', MonitorWebsocket, dict(oEvent=oEvent))
    		], static_path=os.path.join(root, 'static')
	)

	if __name__ == '__main__':
    		oApplication.listen(3498)
        	tornado.ioloop.IOLoop.instance().start()
except (Exception, KeyboardInterrupt, SystemExit) as e:
	logging.info('shudown webserver')
	oScheduler.stop()
