import uuid
import datetime
import re

import rethinkdb as rethink
from redis import Redis

from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse

from chat.models import ChatUser


def get_rethink_conn():
    rethink.connect(host="localhost", port=28015, db="chat").repl()
    return rethink


def get_redis_conn():
    return Redis(host='localhost', db=1)


def create_user_invite_link(user):
    uid = uuid.uuid1().hex
    redis_pipe = get_redis_conn().pipeline()
    redis_pipe.hset(uid, 'username', user.username)
    redis_pipe.hset(uid, 'attempts', 0)
    redis_pipe.hset(uid, 'created_at', datetime.datetime.now().isoformat())
    redis_pipe.execute()
    return uid


def user_invite_handler(user, request):
    invite_hash = create_user_invite_link(user)
    subject = '{}! Invitation to sign up for hoops.com'.format(
        user.first_name)
    url = request.build_absolute_uri(reverse('invite_accept',
                                             kwargs={'uid': invite_hash}))
    message = "{} You have been invited to sign up for..{}".format(
        user.first_name, url)
    from_email = user.referral_user.email or settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [user.email])


def quick_user_invite_handler(invitee_email, referal_email, request):
    subject = 'Invitation to sign up for hoops.com'
    url = request.build_absolute_uri(reverse('register'))
    message = "You have been invited to sign up for..{}".format(url)
    from_email = referal_email or settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [invitee_email])


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
