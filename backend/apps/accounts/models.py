# backend/apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import FileExtensionValidator
import os

class UserLevel(models.TextChoices):
    ANONIMO = 'anon', 'Anônimo'
    USER = 'user', 'User'
    PLUS = 'plus', 'Plus'
    PRO = 'pro', 'Pro'

def profile_picture_path(instance, filename):
    """Gera caminho único para foto de perfil"""
    ext = filename.split('.')[-1]
    filename = f"profile_{instance.username}_{instance.id}.{ext}"
    return os.path.join('profiles', filename)

def cover_picture_path(instance, filename):
    """Gera caminho único para foto de capa"""
    ext = filename.split('.')[-1]
    filename = f"cover_{instance.username}_{instance.id}.{ext}"
    return os.path.join('covers', filename)

class User(AbstractUser):
    level = models.CharField(
        max_length=10,
        choices=UserLevel.choices,
        default=UserLevel.ANONIMO,
        verbose_name='Nível do usuário'
    )
    
    # Profile
    profile_picture = models.ImageField(
        upload_to=profile_picture_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif'])],
        verbose_name='Foto de perfil'
    )
    cover_picture = models.ImageField(
        upload_to=cover_picture_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif'])],
        verbose_name='Foto de capa'
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Biografia'
    )
    
    # Stats
    followers_count = models.PositiveIntegerField(default=0, verbose_name='Seguidores')
    following_count = models.PositiveIntegerField(default=0, verbose_name='Seguindo')
    posts_count = models.PositiveIntegerField(default=0, verbose_name='Posts')
    
    # Preferences
    preferred_tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Tags preferidas'
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Região'
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de nascimento'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['level']),
            models.Index(fields=['region']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_level_display()})"
    
    def can_post(self):
        return self.level in [UserLevel.USER, UserLevel.PLUS, UserLevel.PRO]
    
    def can_react(self):
        return self.level in [UserLevel.PLUS, UserLevel.PRO]
    
    def can_comment(self):
        return self.level == UserLevel.PRO
    
    def can_chat(self):
        return self.level != UserLevel.ANONIMO
    
    def can_follow(self):
        return self.level != UserLevel.ANONIMO
    
    def upgrade_to(self, new_level):
        """Upgrade de nível do usuário"""
        if new_level in UserLevel.values:
            self.level = new_level
            self.save()
            return True
        return False

class Follow(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following_relationships',
        verbose_name='Seguidor'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower_relationships',
        verbose_name='Seguindo'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']
        verbose_name = 'Seguir'
        verbose_name_plural = 'Seguidores'
        indexes = [
            models.Index(fields=['follower', 'following']),
        ]

    def __str__(self):
        return f"{self.follower.username} segue {self.following.username}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            User.objects.filter(pk=self.follower_id).update(following_count=models.F('following_count') + 1)
            User.objects.filter(pk=self.following_id).update(followers_count=models.F('followers_count') + 1)

    def delete(self, *args, **kwargs):
        follower_id = self.follower_id
        following_id = self.following_id
        super().delete(*args, **kwargs)
        User.objects.filter(pk=follower_id).update(following_count=models.F('following_count') - 1)
        User.objects.filter(pk=following_id).update(followers_count=models.F('followers_count') - 1)

class UserActivity(models.Model):
    """Registro de atividades do usuário"""
    ACTIVITY_TYPES = [
        ('post', 'Criou post'),
        ('comment', 'Comentou'),
        ('reaction', 'Reagiu'),
        ('follow', 'Seguiu'),
        ('upgrade', 'Upgrade'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Atividade'
        verbose_name_plural = 'Atividades'
        ordering = ['-created_at']