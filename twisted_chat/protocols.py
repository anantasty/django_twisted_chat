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

    def _handle_likes(self, message):
        ref_msg = self.factory.messages.get(message['ref'])
        ref_msg['likes'] = ref_msg.get('likes', 0) + 1
        message['data'] = {'likes': ref_msg['likes']}
        return message

    def command_handler(self, message):
        if not message.get('command'):
            return message
        if message.get('command') == 'like':
            message = self._handle_likes(message)
        return message

    def dataReceived(self, data):
        try:
            print "self is :{}".format(self.__dict__)
            obj = simplejson.loads(data)
            obj['id'] = str(uuid.uuid1())
            if not 'likes' in obj:
                obj['likes'] =0
            obj = self.command_handler(obj)
            self.factory.messages[obj['id']] = obj
            self.updateClients(obj)
        except Exception as e:
            raise

    def updateClients(self, data):
        for c in self.factory.clients:
            c.message(data)

    def message(self, message):
        print message
        self.transport.write(simplejson.dumps(message))
