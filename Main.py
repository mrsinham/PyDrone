import tornado.ioloop, os
import tornado.web
import argparse, yaml, logging, threading
from time import sleep
from pprint import pprint
from tornado import httpclient
from mako import exceptions
from mako.lookup import TemplateLookup


############# Probe #################
class Probe:
	
	def __init__(self):
		self.name = None
		self.connectTimeout = None
		self.executionTimeout = None
		self.server = None
		self.lastCheck = None
		self.lastResult = None
		self.checkEvery = None # Check every, in sec
	
	def parseProbe(self, oProbe):
		pass

class ProbeBuilder:
	
	def buildProbesFromConfiguration(self, oConfiguration):
		if oConfiguration['probes'] == None:
			raise Exception("Unable to find the probes section")
		aProbes = []
		for sKey, oEachProbe in oConfiguration['probes'].iteritems():
			sProbeName = sKey
			assert isinstance(sProbeName, str)
			assert isinstance(oEachProbe['url'], str)
			assert isinstance(oEachProbe['connectTimeout'], int)
			assert isinstance(oEachProbe['executionTimeout'], int)
			assert isinstance(oEachProbe['checkEvery'], float)
			assert isinstance(oEachProbe['servers'], list)
			for sEachServer in oEachProbe['servers']:
				oProbe = Probe()
				oProbe.name = sProbeName
				oProbe.connectTimeout = oEachProbe['connectTimeout']
				oProbe.executionTimeout = oEachProbe['executionTimeout']
				oProbe.checkEvery = oEachProbe['checkEvery']
				oProbe.server = sEachServer
				aProbes.append(oProbe)
			print sKey
		return aProbes

####################### Scheduler 

class Scheduler(threading.Thread):
	def __init__(self, sName, aListOfProbes):
		threading.Thread.__init__(self)
                self.name = sName
                self.aListOfProbes = aListOfProbes
		self.bRunning = True
	def run(self):
		while self.bRunning:
			logging.info('logging in a thread')
			sleep(0.5)
	def stop(self):
		self.bRunning = False

	
############ Configuration parsing
oParser = argparse.ArgumentParser(description='Python drone : monitor your applications')
oParser.add_argument('--conf', help='Configuraton file path')
oArguments = oParser.parse_args()

logging.basicConfig(level=logging.INFO)

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

oScheduler = Scheduler('Main', aListOfProbes)
oScheduler.start()

############" Start of web server

root = os.path.dirname(__file__)
template_root = os.path.join(root, 'templates')
blacklist_templates = ('layouts',)

template_lookup = TemplateLookup(input_encoding='utf-8',
    output_encoding='utf-8',
    encoding_errors='replace',
    directories=[template_root])

def render_template(filename):
    if os.path.isdir(os.path.join(template_root, filename)):
        filename = os.path.join(filename, 'index.html')
    else:
        filename = '%s.html' % filename
    if any(filename.lstrip('/').startswith(p) for p in blacklist_templates):
        raise httpclient.HTTPError(404)
    try:
        return template_lookup.get_template(filename).render()
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
    def get(self):
        self.write(render_template('monitor'))


oApplication = tornado.web.Application(
    [
        ('/', MainHandler),
        ('/monitor', Monitor)
    ], static_path=os.path.join(root, 'static')
)


if __name__ == '__main__':
    oApplication.listen(3498)
    try:
        tornado.ioloop.IOLoop.instance().start()
    except (KeyboardInterrupt, SystemExit):
	oScheduler.stop()
