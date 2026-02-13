import pytest
from rest_framework import status
from django.urls import reverse
from apps.accounts.models import Follow, UserActivity
from apps.posts.models import Post
from apps.interactions.models import Reaction, Comment

@pytest.mark.django_db
class TestCompleteUserJourney:
    """Testa jornada completa do usuário"""
    
    def test_user_journey_anonymous_to_pro(self, api_client):
        """Testa jornada de usuário anônimo até PRO"""
        
        # 1. Registro
        register_url = reverse('register')
        user_data = {
            'username': 'jornada',
            'email': 'jornada@test.com',
            'password': 'SenhaForte@123',
            'password2': 'SenhaForte@123'
        }
        response = api_client.post(register_url, user_data)
        assert response.status_code == status.HTTP_201_CREATED
        user_id = response.data['id']
        
        # 2. Login
        login_url = reverse('login')
        login_data = {'username': 'jornada', 'password': 'SenhaForte@123'}
        response = api_client.post(login_url, login_data)
        assert response.status_code == status.HTTP_200_OK
        token = response.data['access']
        
        # Cliente autenticado
        from rest_framework.test import APIClient
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # 3. Criar post (USER pode)
        post_url = reverse('post-list')
        post_data = {'content': 'Meu primeiro post!'}
        response = client.post(post_url, post_data)
        assert response.status_code == status.HTTP_201_CREATED
        post_id = response.data['id']
        
        # 4. Tentar reagir (USER não pode)
        react_url = reverse('post-reactions-toggle', args=[post_id])
        react_data = {'reaction_type': 'like'}
        response = client.post(react_url, react_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # 5. Upgrade para PLUS
        # ... (precisa de planos criados)
        
        # 6. Agora pode reagir
        # ...
    
    def test_follow_and_interact(self, auth_client, user_user, plus_user, pro_user):
        """Testa seguir e interagir com posts"""
        # User segue Plus
        client = auth_client(user_user)
        follow_url = reverse('follow', args=[plus_user.id])
        client.post(follow_url)
        
        # Plus cria post
        plus_client = auth_client(plus_user)
        post = Post.objects.create(author=plus_user, content="Post do Plus")
        
        # User reage? Não, USER não pode reagir
        react_url = reverse('post-reactions-toggle', args=[post.id])
        response = client.post(react_url, {'reaction_type': 'like'})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Pro comenta
        pro_client = auth_client(pro_user)
        comment_url = reverse('post-comments-list', args=[post.id])
        response = pro_client.post(comment_url, {'content': 'Belo post!'})
        assert response.status_code == status.HTTP_201_CREATED
        
        # Atividades registradas
        assert UserActivity.objects.filter(user=user_user, activity_type='follow').exists()
        assert UserActivity.objects.filter(user=plus_user, activity_type='post').exists()
        assert UserActivity.objects.filter(user=pro_user, activity_type='comment').exists()