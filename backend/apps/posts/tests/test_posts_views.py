import pytest
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.posts.models import Post, SavedPost

@pytest.mark.django_db
class TestPostViews:
    """Testes para views de posts"""
    
    def test_create_post_user(self, auth_client, user_user):
        """Testa criação de post por usuário USER"""
        client = auth_client(user_user)
        url = reverse('post-list')
        data = {
            'content': 'Meu primeiro post!',
            'tags': ['python', 'django'],
            'region': 'Sudeste'
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'Meu primeiro post!'
        assert response.data['author']['username'] == user_user.username
        
        # Verifica que o contador de posts do usuário aumentou
        user_user.refresh_from_db()
        assert user_user.posts_count == 1
    
    def test_create_post_anonimo_fails(self, auth_client, anon_user):
        """Testa que anônimo não pode criar post"""
        client = auth_client(anon_user)
        url = reverse('post-list')
        data = {'content': 'Tentativa de post'}
        response = client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_list_posts(self, auth_client, user_user, plus_user):
        """Testa listagem de posts"""
        # Criar alguns posts
        Post.objects.create(author=user_user, content="Post 1")
        Post.objects.create(author=plus_user, content="Post 2")
        Post.objects.create(author=user_user, content="Post 3")
        
        client = auth_client(user_user)
        url = reverse('post-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
    
    def test_update_own_post(self, auth_client, user_user):
        """Testa atualizar próprio post"""
        post = Post.objects.create(author=user_user, content="Original")
        client = auth_client(user_user)
        url = reverse('post-detail', args=[post.id])
        
        data = {'content': 'Conteúdo atualizado'}
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['content'] == 'Conteúdo atualizado'
        assert response.data['is_edited'] is True
    
    def test_cannot_update_others_post(self, auth_client, user_user, plus_user):
        """Testa não poder atualizar post de outro"""
        post = Post.objects.create(author=plus_user, content="Post de outro")
        client = auth_client(user_user)
        url = reverse('post-detail', args=[post.id])
        
        data = {'content': 'Tentativa de hack'}
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_own_post(self, auth_client, user_user):
        """Testa deletar próprio post"""
        post = Post.objects.create(author=user_user, content="Para deletar")
        client = auth_client(user_user)
        url = reverse('post-detail', args=[post.id])
        
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Post.objects.filter(id=post.id).exists()
    
    @pytest.mark.media
    def test_create_post_with_image(self, auth_client, user_user, test_image):
        """Testa criar post com imagem"""
        client = auth_client(user_user)
        url = reverse('post-list')
        data = {
            'content': 'Post com imagem',
            'media': [test_image]
        }
        response = client.post(url, data, format='multipart')
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data['media']) == 1
        assert 'file' in response.data['media'][0]

@pytest.mark.django_db
class TestSavedPosts:
    """Testes para posts salvos"""
    
    def test_save_post(self, auth_client, user_user, plus_user):
        """Testa salvar post"""
        post = Post.objects.create(author=plus_user, content="Post legal")
        client = auth_client(user_user)
        url = reverse('post-save', args=[post.id])
        
        response = client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        assert SavedPost.objects.filter(user=user_user, post=post).exists()
    
    def test_unsave_post(self, auth_client, user_user, plus_user):
        """Testa remover post salvo"""
        post = Post.objects.create(author=plus_user, content="Post salvo")
        SavedPost.objects.create(user=user_user, post=post)
        
        client = auth_client(user_user)
        url = reverse('post-unsave', args=[post.id])
        
        response = client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert not SavedPost.objects.filter(user=user_user, post=post).exists()
    
    def test_list_saved_posts(self, auth_client, user_user, plus_user):
        """Testa listar posts salvos"""
        post1 = Post.objects.create(author=plus_user, content="Post 1")
        post2 = Post.objects.create(author=plus_user, content="Post 2")
        
        SavedPost.objects.create(user=user_user, post=post1)
        SavedPost.objects.create(user=user_user, post=post2)
        
        client = auth_client(user_user)
        url = reverse('saved-posts')
        
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2