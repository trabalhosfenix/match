# backend/apps/posts/models.py
from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model
import os

User = get_user_model()

def post_media_path(instance, filename):
    """Gera caminho único para mídia do post"""
    ext = filename.split('.')[-1]
    filename = f"post_{instance.post.id}_{instance.id}.{ext}"
    return os.path.join('posts', filename)

class Post(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Autor'
    )
    content = models.TextField(
        max_length=2000,
        verbose_name='Conteúdo'
    )
    
    # Metadata para timeline
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Tags'
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Região'
    )
    
    # Stats
    reactions_count = models.PositiveIntegerField(default=0, verbose_name='Reações')
    comments_count = models.PositiveIntegerField(default=0, verbose_name='Comentários')
    shares_count = models.PositiveIntegerField(default=0, verbose_name='Compartilhamentos')
    views_count = models.PositiveIntegerField(default=0, verbose_name='Visualizações')
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    is_edited = models.BooleanField(default=False, verbose_name='Editado')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['region']),
            models.Index(fields=['tags']),
        ]
    
    def __str__(self):
        return f"Post de {self.author.username} - {self.created_at.strftime('%d/%m/%Y')}"
    
    def increment_views(self):
        """Incrementa contador de visualizações"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

class Media(models.Model):
    MEDIA_TYPES = [
        ('image', 'Imagem'),
        ('video', 'Vídeo'),
        ('gif', 'GIF'),
    ]
    
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='media',
        verbose_name='Post'
    )
    file = models.FileField(
        upload_to=post_media_path,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm'])],
        verbose_name='Arquivo'
    )
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPES,
        verbose_name='Tipo de mídia'
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Ordem'
    )
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Mídia'
        verbose_name_plural = 'Mídias'
    
    def __str__(self):
        return f"{self.get_media_type_display()} - {self.post.id}"

class SavedPost(models.Model):
    """Posts salvos pelo usuário"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_posts'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='saved_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
        verbose_name = 'Post salvo'
        verbose_name_plural = 'Posts salvos'

class Report(models.Model):
    """Denúncias de posts"""
    REPORT_REASONS = [
        ('spam', 'Spam'),
        ('harassment', 'Assédio'),
        ('hate_speech', 'Discurso de ódio'),
        ('violence', 'Violência'),
        ('nudity', 'Nudez'),
        ('other', 'Outro'),
    ]
    
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_made'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(max_length=500, blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Denúncia'
        verbose_name_plural = 'Denúncias'