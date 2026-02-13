import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.accounts.models import UserLevel
from apps.payments.models import Plan
import tempfile
from PIL import Image
import io

User = get_user_model()

@pytest.fixture
def api_client():
    """Retorna um APICliente não autenticado"""
    return APIClient()

@pytest.fixture
def auth_client():
    """Retorna um APIClient autenticado com usuário comum"""
    def _auth_client(user=None):
        client = APIClient()
        if user:
            client.force_authenticate(user=user)
        return client
    return _auth_client

@pytest.fixture
def anon_user():
    """Cria um usuário anônimo"""
    return User.objects.create_user(
        username='anonimo',
        password='testpass123',
        email='anon@test.com',
        level=UserLevel.ANONIMO
    )

@pytest.fixture
def user_user():
    """Cria um usuário nível USER"""
    return User.objects.create_user(
        username='user',
        password='testpass123',
        email='user@test.com',
        level=UserLevel.USER
    )

@pytest.fixture
def plus_user():
    """Cria um usuário nível PLUS"""
    return User.objects.create_user(
        username='plus',
        password='testpass123',
        email='plus@test.com',
        level=UserLevel.PLUS
    )

@pytest.fixture
def pro_user():
    """Cria um usuário nível PRO"""
    return User.objects.create_user(
        username='pro',
        password='testpass123',
        email='pro@test.com',
        level=UserLevel.PRO
    )

@pytest.fixture
def all_users(anon_user, user_user, plus_user, pro_user):
    """Retorna todos os níveis de usuário"""
    return {
        'anon': anon_user,
        'user': user_user,
        'plus': plus_user,
        'pro': pro_user
    }

@pytest.fixture
def test_image():
    """Cria uma imagem de teste"""
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), 'red')
    image.save(file, 'png')
    file.name = 'test.png'
    file.seek(0)
    return SimpleUploadedFile(
        'test.png', 
        file.read(), 
        content_type='image/png'
    )

@pytest.fixture
def test_video():
    """Cria um vídeo de teste simulado"""
    return SimpleUploadedFile(
        'test.mp4',
        b'fake_video_content',
        content_type='video/mp4'
    )

@pytest.fixture
def create_plan():
    """Cria planos de assinatura"""
    Plan.objects.get_or_create(
        level=UserLevel.PLUS,
        defaults={
            'name': 'Plano Plus',
            'price': 29.90,
            'duration_days': 30,
            'features': ['react', 'post', 'chat']
        }
    )
    Plan.objects.get_or_create(
        level=UserLevel.PRO,
        defaults={
            'name': 'Plano Pro',
            'price': 49.90,
            'duration_days': 30,
            'features': ['comment', 'react', 'post', 'chat']
        }
    )
    return Plan.objects.all()