import time
import simplejson
import uuid

from twisted.protocols import basic


class WebsocketChat(basic.LineReceiver):
    def connectionMade(self):
        print "Got new client!"
        self.transport.write('connected ....\n')
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        print "Lost a client!"
        self.factory.clients.remove(self)

    def dataReceived(self, data):
        try:
            obj = simplejson.loads(data)
            obj['id'] = str(uuid.uuid1())
            self.factory.messages[float(time.time())] = obj
            self.updateClients(obj)
        except:
            pass

    def updateClients(self, data):
        for c in self.factory.clients:
            c.message(data)

    def message(self, message):
        print message
        self.transport.write(simplejson.dumps(message))
