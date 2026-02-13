# backend/apps/chat/serializers.py
from rest_framework import serializers
from .models import ChatRoom, Message, MessageAttachment
from apps.accounts.serializers import UserSerializer

class ChatRoomSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_type', 'name', 'participants',
            'created_at', 'updated_at', 'last_message',
            'unread_count'
        ]
    
    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return {
                'content': last_msg.content[:100],
                'sender': last_msg.sender.username,
                'created_at': last_msg.created_at
            }
        return None
    
    def get_unread_count(self, obj):
        user = self.context.get('request').user
        return obj.messages.filter(
            read_by=user
        ).exclude(sender=user).count()

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    attachments = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'room', 'sender', 'content',
            'is_read', 'attachments', 'created_at'
        ]
        read_only_fields = ['is_read', 'created_at']
    
    def get_attachments(self, obj):
        return [
            {
                'id': att.id,
                'filename': att.filename,
                'file_type': att.file_type,
                'file_size': att.file_size,
                'url': att.file.url
            }
            for att in obj.attachments.all()
        ]

class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['content']