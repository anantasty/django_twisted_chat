import hashlib
import datetime

from redis import Redis

from django.shortcuts import render, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import FormView
from django.views.generic import View
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q
from django.utils import simplejson

from chat import mixins
from chat import constants
from chat.models import ChatRoom, ChatUser
from chat.forms import (ChatUserForm, ChatUserInviteForm,
                        ChangePasswordForm, ChatRoomForm, InviteToChatForm)
from chat import utils


redis = Redis('localhost', db=2)

@login_required
def index(request):
    invited_rooms = redis.smembers(constants.USER_INVITED_TO.format(
        request.user.pk))
    chat_rooms = ChatRoom.objects.filter(
        Q(pk__in=invited_rooms) | Q(created_by=request.user) | Q(public=True),
        end_time__gt=datetime.datetime.now()).order_by('name')[:5]
    context = {
        'chat_list': chat_rooms,
    }
    return render(request,'chats/index.html', context)

def _generate_user_hash(chat, user):
    md5_hash = hashlib.md5()
    md5_hash.update('{}{}'.format(chat, user))
    return md5_hash.hexdigest()

def _register_hash(user, md5_hash, chat):
    redis.lpush(constants.USER_KEY.format(user.username), md5_hash)
    redis.ltrim(constants.USER_KEY.format(user.username), 0, 10)
    redis.hmset(constants.USER_HASH_KEY.format(md5_hash), {'user':user.username,
                                                           'chat': chat.pk})


@login_required
def chat_room(request, chat_room_id):
    chat = get_object_or_404(ChatRoom, pk=chat_room_id)
    md5_hash = _generate_user_hash(chat, request.user)
    _register_hash(request.user, md5_hash, chat)
    resp = render(request, 'chats/chat_room.html', {'chat': chat,
                                                    'user': request.user})
    resp.set_cookie('user_hash', md5_hash)
    return resp


@login_required
def longpoll_chat_room(request, chat_room_id):
    chat = get_object_or_404(ChatRoom, pk=chat_room_id)
    return render(request, 'chats/longpoll_chat_room.html', {'chat': chat})


class RegisterationView(FormView):
    template_name = 'chats/register.html'
    form_class = ChatUserForm

    def get_success_url(self):
        return reverse('index')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.score = 1
        user.save()
        utils.user_invite_handler(user, self.request)
        invited_chats = redis.smembers(
            constants.EMAIL_INVITED_TO.format(user.email))
        for chat in invited_chats:
            redis.sadd(constants.CHAT_INVITED_USERS.format(chat),
                       user.pk)
            redis.sadd(constants.USER_INVITED_TO.format(user.pk), chat)
        return super(RegisterationView, self).form_valid(form)


class UserInvitationView(mixins.LoginRequiredMixin, RegisterationView):
    form_class = ChatUserInviteForm
    template_name = 'chats/invite.html'

    def get_success_url(self):
        return reverse('index')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.referral_user = self.request.user.chatuser
        user.save()
        utils.user_invite_handler(user, self.request)
        return HttpResponse('User has been invited')


class InviteAcceptView(FormView):
    template_name = 'chats/register.html'
    form_class = ChangePasswordForm

    def get_success_url(self):
        return reverse('index')

    def form_valid(self, form):
        uid = self.kwargs.get('uid')
        utils.set_password(uid, form.cleaned_data.get('password1'))
        return super(InviteAcceptView, self).form_valid(form)


def thanks(request):
    render(request, 'chats/thanks.html')


class CreateRoom(mixins.LoginRequiredMixin, FormView):
    template_name = 'chats/create_room.html'
    form_class = ChatRoomForm

    def form_valid(self, form):
        chat_room = form.save(commit=False)
        chat_room.created_by = self.request.user.chatuser
        if not chat_room.end_time:
            chat_room.end_time = datetime.datetime.now() + datetime.timedelta(
                days=7)
        chat_room.save()
        url = reverse('invite_to_chat', kwargs={'chat': chat_room.id})
        return HttpResponseRedirect(url)


class ChatInviteView(mixins.LoginRequiredMixin, FormView):
    template_name = 'chats/invite_to_chat.html'
    form_class = InviteToChatForm

    def form_valid(self, form):
        users_list = utils.users_list_from_str(form.cleaned_data['users'])
        chat = ChatRoom.objects.get(pk=form.cleaned_data.get('chat'))
        utils.invite_users(chat, users_list, self.request)
        return HttpResponseRedirect(reverse('chat_room',
                                            kwargs={'chat_room_id': chat.pk}))

    def get_form(self, form_class):
        form = super(ChatInviteView, self).get_form(form_class)
        form.set_user(self.request.user)
        return form


class JoinChat(View):
    def get(self, request, uid=None):
        uid = self.kwargs.get('uid')
        invite_dict = redis.hgetall(constants.USER_INVITE_HASH.format(uid))
        user = ChatUser.objects.get(pk=invite_dict['user'])
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        url = reverse('chat_room', kwargs={'chat_room_id': invite_dict['chat']})
        return HttpResponseRedirect(url)


@login_required
def friends_autocomplete(request):
    user = request.user.chatuser
    query = request.GET.get('query')
    if query:
        matching_friends = user.friends.filter(Q(username__startswith=query) |
                                               Q(first_name__startswith=query) |
                                               Q(last_name__startswith=query) |
                                               Q(email__startswith=query))
    else:
        matching_friends = user.friends.all()
    friends_list = []
    for friend in matching_friends:
        name = '{} {}'.format(friend.first_name, friend.last_name) if \
          friend.first_name and friend.last_name else friend.email
        friends_list.append({'id': friend.id, 'label': name,
                             'value': friend.email})

    return HttpResponse(simplejson.dumps(friends_list),
                        mimetype='application/json')


class ChangePasswordView(mixins.LoginRequiredMixin, FormView):
    template_name = 'chats/change_password.html'
    form_class = ChangePasswordForm

    def form_valid(self, form):
        user = self.request.user
        user.set_password(form.cleaned_data.get('password1'))
        return HttpResponse('Password change successful.')
