# backend/apps/chat/views.py
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer, MessageCreateSerializer
from apps.accounts.models import User
from apps.accounts.permissions import CanChat

class ChatRoomViewSet(viewsets.ModelViewSet):
    """ViewSet para salas de chat"""
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated, CanChat]
    
    def get_queryset(self):
        return ChatRoom.objects.filter(
            participants=self.request.user
        ).prefetch_related('participants', 'messages')
    
    @action(detail=False, methods=['post'])
    def create_private(self, request):
        """Criar sala privada com outro usuário"""
        other_user_id = request.data.get('user_id')
        other_user = get_object_or_404(User, pk=other_user_id)
        
        # Verificar se já existe sala entre os dois
        existing_room = ChatRoom.objects.filter(
            room_type='private',
            participants=request.user
        ).filter(
            participants=other_user
        ).first()
        
        if existing_room:
            serializer = self.get_serializer(existing_room)
            return Response(serializer.data)
        
        # Criar nova sala
        room = ChatRoom.objects.create(
            room_type='private',
            created_by=request.user
        )
        room.participants.add(request.user, other_user)
        
        serializer = self.get_serializer(room)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Listar mensagens da sala"""
        room = self.get_object()
        messages = room.messages.all().order_by('created_at')
        
        # Paginação
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Enviar mensagem para a sala"""
        room = self.get_object()
        serializer = MessageCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            message = Message.objects.create(
                room=room,
                sender=request.user,
                content=serializer.validated_data['content']
            )
            
            # Atualizar updated_at da sala
            room.save()
            
            return Response(
                MessageSerializer(message).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UnreadMessagesView(generics.ListAPIView):
    """Listar mensagens não lidas"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Message.objects.filter(
            room__participants=self.request.user
        ).exclude(
            sender=self.request.user
        ).exclude(
            read_by=self.request.user
        ).select_related('sender', 'room')