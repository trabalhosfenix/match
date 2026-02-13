import pytest
from rest_framework import status
from django.urls import reverse

@pytest.mark.django_db
class TestLevelPermissions:
    """Testes de permissões baseadas em nível"""
    
    def test_anonimo_restrictions(self, auth_client, anon_user, user_user):
        """Testa todas as restrições do usuário anônimo"""
        client = auth_client(anon_user)
        
        # Não pode seguir
        follow_url = reverse('follow', args=[user_user.id])
        response = client.post(follow_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Não pode ver perfil de outros?
        profile_url = reverse('user-profile', args=[user_user.id])
        response = client.get(profile_url)
        assert response.status_code == status.HTTP_200_OK  # Pode visualizar
    
    def test_user_cannot_react(self, auth_client, user_user):
        """Testa que usuário nível USER não pode reagir"""
        # Este teste será implementado no app interactions
        pass
    
    def test_plus_can_react(self, auth_client, plus_user):
        """Testa que usuário PLUS pode reagir"""
        pass
    
    def test_only_pro_can_comment(self, auth_client, pro_user, plus_user):
        """Testa que apenas PRO pode comentar"""
        pass