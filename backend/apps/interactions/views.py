# backend/apps/interactions/views.py
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F

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
                    reaction.delete()
                    Post.objects.filter(pk=post.id).update(reactions_count=F('reactions_count') - 1)
                    return Response({'message': 'Reação removida'})

                reaction.reaction_type = reaction_type
                reaction.save(update_fields=['reaction_type', 'updated_at'])
                return Response({'message': 'Reação atualizada'})

            Post.objects.filter(pk=post.id).update(reactions_count=F('reactions_count') + 1)

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
    pagination_class = None

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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['post_id'] = self.kwargs.get('post_pk')
        return context

    def perform_create(self, serializer):
        parent = serializer.validated_data.get('parent')
        post_id = int(self.kwargs['post_pk'])

        if parent and parent.post_id != post_id:
            raise ValidationError({'parent': 'Comentário pai inválido para este post.'})

        comment = serializer.save()

        Post.objects.filter(pk=comment.post_id).update(comments_count=F('comments_count') + 1)

        if comment.parent_id:
            Comment.objects.filter(pk=comment.parent_id).update(replies_count=F('replies_count') + 1)

        UserActivity.objects.create(
            user=self.request.user,
            activity_type='comment',
            target_id=comment.post_id
        )

    def perform_update(self, serializer):
        if serializer.instance.user_id != self.request.user.id:
            raise PermissionDenied('Você não pode editar este comentário')
        serializer.save(is_edited=True)

    def perform_destroy(self, instance):
        if instance.user_id != self.request.user.id:
            raise PermissionDenied('Você não pode excluir este comentário')

        post_id = instance.post_id
        parent_id = instance.parent_id
        instance.delete()

        Post.objects.filter(pk=post_id).update(comments_count=F('comments_count') - 1)
        if parent_id:
            Comment.objects.filter(pk=parent_id).update(replies_count=F('replies_count') - 1)

    @action(detail=True, methods=['post'])
    def react(self, request, post_pk=None, pk=None):
        """Reagir a um comentário"""
        comment = self.get_object()
        reaction_type = request.data.get('reaction_type')

        if reaction_type not in dict(CommentReaction.REACTION_TYPES).keys():
            return Response(
                {'error': 'Tipo de reação inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
                Comment.objects.filter(pk=comment.id).update(reactions_count=F('reactions_count') - 1)
                return Response({'message': 'Reação removida'})

            reaction.reaction_type = reaction_type
            reaction.save(update_fields=['reaction_type'])
            return Response({'message': 'Reação atualizada'})

        Comment.objects.filter(pk=comment.id).update(reactions_count=F('reactions_count') + 1)
        return Response({'message': 'Reação adicionada'})
