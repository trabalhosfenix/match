# backend/apps/interactions/views.py
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Reaction, Comment, CommentReaction
from .serializers import (
    ReactionSerializer, CommentSerializer, 
    CommentCreateSerializer
)
from apps.posts.models import Post
from apps.accounts.permissions import CanReact, CanComment
from apps.accounts.models import UserActivity

class ReactionViewSet(viewsets.GenericViewSet):
    """ViewSet para reações"""
    serializer_class = ReactionSerializer
    permission_classes = [permissions.IsAuthenticated, CanReact]
    
    def get_queryset(self):
        return Reaction.objects.filter(post_id=self.kwargs['post_pk'])
    
    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle(self, request, post_pk=None):
        """Adicionar ou remover reação"""
        post = get_object_or_404(Post, pk=post_pk)
        reaction_type = request.data.get('reaction_type')
        
        if reaction_type not in dict(Reaction.REACTION_TYPES).keys():
            return Response(
                {'error': 'Tipo de reação inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            reaction, created = Reaction.objects.get_or_create(
                user=request.user,
                post=post,
                defaults={'reaction_type': reaction_type}
            )
            
            if not created:
                if reaction.reaction_type == reaction_type:
                    # Remover reação
                    reaction.delete()
                    post.reactions_count -= 1
                    post.save()
                    return Response({'message': 'Reação removida'})
                else:
                    # Atualizar tipo de reação
                    reaction.reaction_type = reaction_type
                    reaction.save()
                    return Response({'message': 'Reação atualizada'})
            else:
                # Nova reação
                post.reactions_count += 1
                post.save()
                
                # Registrar atividade
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='reaction',
                    target_id=post.id,
                    metadata={'reaction': reaction_type}
                )
                
                return Response(
                    {'message': 'Reação adicionada'},
                    status=status.HTTP_201_CREATED
                )

class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet para comentários"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Comment.objects.filter(
            post_id=self.kwargs['post_pk'],
            parent=None,
            is_active=True
        ).select_related('user').prefetch_related('replies')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated, CanComment]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        comment = serializer.save()
        
        # Atualizar contador do post
        post = comment.post
        post.comments_count += 1
        post.save()
        
        # Registrar atividade
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='comment',
            target_id=post.id
        )
    
    @action(detail=True, methods=['post'])
    def react(self, request, post_pk=None, pk=None):
        """Reagir a um comentário"""
        comment = self.get_object()
        reaction_type = request.data.get('reaction_type')
        
        if not request.user.can_react():
            return Response(
                {'error': 'Seu nível não permite reagir a comentários'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reaction, created = CommentReaction.objects.get_or_create(
            user=request.user,
            comment=comment,
            defaults={'reaction_type': reaction_type}
        )
        
        if not created:
            if reaction.reaction_type == reaction_type:
                reaction.delete()
                comment.reactions_count -= 1
                comment.save()
                return Response({'message': 'Reação removida'})
            else:
                reaction.reaction_type = reaction_type
                reaction.save()
        else:
            comment.reactions_count += 1
            comment.save()
        
        return Response({'message': 'Reação adicionada'})