import tornado.ioloop, os
import tornado.web
import argparse, yaml
from tornado import httpclient
from mako import exceptions
from mako.lookup import TemplateLookup




############ Configuration parsing
oParser = argparse.ArgumentParser(description='Python drone : monitor your applications')
oParser.add_argument('--conf', help='Configuraton file path')
oArguments = oParser.parse_args()

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
print(vars(oConfiguration))
exit()

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
    tornado.ioloop.IOLoop.instance().start()
