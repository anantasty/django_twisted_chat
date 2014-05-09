from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MinValueValidator, MaxValueValidator

from chat.models import ChatUser, ChatRoom


class ChatUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_intro = forms.CharField()

    class Meta:
        model = ChatUser
        fields = ('first_name', 'last_name', 'username', 'email', 'password1',
                  'password2', 'user_intro', 'email')

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.user_intro = self.cleaned_data['user_intro']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class ChatUserInviteForm(ChatUserForm):
    def __init__(self, *args, **kwargs):
        super(ChatUserInviteForm, self).__init__(*args, **kwargs)
        del self.fields['password1']
        del self.fields['password2']


    score = forms.FloatField(validators=[MinValueValidator(1),
                                         MaxValueValidator(4)])

    class Meta:
        model = ChatUser
        fields = ('first_name', 'last_name', 'username', 'email', 'user_intro',
                  'email', 'score')

    def save(self, commit=True):

        user = super(UserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.user_intro = self.cleaned_data['user_intro']
        if commit:
            user.save()
        return user


class ChangePasswordForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())


class ChatRoomForm(forms.ModelForm):
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
