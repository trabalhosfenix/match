import pytest
from rest_framework.exceptions import ValidationError
from apps.accounts.serializers import (
    RegisterSerializer, LoginSerializer, 
    ProfileUpdateSerializer, UserSerializer
)
from apps.accounts.models import UserLevel

@pytest.mark.django_db
class TestRegisterSerializer:
    """Testes para serializer de registro"""
    
    def test_valid_registration(self):
        """Testa registro válido"""
        data = {
            'username': 'novouser',
            'email': 'novo@test.com',
            'password': 'senha123',
            'password2': 'senha123',
            'first_name': 'João',
            'last_name': 'Silva'
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid()
        
        user = serializer.save()
        assert user.username == 'novouser'
        assert user.email == 'novo@test.com'
        assert user.level == UserLevel.USER
    
    def test_password_mismatch(self):
        """Testa senhas não coincidentes"""
        data = {
            'username': 'novouser',
            'email': 'novo@test.com',
            'password': 'senha123',
            'password2': 'senhadiferente'
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
    
    def test_duplicate_username(self, user_user):
        """Testa username duplicado"""
        data = {
            'username': user_user.username,
            'email': 'outro@test.com',
            'password': 'senha123',
            'password2': 'senha123'
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()

class TestLoginSerializer:
    """Testes para serializer de login"""
    
    def test_valid_login(self, user_user):
        """Testa login válido"""
        data = {
            'username': user_user.username,
            'password': 'testpass123'
        }
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid()
    
    def test_invalid_login(self):
        """Testa login inválido"""
        data = {
            'username': 'naoexiste',
            'password': 'errada'
        }
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()