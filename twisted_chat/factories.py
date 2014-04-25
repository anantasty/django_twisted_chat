import uuid

import rethinkdb as rethink
from redis import Redis

from twisted.internet.protocol import Factory

from twisted_chat.protocols import WebsocketChat


class ChatFactory(Factory):
    def __init__(self, *args, **kwargs):
        rethink.connect(host="localhost", port=28015, db="chat").repl()
        self.rethink = rethink
        self.redis = Redis(host='localhost', db=1)

    protocol = WebsocketChat
    clients = []
    messages = {}
    chat_id = str(uuid.uuid1())
