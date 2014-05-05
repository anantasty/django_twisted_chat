import hashlib

import rethinkdb as rdb

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from chat import mixins
from chat.models import ChatRoom
from chat.forms import (ChatUserForm, ChatUserInviteForm,
                        ChangePasswordForm, ChatRoomForm)
from chat import utils

rdb.connect('localhost',28015, db='chat').repl()

@login_required
def index(request):
    chat_rooms = ChatRoom.objects.order_by('name')[:5]
    context = {
        'chat_list': chat_rooms,
    }
    return render(request,'chats/index.html', context)

def generate_user_hash(chat, user):
    md5_hash = hashlib.md5()
    md5_hash.update('{}{}'.format(chat, user))
    return md5_hash.hexdigest()

def register_hash(user, md5_hash):
    pass


@login_required
def chat_room(request, chat_room_id):
    chat = get_object_or_404(ChatRoom, pk=chat_room_id)
    md5_hash = generate_user_hash(chat, request.user)
    register_hash(request.user, md5_hash)
    resp = render(request, 'chats/chat_room.html', {'chat': chat,
                                                    'user': request.user})
    resp.set_cookie('TEST', 'HELLO')
    return resp


@login_required
def longpoll_chat_room(request, chat_room_id):
    chat = get_object_or_404(ChatRoom, pk=chat_room_id)
    return render(request, 'chats/longpoll_chat_room.html', {'chat': chat})


class RegisterationView(FormView):
    template_name = 'chats/register.html'
    form_class = ChatUserForm
    success_url = 'chats/thanks/'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.score = 1
        user.save()
        utils.user_invite_handler(user, self.request)
        return super(RegisterationView, self).form_valid(form)


class UserInvitationView(mixins.LoginRequiredMixin, RegisterationView):
    form_class = ChatUserInviteForm

    def form_valid(self, form):
        user = form.save(commit=False)
        user.referral_user = self.request.user.chatuser
        user.save()
        utils.user_invite_handler(user, self.request)
        return super(RegisterationView, self).form_valid(form)


class InviteAcceptView(FormView):
    template_name = 'chats/register.html'
    form_class = ChangePasswordForm
    success_url = 'chats/thanks/'

    def form_valid(self, form):
        uid = self.kwargs.get('uid')
        utils.set_password(uid, form.cleaned_data.get('password1'))
        return super(InviteAcceptView, self).form_valid(form)


def thanks(request):
    render(request, 'chats/thanks.html')

class CreateRoom(FormView):
    template_name = 'chats/create_room.html'
    form_class = ChatRoomForm

    def form_valid(self, form):
        chat_room = form.save()
        url = reverse('chat_room', kwargs={'chat_room_id': chat_room.id})
        return HttpResponseRedirect(url)
