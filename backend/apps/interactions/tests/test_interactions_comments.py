import pytest
from rest_framework import status
from django.urls import reverse
from apps.posts.models import Post
from apps.interactions.models import Comment

@pytest.mark.django_db
class TestComments:
    """Testes para sistema de comentários"""
    
    def test_pro_can_comment(self, auth_client, pro_user, user_user):
        """Testa que usuário PRO pode comentar"""
        post = Post.objects.create(author=user_user, content="Post para comentar")
        client = auth_client(pro_user)
        
        url = reverse('post-comments-list', args=[post.id])
        data = {'content': 'Excelente post!'}
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Comment.objects.filter(
            user=pro_user,
            post=post,
            content='Excelente post!'
        ).exists()
        
        post.refresh_from_db()
        assert post.comments_count == 1
    
    def test_plus_cannot_comment(self, auth_client, plus_user, user_user):
        """Testa que usuário PLUS não pode comentar"""
        post = Post.objects.create(author=user_user, content="Post")
        client = auth_client(plus_user)
        
        url = reverse('post-comments-list', args=[post.id])
        data = {'content': 'Tentativa de comentário'}
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_list_comments(self, auth_client, pro_user, user_user, plus_user):
        """Testa listagem de comentários"""
        post = Post.objects.create(author=user_user, content="Post")
        Comment.objects.create(
            user=pro_user,
            post=post,
            content="Comentário 1"
        )
        Comment.objects.create(
            user=plus_user,
            post=post,
            content="Comentário 2"
        )
        
        client = auth_client(user_user)
        url = reverse('post-comments-list', args=[post.id])
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    def test_update_own_comment(self, auth_client, pro_user, user_user):
        """Testa atualizar próprio comentário"""
        post = Post.objects.create(author=user_user, content="Post")
        comment = Comment.objects.create(
            user=pro_user,
            post=post,
            content="Comentário original"
        )
        
        client = auth_client(pro_user)
        url = reverse('post-comments-detail', args=[post.id, comment.id])
        data = {'content': 'Comentário atualizado'}
        response = client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        comment.refresh_from_db()
        assert comment.content == 'Comentário atualizado'
        assert comment.is_edited is True
    
    def test_delete_comment(self, auth_client, pro_user, user_user):
        """Testa deletar comentário"""
        post = Post.objects.create(author=user_user, content="Post")
        comment = Comment.objects.create(
            user=pro_user,
            post=post,
            content="Comentário para deletar"
        )
        
        client = auth_client(pro_user)
        url = reverse('post-comments-detail', args=[post.id, comment.id])
        response = client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Comment.objects.filter(id=comment.id).exists()
        
        post.refresh_from_db()
        assert post.comments_count == 0
    
    def test_reply_to_comment(self, auth_client, pro_user, user_user):
        """Testa responder a um comentário"""
        post = Post.objects.create(author=user_user, content="Post")
        parent = Comment.objects.create(
            user=pro_user,
            post=post,
            content="Comentário pai"
        )
        
        client = auth_client(pro_user)
        url = reverse('post-comments-list', args=[post.id])
        data = {
            'content': 'Resposta ao comentário',
            'parent': parent.id
        }
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        parent.refresh_from_db()
        assert parent.replies_count == 1
    
    def test_comment_reaction(self, auth_client, pro_user, plus_user, user_user):
        """Testa reagir a comentário"""
        post = Post.objects.create(author=user_user, content="Post")
        comment = Comment.objects.create(
            user=pro_user,
            post=post,
            content="Comentário"
        )
        
        # PLUS pode reagir a comentários
        client = auth_client(plus_user)
        url = reverse('post-comments-react', args=[post.id, comment.id])
        data = {'reaction_type': 'like'}
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        comment.refresh_from_db()
        assert comment.reactions_count == 1