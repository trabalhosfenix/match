# backend/apps/chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatRoom, Message
from apps.accounts.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Verificar autenticação
        user = self.scope['user']
        if not user.is_authenticated or not user.can_chat():
            await self.close()
            return
        
        # Verificar se usuário é participante da sala
        if not await self.is_participant(user, self.room_id):
            await self.close()
            return
        
        self.user = user
        
        # Entrar no grupo
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Marcar mensagens como lidas
        await self.mark_messages_as_read()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'message')
        
        if message_type == 'message':
            content = text_data_json['content']
            
            # Salvar mensagem no banco
            message = await self.save_message(content)
            
            # Enviar para o grupo
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': message.id,
                    'content': content,
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'sender_avatar': self.user.profile_picture.url if self.user.profile_picture else None,
                    'timestamp': str(timezone.now())
                }
            )
        
        elif message_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': text_data_json['is_typing']
                }
            )
    
    async def chat_message(self, event):
        """Receber mensagem do grupo e enviar para WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'id': event['message_id'],
            'content': event['content'],
            'sender': {
                'id': event['sender_id'],
                'username': event['sender_username'],
                'avatar': event['sender_avatar']
            },
            'timestamp': event['timestamp']
        }))
    
    async def typing_indicator(self, event):
        """Receber indicador de digitação"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))
    
    @database_sync_to_async
    def is_participant(self, user, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
            return user in room.participants.all()
        except ChatRoom.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        room = ChatRoom.objects.get(id=self.room_id)
        return Message.objects.create(
            room=room,
            sender=self.user,
            content=content
        )
    
    @database_sync_to_async
    def mark_messages_as_read(self):
        Message.objects.filter(
            room_id=self.room_id
        ).exclude(
            sender=self.user
        ).exclude(
            read_by=self.user
        ).update(is_read=True)