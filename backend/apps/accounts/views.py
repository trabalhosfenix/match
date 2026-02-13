# backend/apps/accounts/views.py
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from django.utils import timezone

from .models import User, Follow, UserActivity, UserLevel
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    ProfileUpdateSerializer, FollowSerializer, UserActivitySerializer
)
from .permissions import IsOwnerOrReadOnly, CanFollow

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """Registro de novo usuário"""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

class LoginView(APIView):
    """Login de usuário"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            
            # Atualizar último acesso
            user.last_login = timezone.now()
            user.save()
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(generics.RetrieveUpdateAPIView):
    """Visualizar e editar próprio perfil"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = ProfileUpdateSerializer(
            instance, 
            data=request.data, 
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(UserSerializer(instance).data)

class UserProfileView(generics.RetrieveAPIView):
    """Visualizar perfil de outro usuário"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

class FollowView(APIView):
    """Seguir usuário"""
    permission_classes = [permissions.IsAuthenticated, CanFollow]
    
    def post(self, request, user_id):
        user_to_follow = get_object_or_404(User, pk=user_id)
        
        if request.user == user_to_follow:
            return Response(
                {'error': 'Você não pode seguir a si mesmo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if created:
            # Atualizar contadores
            request.user.following_count += 1
            request.user.save()
            user_to_follow.followers_count += 1
            user_to_follow.save()
            
            # Registrar atividade
            UserActivity.objects.create(
                user=request.user,
                activity_type='follow',
                target_id=user_to_follow.id,
                metadata={'username': user_to_follow.username}
            )
            
            return Response(
                {'message': f'Agora você segue {user_to_follow.username}'},
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {'message': 'Você já segue este usuário'},
            status=status.HTTP_200_OK
        )

class UnfollowView(APIView):
    """Deixar de seguir usuário"""
    permission_classes = [permissions.IsAuthenticated, CanFollow]
    
    def post(self, request, user_id):
        user_to_unfollow = get_object_or_404(User, pk=user_id)
        
        try:
            follow = Follow.objects.get(
                follower=request.user,
                following=user_to_unfollow
            )
            follow.delete()
            
            # Atualizar contadores
            request.user.following_count -= 1
            request.user.save()
            user_to_unfollow.followers_count -= 1
            user_to_unfollow.save()
            
            return Response(
                {'message': f'Você deixou de seguir {user_to_unfollow.username}'},
                status=status.HTTP_200_OK
            )
        except Follow.DoesNotExist:
            return Response(
                {'error': 'Você não segue este usuário'},
                status=status.HTTP_400_BAD_REQUEST
            )

class FollowersListView(generics.ListAPIView):
    """Lista de seguidores"""
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Follow.objects.filter(following_id=user_id)

class FollowingListView(generics.ListAPIView):
    """Lista de quem o usuário segue"""
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Follow.objects.filter(follower_id=user_id)

class UserActivityView(generics.ListAPIView):
    """Histórico de atividades do usuário"""
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user)
