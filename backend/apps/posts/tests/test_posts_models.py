import pytest
from django.utils import timezone
from datetime import timedelta
from apps.posts.models import Post, Media, SavedPost, Report

@pytest.mark.django_db
class TestPostModel:
    """Testes para modelo Post"""
    
    def test_create_post(self, user_user):
        """Testa criação de post"""
        post = Post.objects.create(
            author=user_user,
            content="Meu primeiro post!",
            tags=["python", "django"],
            region="Sudeste"
        )
        assert post.author == user_user
        assert post.content == "Meu primeiro post!"
        assert post.tags == ["python", "django"]
        assert post.reactions_count == 0
        assert post.comments_count == 0
        assert post.views_count == 0
    
    def test_increment_views(self, user_user):
        """Testa incremento de visualizações"""
        post = Post.objects.create(
            author=user_user,
            content="Post para testes"
        )
        assert post.views_count == 0
        
        post.increment_views()
        post.refresh_from_db()
        assert post.views_count == 1
        
        post.increment_views()
        post.refresh_from_db()
        assert post.views_count == 2
    
    def test_str_method(self, user_user):
        """Testa representação string do post"""
        post = Post.objects.create(
            author=user_user,
            content="Conteúdo do post"
        )
        assert str(post).startswith(f"Post de {user_user.username}")

@pytest.mark.django_db
class TestMediaModel:
    """Testes para modelo Media"""
    
    def test_create_image(self, user_user, test_image):
        """Testa criação de mídia imagem"""
        post = Post.objects.create(author=user_user, content="Com imagem")
        media = Media.objects.create(
            post=post,
            file=test_image,
            media_type='image',
            order=0
        )
        assert media.post == post
        assert media.media_type == 'image'
        assert media.order == 0
    
    def test_multiple_media(self, user_user, test_image, test_video):
        """Testa múltiplas mídias no mesmo post"""
        post = Post.objects.create(author=user_user, content="Múltiplas mídias")
        
        media1 = Media.objects.create(
            post=post, file=test_image, media_type='image', order=0
        )
        media2 = Media.objects.create(
            post=post, file=test_video, media_type='video', order=1
        )
        
        assert post.media.count() == 2
        assert list(post.media.values_list('order', flat=True)) == [0, 1]

@pytest.mark.django_db
class TestSavedPost:
    """Testes para posts salvos"""
    
    def test_save_post(self, user_user, plus_user):
        """Testa salvar post"""
        post = Post.objects.create(author=plus_user, content="Post para salvar")
        saved = SavedPost.objects.create(user=user_user, post=post)
        
        assert saved.user == user_user
        assert saved.post == post
        assert user_user.saved_posts.count() == 1
    
    def test_unique_save(self, user_user, plus_user):
        """Testa unique together"""
        post = Post.objects.create(author=plus_user, content="Post")
        SavedPost.objects.create(user=user_user, post=post)
        
        with pytest.raises(Exception):
            SavedPost.objects.create(user=user_user, post=post)