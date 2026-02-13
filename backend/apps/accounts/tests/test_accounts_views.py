import pytest
from rest_framework import status
from django.urls import reverse
from apps.accounts.models import Follow, UserLevel

@pytest.mark.django_db
class TestAuthViews:
    """Testes para views de autenticação"""
    
    def test_register(self, api_client):
        """Testa endpoint de registro"""
        url = reverse('register')
        data = {
            'username': 'teste',
            'email': 'teste@test.com',
            'password': 'T7v!9Qp#2Lm$4Xz',
            'password2': 'T7v!9Qp#2Lm$4Xz'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['username'] == 'teste'
    
    def test_login(self, api_client, user_user):
        """Testa endpoint de login"""
        url = reverse('login')
        data = {
            'username': 'user',
            'password': 'testpass123'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data
    
    def test_profile_view(self, auth_client, user_user):
        """Testa visualização do próprio perfil"""
        client = auth_client(user_user)
        url = reverse('profile')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == user_user.username
    
    def test_update_profile(self, auth_client, user_user, test_image):
        """Testa atualização do perfil"""
        client = auth_client(user_user)
        url = reverse('profile')
        data = {
            'first_name': 'João',
            'last_name': 'Silva',
            'bio': 'Nova biografia',
            'region': 'Sudeste',
            'profile_picture': test_image
        }
        response = client.patch(url, data, format='multipart')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'João'
        assert response.data['bio'] == 'Nova biografia'

@pytest.mark.django_db
class TestFollowViews:
    """Testes para funcionalidade de seguir"""
    
    def test_follow_user(self, auth_client, user_user, plus_user):
        """Testa seguir outro usuário"""
        client = auth_client(user_user)
        url = reverse('follow', args=[plus_user.id])
        response = client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        
        assert Follow.objects.filter(
            follower=user_user,
            following=plus_user
        ).exists()
    
    def test_cannot_follow_self(self, auth_client, user_user):
        """Testa não poder seguir a si mesmo"""
        client = auth_client(user_user)
        url = reverse('follow', args=[user_user.id])
        response = client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_anonimo_cannot_follow(self, auth_client, anon_user, user_user):
        """Testa que anônimo não pode seguir"""
        client = auth_client(anon_user)
        url = reverse('follow', args=[user_user.id])
        response = client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_unfollow_user(self, auth_client, user_user, plus_user):
        """Testa deixar de seguir"""
        # Primeiro segue
        Follow.objects.create(follower=user_user, following=plus_user)
        
        client = auth_client(user_user)
        url = reverse('unfollow', args=[plus_user.id])
        response = client.post(url)
        assert response.status_code == status.HTTP_200_OK
        
        assert not Follow.objects.filter(
            follower=user_user,
            following=plus_user
        ).exists()
    
    def test_followers_list(self, auth_client, user_user, plus_user, pro_user):
        """Testa listagem de seguidores"""
        # Usuário plus segue user
        Follow.objects.create(follower=plus_user, following=user_user)
        # Usuário pro segue user
        Follow.objects.create(follower=pro_user, following=user_user)
        
        client = auth_client(user_user)
        url = reverse('followers', args=[user_user.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    def test_following_list(self, auth_client, user_user, plus_user, pro_user):
        """Testa listagem de quem o usuário segue"""
        # User segue plus
        Follow.objects.create(follower=user_user, following=plus_user)
        # User segue pro
        Follow.objects.create(follower=user_user, following=pro_user)
        
        client = auth_client(user_user)
        url = reverse('following', args=[user_user.id])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2