# backend/apps/interactions/serializers.py
from rest_framework import serializers
from .models import Reaction, Comment, CommentReaction
from apps.accounts.serializers import UserSerializer

class ReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Reaction
        fields = ['id', 'user', 'reaction_type', 'created_at']
        read_only_fields = ['created_at']

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'post', 'content', 'parent',
            'reactions_count', 'replies_count',
            'is_edited', 'is_active', 'created_at', 'updated_at',
            'replies', 'user_reaction'
        ]
        read_only_fields = [
            'reactions_count', 'replies_count',
            'is_edited', 'created_at', 'updated_at'
        ]
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(
                obj.replies.filter(is_active=True)[:5],
                many=True,
                context=self.context
            ).data
        return []
    
    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                reaction = CommentReaction.objects.get(
                    user=request.user, 
                    comment=obj
                )
                return reaction.reaction_type
            except CommentReaction.DoesNotExist:
                pass
        return None

class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content', 'parent']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['post_id'] = self.context['post_id']
        return super().create(validated_data)