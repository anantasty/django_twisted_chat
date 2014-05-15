import uuid
from collections import defaultdict

from redis import Redis

from twisted.internet.protocol import Factory

from twisted_chat.protocols import WebsocketChat


class ChatFactory(Factory):
    protocol = WebsocketChat

    def __init__(self, *args, **kwargs):
        self.redis = Redis(host='localhost', db=2)
        self.clients = []
        self.messages = {}
        self.chat_id = str(uuid.uuid1())
        self.client_map = defaultdict(list)
        self.likes_map =  defaultdict(set)
