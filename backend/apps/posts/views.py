# backend/apps/posts/views.py
from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Prefetch
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from .models import Post, SavedPost
from .serializers import (
    PostSerializer, PostCreateSerializer,
    SavedPostSerializer, ReportSerializer
)
from apps.accounts.permissions import CanPost, CanViewContent
from apps.accounts.models import UserActivity
from apps.interactions.models import Reaction


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet para posts"""
    queryset = Post.objects.filter(is_active=True)
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewContent]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['region', 'tags', 'author']
    search_fields = ['content']

    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer
        return PostSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated, CanPost]
        return super().get_permissions()

    def perform_create(self, serializer):
        post = serializer.save()

        UserActivity.objects.create(
            user=self.request.user,
            activity_type='post',
            target_id=post.id
        )

        self.request.user.posts_count += 1
        self.request.user.save()

    def perform_update(self, serializer):
        if serializer.instance.author_id != self.request.user.id:
            raise PermissionDenied('Você não pode editar este post')
        serializer.save(is_edited=True)

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.id:
            raise PermissionDenied('Você não pode excluir este post')
        instance.delete()

    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        post = self.get_object()
        saved, created = SavedPost.objects.get_or_create(
            user=request.user,
            post=post
        )

        if created:
            return Response({'message': 'Post salvo com sucesso'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Post já está salvo'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def unsave(self, request, pk=None):
        post = self.get_object()
        try:
            saved = SavedPost.objects.get(user=request.user, post=post)
            saved.delete()
            return Response({'message': 'Post removido dos salvos'}, status=status.HTTP_200_OK)
        except SavedPost.DoesNotExist:
            return Response({'error': 'Post não está salvo'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        post = self.get_object()
        serializer = ReportSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(reporter=request.user, post=post)
            return Response({'message': 'Denúncia enviada com sucesso'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        post = self.get_object()
        post.increment_views()
        return Response({'views_count': post.views_count})


class TimelineView(generics.ListAPIView):
    """Timeline diária com filtros"""
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewContent]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['region', 'tags']

    def get_queryset(self):
        user = self.request.user
        today = timezone.now().date()

        queryset = Post.objects.filter(
            created_at__date=today,
            is_active=True
        ).select_related('author').prefetch_related(
            'media',
            Prefetch(
                'reactions',
                queryset=Reaction.objects.filter(user=user),
                to_attr='user_reaction'
            )
        ).order_by('-created_at')

        if user.preferred_tags:
            allowed_ids = [
                post.id for post in queryset
                if set(post.tags or []).intersection(set(user.preferred_tags))
            ]
            queryset = queryset.filter(id__in=allowed_ids)

        if user.region:
            queryset = queryset.filter(Q(region=user.region) | Q(region=''))

        return queryset


class UserPostsView(generics.ListAPIView):
    """Posts de um usuário específico"""
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewContent]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Post.objects.filter(author_id=user_id, is_active=True).order_by('-created_at')


class SavedPostsView(generics.ListAPIView):
    """Posts salvos pelo usuário"""
    serializer_class = SavedPostSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewContent]

    def get_queryset(self):
        return SavedPost.objects.filter(user=self.request.user).select_related('post__author').order_by('-created_at')
