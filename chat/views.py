import hashlib

import rethinkdb as rdb

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import FormView
from django.core.mail import send_mail

from chat import mixins
from chat.models import ChatRoom
from chat.forms import ChatUserForm, ChatUserInviteForm

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
    register_hash(md5_hash)
    return render(request, 'chats/chat_room.html', {'chat': chat,
                                                    'user': request.user})

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
        return super(RegisterationView, self).form_valid(form)


class UserInvitationView(mixins.LoginRequiredMixin, RegisterationView):
    form_class = ChatUserInviteForm

    def form_valid(self, form):
        user = form.save(commit=False)
        user.referral_user = self.request.user
        user.save()
        subject = '{}! Invitation to sign up for hoops.com'.format(
            user.first_name)
        message = "{} {} You have been invited to sign up for..".format(
            'SITE_URL')
        from_email = user.referral_user.email or settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email, [user.email])
        return super(RegisterationView, self).form_valid(form)


def thanks(request):
    render(request, 'chats/thanks.html')
