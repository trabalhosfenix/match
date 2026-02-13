import pytest
from apps.chat.models import ChatRoom, Message, UserTyping
from apps.accounts.models import UserLevel

@pytest.mark.django_db
class TestChatModels:
    """Testes para modelos do chat"""
    
    def test_create_private_room(self, user_user, plus_user):
        """Testa criar sala privada"""
        room = ChatRoom.objects.create(
            room_type='private',
            created_by=user_user
        )
        room.participants.add(user_user, plus_user)
        
        assert room.room_type == 'private'
        assert room.participants.count() == 2
    
    def test_create_message(self, user_user, plus_user):
        """Testa criar mensagem"""
        room = ChatRoom.objects.create(room_type='private')
        room.participants.add(user_user, plus_user)
        
        message = Message.objects.create(
            room=room,
            sender=user_user,
            content="Olá, tudo bem?"
        )
        
        assert message.content == "Olá, tudo bem?"
        assert message.sender == user_user
        assert not message.is_read
    
    def test_user_typing(self, user_user, plus_user):
        """Testa status de digitação"""
        room = ChatRoom.objects.create(room_type='private')
        room.participants.add(user_user, plus_user)
        
        typing = UserTyping.objects.create(
            room=room,
            user=user_user,
            is_typing=True
        )
        
        assert typing.is_typing is True
        assert typing.user == user_user