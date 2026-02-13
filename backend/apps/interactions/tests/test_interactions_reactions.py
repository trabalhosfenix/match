import pytest
from rest_framework import status
from django.urls import reverse
from apps.posts.models import Post
from apps.interactions.models import Reaction, Comment, CommentReaction

@pytest.mark.django_db
class TestReactions:
    """Testes para sistema de reações"""
    
    def test_plus_can_add_reaction(self, auth_client, plus_user, user_user):
        """Testa que usuário PLUS pode adicionar reação"""
        post = Post.objects.create(author=user_user, content="Post para reagir")
        client = auth_client(plus_user)
        
        url = reverse('post-reactions-toggle', args=[post.id])
        data = {'reaction_type': 'like'}
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Reaction.objects.filter(
            user=plus_user,
            post=post,
            reaction_type='like'
        ).exists()
        
        post.refresh_from_db()
        assert post.reactions_count == 1
    
    def test_user_cannot_add_reaction(self, auth_client, user_user, plus_user):
        """Testa que usuário USER não pode reagir"""
        post = Post.objects.create(author=plus_user, content="Post")
        client = auth_client(user_user)
        
        url = reverse('post-reactions-toggle', args=[post.id])
        data = {'reaction_type': 'like'}
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_remove_reaction(self, auth_client, plus_user, user_user):
        """Testa remover reação"""
        post = Post.objects.create(author=user_user, content="Post")
        Reaction.objects.create(
            user=plus_user,
            post=post,
            reaction_type='like'
        )
        post.reactions_count = 1
        post.save()
        
        client = auth_client(plus_user)
        url = reverse('post-reactions-toggle', args=[post.id])
        data = {'reaction_type': 'like'}
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert not Reaction.objects.filter(
            user=plus_user,
            post=post
        ).exists()
        
        post.refresh_from_db()
        assert post.reactions_count == 0
    
    def test_change_reaction(self, auth_client, plus_user, user_user):
        """Testa mudar tipo de reação"""
        post = Post.objects.create(author=user_user, content="Post")
        Reaction.objects.create(
            user=plus_user,
            post=post,
            reaction_type='like'
        )
        
        client = auth_client(plus_user)
        url = reverse('post-reactions-toggle', args=[post.id])
        data = {'reaction_type': 'love'}
        response = client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        reaction = Reaction.objects.get(user=plus_user, post=post)
        assert reaction.reaction_type == 'love'