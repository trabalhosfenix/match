# backend/apps/payments/views.py
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db import transaction

from .models import Plan, Subscription, Payment
from .serializers import (
    PlanSerializer, SubscriptionSerializer,
    PaymentSerializer, PaymentCreateSerializer
)
from apps.accounts.models import UserActivity, UserLevel

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """Listar planos disponíveis"""
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticated]

class SubscriptionViewSet(viewsets.GenericViewSet):
    """Gerenciar assinaturas"""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_subscription(self, request):
        """Ver minha assinatura atual"""
        try:
            subscription = Subscription.objects.get(user=request.user)
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            return Response(
                {'message': 'Nenhuma assinatura ativa'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def cancel(self, request):
        """Cancelar assinatura"""
        try:
            subscription = Subscription.objects.get(user=request.user)
            subscription.status = 'cancelled'
            subscription.auto_renew = False
            subscription.save()
            
            return Response({'message': 'Assinatura cancelada com sucesso'})
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'Nenhuma assinatura encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

class PaymentViewSet(viewsets.GenericViewSet):
    """Processar pagamentos"""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def process(self, request):
        """Processar pagamento e upgrade"""
        serializer = PaymentCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        plan = Plan.objects.get(id=serializer.validated_data['plan_id'])
        
        # Validar upgrade (não pode fazer downgrade aqui)
        if self._get_level_value(request.user.level) >= self._get_level_value(plan.level):
            return Response(
                {'error': 'Você já possui um nível igual ou superior'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Criar pagamento
        payment = Payment.objects.create(
            user=request.user,
            plan=plan,
            amount=plan.price,
            payment_method=serializer.validated_data['payment_method'],
            status='processing',
            metadata={
                'user_level_before': request.user.level,
                'target_level': plan.level
            }
        )
        
        # TODO: Integrar com gateway de pagamento aqui
        # Simulação de pagamento bem sucedido
        payment.status = 'completed'
        payment.transaction_id = f"TXN{payment.id}{timezone.now().strftime('%Y%m%d%H%M%S')}"
        payment.processed_at = timezone.now()
        payment.save()
        
        # Atualizar ou criar assinatura
        subscription, created = Subscription.objects.update_or_create(
            user=request.user,
            defaults={
                'plan': plan,
                'status': 'active',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timezone.timedelta(days=plan.duration_days),
                'auto_renew': False
            }
        )
        
        payment.subscription = subscription
        payment.save()
        
        # Fazer upgrade do usuário
        old_level = request.user.level
        request.user.level = plan.level
        request.user.save()
        
        # Registrar atividade
        UserActivity.objects.create(
            user=request.user,
            activity_type='upgrade',
            metadata={
                'from_level': old_level,
                'to_level': plan.level,
                'payment_id': payment.id,
                'plan_name': plan.name,
                'amount': float(plan.price)
            }
        )
        
        return Response({
            'message': f'Upgrade para {plan.name} realizado com sucesso!',
            'payment': PaymentSerializer(payment).data,
            'subscription': SubscriptionSerializer(subscription).data,
            'new_level': request.user.level
        }, status=status.HTTP_201_CREATED)
    
    def _get_level_value(self, level):
        """Converte nível para valor numérico para comparação"""
        values = {
            UserLevel.ANONIMO: 0,
            UserLevel.USER: 1,
            UserLevel.PLUS: 2,
            UserLevel.PRO: 3
        }
        return values.get(level, 0)