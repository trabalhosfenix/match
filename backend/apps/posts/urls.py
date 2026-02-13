# backend/apps/posts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'posts', views.PostViewSet, basename='post')

urlpatterns = [
    # Timeline e feeds
    path('timeline/', views.TimelineView.as_view(), name='timeline'),
    path('user/<int:user_id>/', views.UserPostsView.as_view(), name='user-posts'),
    path('saved/', views.SavedPostsView.as_view(), name='saved-posts'),
    
    # Incluir rotas do router
    path('', include(router.urls)),
]