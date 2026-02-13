# backend/apps/posts/serializers.py
from rest_framework import serializers
from .models import Post, Media, SavedPost, Report
from apps.accounts.serializers import UserSerializer

class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ['id', 'file', 'media_type', 'order']

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    media = MediaSerializer(many=True, read_only=True)
    user_reaction = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content', 'media',
            'tags', 'region', 'reactions_count',
            'comments_count', 'shares_count', 'views_count',
            'is_edited', 'created_at', 'updated_at',
            'user_reaction'
        ]
        read_only_fields = [
            'reactions_count', 'comments_count', 
            'shares_count', 'views_count', 'is_edited'
        ]
    
    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from apps.interactions.models import Reaction
            try:
                reaction = Reaction.objects.get(user=request.user, post=obj)
                return reaction.reaction_type
            except Reaction.DoesNotExist:
                pass
        return None

class PostCreateSerializer(serializers.ModelSerializer):
    media = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Post
        fields = ['content', 'tags', 'region', 'media']
    
    def create(self, validated_data):
        media_files = validated_data.pop('media', [])
        validated_data['author'] = self.context['request'].user
        
        post = Post.objects.create(**validated_data)
        
        # Processar mídia
        for order, media_file in enumerate(media_files):
            media_type = 'image'
            if hasattr(media_file, 'content_type'):
                if 'video' in media_file.content_type:
                    media_type = 'video'
                elif 'gif' in media_file.content_type:
                    media_type = 'gif'
            
            Media.objects.create(
                post=post,
                file=media_file,
                media_type=media_type,
                order=order
            )
        
        return post

class SavedPostSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    
    class Meta:
        model = SavedPost
        fields = ['id', 'post', 'created_at']

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'reason', 'description', 'created_at', 'is_resolved']
        read_only_fields = ['is_resolved', 'created_at']