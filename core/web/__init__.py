import cherrypy
import core
from mako import exceptions
from mako.lookup import TemplateLookup
import os


def serve_template(name, **kwargs):
    try:
        loc = os.path.join(core.RUN_DIR, 'web/interfaces/')

        template = TemplateLookup(directories=[os.path.join(loc, 'html/')])

        return template.get_template(name).render(**kwargs)

    except Exception as e:
        #logger.error('%s' % exceptions.text_error_template())
        return exceptions.html_error_template().render()


class Root(object):
    def __init__(self, *args, **kwargs):
        pass

    @cherrypy.expose
    def index(self):
        return 'Hello you!'

    @cherrypy.expose
    def sql(self, query):
        """ xxx """

    @cherrypy.expose
    def restart(self):
        pass

    @cherrypy.expose
    def shutdown(self):
        shutdown()

    @cherrypy.expose
    def exit(self):
        os._exit()


def start():
    return cherrypy.quickstart(Root())


def shutdown():
    cherrypy.engine.exit()
