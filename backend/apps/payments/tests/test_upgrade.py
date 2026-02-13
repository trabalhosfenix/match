import pytest
from rest_framework import status
from django.urls import reverse
from apps.payments.models import Plan, Subscription, Payment
from apps.accounts.models import UserLevel

@pytest.mark.django_db
class TestUpgradeSystem:
    """Testes para sistema de upgrade"""
    
    def test_list_plans(self, auth_client, user_user, create_plan):
        """Testa listagem de planos"""
        client = auth_client(user_user)
        url = reverse('plan-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert {p['level'] for p in response.data} == {UserLevel.PLUS, UserLevel.PRO}
    
    def test_upgrade_from_user_to_plus(self, auth_client, user_user, create_plan):
        """Testa upgrade de USER para PLUS"""
        client = auth_client(user_user)
        url = reverse('payment-process')
        
        plan = Plan.objects.get(level=UserLevel.PLUS)
        data = {
            'plan_id': plan.id,
            'payment_method': 'credit_card'
        }
        
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verifica upgrade
        user_user.refresh_from_db()
        assert user_user.level == UserLevel.PLUS
        
        # Verifica assinatura criada
        assert Subscription.objects.filter(user=user_user).exists()
        subscription = Subscription.objects.get(user=user_user)
        assert subscription.plan == plan
        assert subscription.status == 'active'
        
        # Verifica pagamento registrado
        assert Payment.objects.filter(user=user_user).exists()
    
    def test_upgrade_from_plus_to_pro(self, auth_client, plus_user, create_plan):
        """Testa upgrade de PLUS para PRO"""
        client = auth_client(plus_user)
        url = reverse('payment-process')
        
        plan = Plan.objects.get(level=UserLevel.PRO)
        data = {
            'plan_id': plan.id,
            'payment_method': 'pix'
        }
        
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        
        plus_user.refresh_from_db()
        assert plus_user.level == UserLevel.PRO
    
    def test_cannot_downgrade(self, auth_client, pro_user, create_plan):
        """Testa não poder fazer downgrade"""
        client = auth_client(pro_user)
        url = reverse('payment-process')
        
        plan = Plan.objects.get(level=UserLevel.PLUS)
        data = {
            'plan_id': plan.id,
            'payment_method': 'credit_card'
        }
        
        response = client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'já possui um nível igual ou superior' in str(response.data)
    
    def test_anonimo_cannot_upgrade(self, auth_client, anon_user, create_plan):
        """Testa que anônimo não pode fazer upgrade"""
        client = auth_client(anon_user)
        url = reverse('payment-process')
        
        plan = Plan.objects.get(level=UserLevel.PLUS)
        data = {
            'plan_id': plan.id,
            'payment_method': 'credit_card'
        }
        
        response = client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Registre-se primeiro' in str(response.data)
    
    def test_cancel_subscription(self, auth_client, plus_user, create_plan):
        """Testa cancelar assinatura"""
        # Primeiro faz upgrade
        client = auth_client(plus_user)
        upgrade_url = reverse('payment-process')
        plan = Plan.objects.get(level=UserLevel.PRO)
        client.post(upgrade_url, {
            'plan_id': plan.id,
            'payment_method': 'credit_card'
        })
        
        # Depois cancela
        cancel_url = reverse('subscription-cancel')
        response = client.post(cancel_url)
        
        assert response.status_code == status.HTTP_200_OK
        subscription = Subscription.objects.get(user=plus_user)
        assert subscription.status == 'cancelled'
        assert subscription.auto_renew is False