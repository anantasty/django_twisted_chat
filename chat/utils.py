import uuid
import datetime
import re

from redis import Redis

from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse

from chat.models import ChatUser
from chat import constants


def get_redis_conn():
    return Redis(host='localhost', db=1)


def create_user_invite_link(user):
    uid = uuid.uuid1().hex
    redis = get_redis_conn()
    redis.hmset('InviteHash:{}'.format(uid),
                     {'username': user.username, 'attempts': 0,
                      'created_at': datetime.datetime.now().isoformat(),
                      'user_pk': user.pk})
    return uid


def user_invite_handler(user, request):
    invite_hash = create_user_invite_link(user)
    subject = '{}! Invitation to sign up for flazchat.com'.format(
        user.first_name)
    url = request.build_absolute_uri(reverse('invite_accept',
                                             kwargs={'uid': invite_hash}))
    message = "{} You have been invited to sign up for..{}".format(
        user.first_name, url)
    from_email = user.referral_user.email or settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [user.email])


def quick_user_invite_handler(invitee_email, referal_email, request):
    subject = 'Invitation to sign up for flazchat.com'
    url = request.build_absolute_uri(reverse('register'))
    message = "You have been invited to sign up for..{}".format(url)
    from_email = referal_email or settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [invitee_email])


def send_user_invite_email(email, chat, invite_hash, request):
    name = chat.created_by.username or chat.created_by.email
    subject = '{} invited you to chat on {} at Flazchat.com'.format(name,
                                                                    chat.name)
    url = request.build_absolute_uri(reverse('join_chat',
                                             kwargs={'uid': invite_hash}))
    message = ('{} invited you to join the chat {} from {} to {}'
               'click the following link to join the chat {}'.format(
                   name, chat.name, chat.start_time, chat.end_time, url))
    from_email = chat.created_by.email or settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [email])


def quick_create_users(emails, creating_user):
    users = []
    for email in emails:
        user = ChatUser(email=email, username=email)
        user.referral_user = creating_user
        user.save()
        users.append(user)
    return users

def set_password(uid, password):
    redis = get_redis_conn()
    username = redis.hget(uid, 'username')
    redis.hincrby(uid, 'attempts')
    user = ChatUser.objects.get(username=username)
    user.set_password(password)
    user.save(
)


def validate_email(email):
    if len(email) > 7:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
            return True
    return False



def invite_users(chat, users, request):
    redis = get_redis_conn()
    for user in users:
        invite_hash = create_user_invite_link(user)
        redis.hmset(constants.USER_INVITE_HASH.format(invite_hash),
            {'user': user.pk,
             'chat': chat.pk,
             'chat_start': chat.start_time,
             'chat_end': chat.end_time})
        send_user_invite_email(user.email, chat, invite_hash,
                               request)


def users_list_from_str(user_str, creating_user, new_only=False):
    invitees = user_str.split(',')
    users = ChatUser.objects.filter(username__in=invitees)
    not_found = set(invitees) - set([user.email for user in users])
    emails = [email for email in not_found if validate_email(email)]
    new_users = quick_create_users(emails, creating_user)
    if new_only:
        return new_users
    return list(users) + new_users
