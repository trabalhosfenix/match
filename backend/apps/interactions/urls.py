from django.urls import path, include
from rest_framework_nested import routers
from rest_framework.routers import DefaultRouter
from . import views
from apps.posts.views import PostViewSet

# Router principal com resource registrado
router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')

# Nested router para reactions e comments
posts_router = routers.NestedDefaultRouter(router, r'posts', lookup='post')
posts_router.register(r'reactions', views.ReactionViewSet, basename='post-reactions')
posts_router.register(r'comments', views.CommentViewSet, basename='post-comments')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(posts_router.urls)),
]