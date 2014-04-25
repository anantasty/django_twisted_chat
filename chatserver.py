import os

import rethinkdb as r

from twisted.application import service, internet
from twisted.internet import reactor

from twisted.web import wsgi
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.websockets import WebSocketsResource, lookupProtocolForFactory

from twisted_chat.factories import ChatFactory
from twisted_chat.resources import HttpChat, StaticFileScanner
from twisted_chat.wsgi import WsgiRoot
from twisted.python.threadpool import ThreadPool

from django.core.handlers.wsgi import WSGIHandler



shared_messages = {}

rethink = r.connect(host='localhost', port=28015)
if 'chat' not in rethink.db_list().run():
    rethink.db_create('chat').run()
resource = HttpChat(shared_messages)
factory = Site(resource)
ws_resource = WebSocketsResource(lookupProtocolForFactory(resource.wsFactory))

root = Resource()
root.putChild("",resource) #the http protocol is up at /
root.putChild("ws",ws_resource) #the websocket protocol is at /ws

application = service.Application("chatserver")
print "starting chat server"
internet.TCPServer(1025, Site(root)).setServiceParent(application)
print "chat server startedf"

#serving django over wsgi
# Create and start a thread pool,
wsgiThreadPool = ThreadPool()
wsgiThreadPool.start()

django_application = WSGIHandler()
django_resource = wsgi.WSGIResource(reactor, wsgiThreadPool, django_application)

django_root = WsgiRoot(django_resource)
project_dir = os.getcwd()
django_root.putChild('static', StaticFileScanner(project_dir + "/chat/static", project_dir + "/django_twisted_chat/static"))
print "Starting django"
internet.TCPServer(8000, Site(django_root)).setServiceParent(application)
