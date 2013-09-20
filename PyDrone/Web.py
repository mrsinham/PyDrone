import os
from mako.lookup import TemplateLookup
from tornado import httpclient, websocket
from mako import exceptions
import tornado.web
import logging, json
import Event

class WebLauncher:

    defaultPort = 3498

    def __init__(self, sRootDir, aConfiguration, aListOfProbes, oEvent):
        assert isinstance(oEvent, Event.ProbeEvent)
        self.template_root = os.path.join(sRootDir, 'templates')
        self.aConfiguration = aConfiguration
        self.blacklist_templates = ('layouts',)
        self.oLogger = logging.getLogger('web')
        self.template_lookup = TemplateLookup(input_encoding='utf-8',
            output_encoding='utf-8',
            encoding_errors='replace',
            directories=[self.template_root])
        self.oApplication = tornado.web.Application(
            [
                ('/', MainHandler),
                ('/monitor', Monitor, dict(oWebEngine=self, aProbeList=aListOfProbes)),
                ('/socket', MonitorWebsocket, dict(oEvent=oEvent))
            ], static_path=os.path.join(sRootDir, 'static')
        )

    def getPort(self):
        if 'web' not in self.aConfiguration.keys():
            return WebLauncher.defaultPort
        if 'port' in self.aConfiguration['web'].keys() and isinstance(self.aConfiguration['web']['port'], int):
            return int(self.aConfiguration['web']['port'])



    def start(self):
        iPort = self.getPort()
        self.oLogger.info('started on port '+ str(iPort))
        self.oApplication.listen(iPort)
        tornado.ioloop.IOLoop.instance().start()

    def get_error_html(self, status_code, exception, **kwargs):
        if hasattr(exception, 'code'):
            self.set_status(exception.code)
            if exception.code == 500:
                return exceptions.html_error_template().render()
            return self.render_template(str(exception.code))
        return exceptions.html_error_template().render()

    def render_template(self, sFilename, **kwargs):
        if os.path.isdir(os.path.join(self.template_root, sFilename)):
            sFilename = os.path.join(sFilename, 'index.html')
        else:
            sFilename = '%s.html' % sFilename
        if any(sFilename.lstrip('/').startswith(p) for p in self.blacklist_templates):
            raise httpclient.HTTPError(404)
        try:
            return self.template_lookup.get_template(sFilename).render(**kwargs)
        except exceptions.TopLevelLookupException:
            raise httpclient.HTTPError(404)


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.redirect('/monitor')

class Monitor(tornado.web.RequestHandler):
    def initialize(self, oWebEngine, aProbeList):
        self.aProbeList = aProbeList
        assert isinstance(oWebEngine, WebLauncher)
        self.oWebEngine = oWebEngine
    def get(self):
        self.write(self.oWebEngine.render_template('monitor', aProbes=self.aProbeList))
    def get_error_html(self, status_code, exception, **kwargs):
        if hasattr(exception, 'code'):
            self.set_status(exception.code)
            if exception.code == 500:
                return exceptions.html_error_template().render()
            return self.oWebEngine.render_template(str(exception.code))
        return exceptions.html_error_template().render()

class MonitorWebsocket(tornado.websocket.WebSocketHandler):
    waiters = set()

    def initialize(self, oEvent):
        self.oLogger = logging.getLogger('web.websocket')
        self.oLogger.info('a websocket client has connected')
        self.oEvent = oEvent

        oEvent.addListener(self)

    def open(self):
        MonitorWebsocket.waiters.add(self)
        self.oLogger.debug('client connected. ('+self.getNbClientFormated()+')')
        self.sendClientNbUpdate()

    def getNbClient(self):
        return len(MonitorWebsocket.waiters)

    def getNbClientFormated(self):
        return str(len(MonitorWebsocket.waiters))+' currently connected'

    def sendClientNbUpdate(self):
        self.sendMessageToAllClients('nbClientUpdate', json.dumps({'nbClient':self.getNbClient()}))

    def on_close(self):
        MonitorWebsocket.waiters.remove(self)
        self.oEvent.removeListener(self)
        self.sendClientNbUpdate()
        self.oLogger.info('client leaves. ('+self.getNbClientFormated()+')')

    def sendMessageToAllClients(self, sType, sMessage):
        for oEachWaiters in MonitorWebsocket.waiters:
            try:
                oEachWaiters.writeMessageToClient(sType, sMessage)
            except __builtins__.Exception as e:
                print e
                logging.error('Unable to send message to clients');

    def writeMessageToClient(self, sType, sMessage):
        sFinalMsg = sType + '|||' + sMessage
        self.write_message(sFinalMsg)

    def sendUpdate(self, oProbe):
        self.sendMessageToAllClients('probeUpdate', str(oProbe))

    def on_message(self, sMessage):
        pass
