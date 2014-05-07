from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class ChatRoom(models.Model):
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey("ChatUser", null=True, blank=True)

    def __unicode__(self):
        return self.name


class ChatUser(User):
    user_intro = models.CharField(max_length=50)
    score = models.FloatField(validators=[MinValueValidator(1),
                                          MaxValueValidator(4)])
    referral_user = models.ForeignKey("ChatUser", null=True, blank=True)
    friends = models.ManyToManyField('ChatUser', null=True, blank=True,
                                     related_name='friends')

