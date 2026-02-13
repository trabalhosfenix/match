import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from apps.accounts.models import Follow, UserActivity, UserLevel

User = get_user_model()

@pytest.mark.django_db
class TestUserModel:
    """Testes para o modelo User"""
    
    def test_create_user(self):
        """Testa criação de usuário comum"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@test.com'
        assert user.check_password('testpass123')
        assert user.level == UserLevel.ANONIMO
        assert user.followers_count == 0
        assert user.following_count == 0
        assert user.posts_count == 0
    
    def test_create_superuser(self):
        """Testa criação de superusuário"""
        admin = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        assert admin.is_superuser
        assert admin.is_staff
    
    def test_user_level_permissions(self, all_users):
        """Testa permissões baseadas em nível"""
        # Anônimo
        assert not all_users['anon'].can_post()
        assert not all_users['anon'].can_react()
        assert not all_users['anon'].can_comment()
        assert not all_users['anon'].can_chat()
        assert not all_users['anon'].can_follow()
        
        # User
        assert all_users['user'].can_post()
        assert not all_users['user'].can_react()
        assert not all_users['user'].can_comment()
        assert all_users['user'].can_chat()
        assert all_users['user'].can_follow()
        
        # Plus
        assert all_users['plus'].can_post()
        assert all_users['plus'].can_react()
        assert not all_users['plus'].can_comment()
        assert all_users['plus'].can_chat()
        assert all_users['plus'].can_follow()
        
        # Pro
        assert all_users['pro'].can_post()
        assert all_users['pro'].can_react()
        assert all_users['pro'].can_comment()
        assert all_users['pro'].can_chat()
        assert all_users['pro'].can_follow()
    
    def test_upgrade_user(self, user_user):
        """Testa upgrade de nível"""
        assert user_user.level == UserLevel.USER
        
        # Upgrade para Plus
        user_user.upgrade_to(UserLevel.PLUS)
        assert user_user.level == UserLevel.PLUS
        
        # Upgrade para Pro
        user_user.upgrade_to(UserLevel.PRO)
        assert user_user.level == UserLevel.PRO
        
        # Tentativa de upgrade inválido
        assert not user_user.upgrade_to('invalid_level')

@pytest.mark.django_db
class TestFollowModel:
    """Testes para o modelo Follow"""
    
    def test_create_follow(self, user_user, plus_user):
        """Testa criar relação de seguir"""
        follow = Follow.objects.create(
            follower=user_user,
            following=plus_user
        )
        assert follow.follower == user_user
        assert follow.following == plus_user
        
        # Testa unique together
        with pytest.raises(IntegrityError):
            Follow.objects.create(
                follower=user_user,
                following=plus_user
            )
    
    def test_follow_counts(self, user_user, plus_user):
        """Testa atualização dos contadores ao seguir"""
        Follow.objects.create(
            follower=user_user,
            following=plus_user
        )
        
        user_user.refresh_from_db()
        plus_user.refresh_from_db()
        
        assert user_user.following_count == 1
        assert plus_user.followers_count == 1