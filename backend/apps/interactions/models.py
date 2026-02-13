# backend/apps/interactions/models.py
from django.db import models
from django.contrib.auth import get_user_model
from apps.posts.models import Post

User = get_user_model()

class Reaction(models.Model):
    REACTION_TYPES = [
        ('like', '👍 Like'),
        ('love', '❤️ Love'),
        ('laugh', '😂 Laugh'),
        ('wow', '😮 Wow'),
        ('sad', '😢 Sad'),
        ('angry', '😠 Angry'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name='Usuário'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name='Post'
    )
    reaction_type = models.CharField(
        max_length=10,
        choices=REACTION_TYPES,
        verbose_name='Tipo de reação'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'post']
        verbose_name = 'Reação'
        verbose_name_plural = 'Reações'
        indexes = [
            models.Index(fields=['user', 'post']),
            models.Index(fields=['post', 'reaction_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_reaction_type_display()}"

class Comment(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Usuário'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Post'
    )
    content = models.TextField(
        max_length=1000,
        verbose_name='Conteúdo'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='Resposta a'
    )
    
    # Stats
    reactions_count = models.PositiveIntegerField(default=0)
    replies_count = models.PositiveIntegerField(default=0)
    
    # Status
    is_edited = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Comentário de {self.user.username} - {self.created_at.strftime('%d/%m/%Y')}"

class CommentReaction(models.Model):
    """Reações em comentários"""
    REACTION_TYPES = Reaction.REACTION_TYPES
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'comment']