from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MinValueValidator, MaxValueValidator

from chat.models import ChatUser, ChatRoom


class ChatUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = ChatUser
        fields = ('username', 'email', 'password1',
                  'password2')
        exclude = ('user_intro', 'score')

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class ChatUserInviteForm(forms.Form):
    users = forms.CharField(required=False)


class ChangePasswordForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())


class ChatRoomForm(forms.ModelForm):
    users = forms.CharField(required=False)
    class Meta:
        model = ChatRoom
        widgets = {'created_by': forms.HiddenInput()}


class InviteToChatForm(forms.Form):
    CHATS = [(room.pk, room.name) for room in ChatRoom.objects.all()]
    chat = forms.ChoiceField(choices=CHATS)
    users = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(InviteToChatForm, self).__init__(*args, **kwargs)
        if 'user' in kwargs:
            user = kwargs.get('user')
            CHATS = [(room.pk, room.name) for room in ChatRoom.objects.filter(
                created_by=user)]
            self.fields['chat'] = forms.ChoiceField(choices=CHATS)

    def set_user(self, user):
        CHATS = [(room.pk, room.name) for room in ChatRoom.objects.filter(
            created_by=user)]
        self.fields['chat'] = forms.ChoiceField(choices=CHATS)
