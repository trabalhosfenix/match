# backend/apps/chat/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class ChatRoom(models.Model):
    ROOM_TYPES = [
        ('private', 'Privado'),
        ('group', 'Grupo'),
    ]
    
    room_type = models.CharField(
        max_length=10,
        choices=ROOM_TYPES,
        default='private'
    )
    participants = models.ManyToManyField(
        User,
        related_name='chat_rooms',
        verbose_name='Participantes'
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Nome da sala'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_rooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Sala de chat'
        verbose_name_plural = 'Salas de chat'
    
    def __str__(self):
        if self.room_type == 'private':
            return f"Sala privada {self.id}"
        return self.name or f"Grupo {self.id}"

class Message(models.Model):
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Sala'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Remetente'
    )
    content = models.TextField(
        max_length=2000,
        verbose_name='Conteúdo'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Lida'
    )
    read_by = models.ManyToManyField(
        User,
        related_name='read_messages',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        indexes = [
            models.Index(fields=['room', '-created_at']),
        ]
    
    def __str__(self):
        return f"Mensagem de {self.sender.username} - {self.created_at.strftime('%H:%M')}"

class MessageAttachment(models.Model):
    """Anexos em mensagens"""
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='chat/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    file_size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

class UserTyping(models.Model):
    """Status de digitação"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_typing = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['room', 'user']