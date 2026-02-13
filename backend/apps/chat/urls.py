# backend/apps/chat/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'rooms', views.ChatRoomViewSet, basename='chat-room')

urlpatterns = [
    path('', include(router.urls)),
    path('unread/', views.UnreadMessagesView.as_view(), name='unread-messages'),
]