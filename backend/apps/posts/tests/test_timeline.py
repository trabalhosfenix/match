import pytest
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.posts.models import Post

@pytest.mark.django_db
class TestTimeline:
    """Testes para timeline diária filtrada"""
    
    def test_timeline_only_today_posts(self, auth_client, user_user):
        """Testa que timeline só mostra posts do dia"""
        # Post de hoje
        post_today = Post.objects.create(
            author=user_user,
            content="Post de hoje"
        )
        
        # Post de ontem
        post_yesterday = Post.objects.create(
            author=user_user,
            content="Post de ontem"
        )
        post_yesterday.created_at = timezone.now() - timedelta(days=1)
        post_yesterday.save()
        
        client = auth_client(user_user)
        url = reverse('timeline')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['content'] == 'Post de hoje'
    
    def test_timeline_filter_by_region(self, auth_client, user_user, plus_user):
        """Testa filtro por região"""
        Post.objects.create(
            author=user_user,
            content="Post Sudeste",
            region="Sudeste"
        )
        Post.objects.create(
            author=plus_user,
            content="Post Sul",
            region="Sul"
        )
        
        # Usuário com região Sudeste
        user_user.region = "Sudeste"
        user_user.save()
        
        client = auth_client(user_user)
        url = reverse('timeline')
        response = client.get(url)
        
        assert len(response.data) == 1
        assert response.data[0]['content'] == 'Post Sudeste'
    
    def test_timeline_filter_by_tags(self, auth_client, user_user, plus_user):
        """Testa filtro por tags preferidas"""
        Post.objects.create(
            author=user_user,
            content="Post Python",
            tags=["python", "django"]
        )
        Post.objects.create(
            author=plus_user,
            content="Post JavaScript",
            tags=["js", "react"]
        )
        
        # Usuário prefere Python
        user_user.preferred_tags = ["python"]
        user_user.save()
        
        client = auth_client(user_user)
        url = reverse('timeline')
        response = client.get(url)
        
        assert len(response.data) == 1
        assert "Python" in response.data[0]['content']
    
    def test_anonimo_cannot_see_timeline(self, auth_client, anon_user):
        """Testa que anônimo não vê timeline"""
        client = auth_client(anon_user)
        url = reverse('timeline')
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_user_posts_view(self, auth_client, user_user, plus_user):
        """Testa visualização de posts de um usuário específico"""
        Post.objects.create(author=user_user, content="Post do User 1")
        Post.objects.create(author=user_user, content="Post do User 2")
        Post.objects.create(author=plus_user, content="Post do Plus")
        
        client = auth_client(user_user)
        url = reverse('user-posts', args=[user_user.id])
        response = client.get(url)
        
        assert len(response.data) == 2
        assert all(p['author']['id'] == user_user.id for p in response.data)