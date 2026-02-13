# backend/apps/accounts/permissions.py
from rest_framework import permissions
from .models import UserLevel

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permissão para apenas o dono editar"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user

class CanFollow(permissions.BasePermission):
    """Verifica se usuário pode seguir outros"""
    
    def has_permission(self, request, view):
        return request.user.can_follow()

class IsAnonimo(permissions.BasePermission):
    """Verifica se é anônimo"""
    
    def has_permission(self, request, view):
        return request.user.level == UserLevel.ANONIMO

class CanPost(permissions.BasePermission):
    """Verifica se pode postar"""
    
    def has_permission(self, request, view):
        return request.user.can_post()

class CanReact(permissions.BasePermission):
    """Verifica se pode reagir"""
    
    def has_permission(self, request, view):
        return request.user.can_react()

class CanComment(permissions.BasePermission):
    """Verifica se pode comentar"""
    
    def has_permission(self, request, view):
        return request.user.can_comment()

class CanChat(permissions.BasePermission):
    """Verifica se pode usar chat"""
    
    def has_permission(self, request, view):
        return request.user.can_chat()

class CanViewContent(permissions.BasePermission):
    """Verifica se pode visualizar conteúdo social"""

    def has_permission(self, request, view):
        return request.user.level != UserLevel.ANONIMO
