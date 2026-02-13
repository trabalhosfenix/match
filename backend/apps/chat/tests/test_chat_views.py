import pytest
from rest_framework import status
from django.urls import reverse
from apps.chat.models import ChatRoom, Message
from apps.accounts.models import Follow

@pytest.mark.django_db
class TestChatViews:
    """Testes para views do chat"""
    
    def test_create_private_room(self, auth_client, user_user, plus_user):
        """Testa criar sala privada"""
        Follow.objects.create(follower=user_user, following=plus_user)
        Follow.objects.create(follower=plus_user, following=user_user)
        client = auth_client(user_user)
        url = reverse('chat-room-create-private')
        data = {'user_id': plus_user.id}
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['room_type'] == 'private'
        assert len(response.data['participants']) == 2
    
    def test_create_existing_room(self, auth_client, user_user, plus_user):
        """Testa reutilizar sala existente"""
        Follow.objects.create(follower=user_user, following=plus_user)
        Follow.objects.create(follower=plus_user, following=user_user)
        # Criar sala uma vez
        room = ChatRoom.objects.create(room_type='private')
        room.participants.add(user_user, plus_user)
        
        client = auth_client(user_user)
        url = reverse('chat-room-create-private')
        data = {'user_id': plus_user.id}
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == room.id
    
    def test_anonimo_cannot_chat(self, auth_client, anon_user, plus_user):
        """Testa que anônimo não pode usar chat"""
        client = auth_client(anon_user)
        url = reverse('chat-room-create-private')
        data = {'user_id': plus_user.id}
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    

    def test_create_private_room_requires_mutual_follow(self, auth_client, user_user, plus_user):
        """Bloqueia chat sem follow mútuo"""
        Follow.objects.create(follower=user_user, following=plus_user)

        client = auth_client(user_user)
        url = reverse('chat-room-create-private')
        response = client.post(url, {'user_id': plus_user.id})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_send_message(self, auth_client, user_user, plus_user):
        """Testa enviar mensagem"""
        Follow.objects.create(follower=user_user, following=plus_user)
        Follow.objects.create(follower=plus_user, following=user_user)
        # Criar sala
        room = ChatRoom.objects.create(room_type='private')
        room.participants.add(user_user, plus_user)
        
        client = auth_client(user_user)
        url = reverse('chat-room-send-message', args=[room.id])
        data = {'content': 'Mensagem de teste'}
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'Mensagem de teste'
        assert response.data['sender']['username'] == user_user.username
        
        assert Message.objects.filter(room=room, sender=user_user).count() == 1
    
    def test_list_messages(self, auth_client, user_user, plus_user):
        """Testa listar mensagens da sala"""
        Follow.objects.create(follower=user_user, following=plus_user)
        Follow.objects.create(follower=plus_user, following=user_user)
        room = ChatRoom.objects.create(room_type='private')
        room.participants.add(user_user, plus_user)
        
        Message.objects.create(
            room=room,
            sender=user_user,
            content="Mensagem 1"
        )
        Message.objects.create(
            room=room,
            sender=plus_user,
            content="Mensagem 2"
        )
        
        client = auth_client(user_user)
        url = reverse('chat-room-messages', args=[room.id])
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    def test_unread_messages(self, auth_client, user_user, plus_user):
        """Testa mensagens não lidas"""
        Follow.objects.create(follower=user_user, following=plus_user)
        Follow.objects.create(follower=plus_user, following=user_user)
        room = ChatRoom.objects.create(room_type='private')
        room.participants.add(user_user, plus_user)
        
        # Plus envia mensagem para User
        Message.objects.create(
            room=room,
            sender=plus_user,
            content="Mensagem não lida"
        )
        
        client = auth_client(user_user)
        url = reverse('unread-messages')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['content'] == 'Mensagem não lida'
        assert response.data[0]['sender']['username'] == plus_user.username