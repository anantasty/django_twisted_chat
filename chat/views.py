from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import FormView

from chat.models import ChatRoom
from chat.forms import ChatUserForm

@login_required
def index(request):
    chat_rooms = ChatRoom.objects.order_by('name')[:5]
    context = {
        'chat_list': chat_rooms,
    }
    return render(request,'chats/index.html', context)

@login_required
def chat_room(request, chat_room_id):
    chat = get_object_or_404(ChatRoom, pk=chat_room_id)
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
        user = form.save()
        print user
        return super(RegisterationView, self).form_valid(form)


def thanks(request):
    render(request, 'chats/thanks.html')
