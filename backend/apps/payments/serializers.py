# backend/apps/payments/serializers.py
from rest_framework import serializers
from .models import Plan, Subscription, Payment

class PlanSerializer(serializers.ModelSerializer):
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'level', 'level_display',
            'price', 'duration_days', 'features', 'is_active'
        ]

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'plan', 'status',
            'start_date', 'end_date', 'auto_renew',
            'is_active', 'created_at'
        ]

class PaymentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'subscription', 'plan', 'plan_name',
            'amount', 'payment_method', 'status',
            'transaction_id', 'created_at', 'processed_at'
        ]
        read_only_fields = ['status', 'transaction_id', 'processed_at']

class PaymentCreateSerializer(serializers.Serializer):
    """Serializer para criar um pagamento"""
    plan_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=Payment.PAYMENT_METHODS)
    
    def validate_plan_id(self, value):
        try:
            plan = Plan.objects.get(id=value, is_active=True)
        except Plan.DoesNotExist:
            raise serializers.ValidationError("Plano não encontrado ou inativo")
        return value