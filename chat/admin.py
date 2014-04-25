from django.contrib import admin
from chat.models import ChatRoom
from chat.models import ChatUser

admin.site.register(ChatRoom)
admin.site.register(ChatUser)
