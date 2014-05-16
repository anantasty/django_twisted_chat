import simplejson
import uuid

from twisted.protocols import basic

from chat import constants


class WebsocketChat(basic.LineReceiver):
    def connectionMade(self):
        self.message({'command': 'connected'})
        self.message({'msg': str(self.factory.client_map.keys()), 'likes': 0, 'command': None, 'user': 'anant1'})
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)
        del self.factory.client_map[self.user]

    def _handle_likes(self, message):
        ref = message['ref']
        user = message['user']
        likes_map_msg_key = 'Message:{}'.format(ref)
        likes_map_user_key = 'User:{}'.format(user)
        ref_msg = self.factory.messages.get(ref)
        likes_map = self.factory.likes_map
        if likes_map_msg_key in likes_map and \
          user in likes_map.get(likes_map_msg_key):
          return message
        ref_msg['likes'] = ref_msg.get('likes', 0) + 1
        message['data'] = {'likes': ref_msg['likes']}
        likes_map[likes_map_msg_key].add(user)
        likes_map[likes_map_user_key].add(ref)
        return message

    def _handle_connection_registeration(self, message):
        user = self.factory.redis.hget(constants.USER_HASH_KEY.format(
                message.get('user_hash')),
                               'user')
        self.factory.client_map[user] = self
        self.user = user

    def command_handler(self, message):
        if not message.get('command'):
            return message
        if message.get('command') == 'like':
            message = self._handle_likes(message)
        if message.get('command') == 'register_connection':
            self._handle_connection_registeration(message)
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
        except Exception:
            raise

    def updateClients(self, data):
        for c in self.factory.clients:
            c.message(data)

    def message(self, message):
        print message
        self.transport.write(simplejson.dumps(message))
