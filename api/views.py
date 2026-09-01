from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta

from .models import Institution, Customer, VerificationRequest, AuditLog
from .serializers import (
    InstitutionSerializer, CustomerSerializer, VerificationRequestSerializer,
    AuditLogSerializer
)
from .permissions import IsPlatformAdmin, IsMfiStaff, IsMfiAdmin, IsInstitutionScopedObject


class InstitutionViewSet(viewsets.ModelViewSet):
    """ViewSet for Institution model"""
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated, IsInstitutionScopedObject]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'country']
    search_fields = ['name', 'code', 'email']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsPlatformAdmin]
        else:
            permission_classes = [IsAuthenticated, IsInstitutionScopedObject]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Institution.objects.none()
        if getattr(user, 'is_superuser', False):
            return Institution.objects.all()
        membership = getattr(user, 'institution_membership', None)
        if membership and membership.is_active:
            return Institution.objects.filter(pk=membership.institution_id)
        return Institution.objects.none()


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for Customer model"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsInstitutionScopedObject]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['institution', 'is_verified', 'gender']
    search_fields = ['first_name', 'last_name', 'email', 'national_id', 'phone']
    ordering_fields = ['created_at', 'first_name', 'last_name']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsPlatformAdmin]
        elif self.action in ['mark_verified']:
            permission_classes = [IsAuthenticated, IsMfiAdmin]
        else:
            permission_classes = [IsAuthenticated, IsInstitutionScopedObject]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Customer.objects.none()
        if getattr(user, 'is_superuser', False):
            return Customer.objects.all()
        membership = getattr(user, 'institution_membership', None)
        if membership and membership.is_active:
            return Customer.objects.filter(institution_id=membership.institution_id)
        return Customer.objects.none()

    @action(detail=False, methods=['get'])
    def unverified(self, request):
        """Get all unverified customers"""
        queryset = self.get_queryset().filter(is_verified=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_verified(self, request, pk=None):
        """Mark a customer as verified"""
        customer = self.get_object()
        customer.is_verified = True
        customer.save()
        
        # Log action
        AuditLog.objects.create(
            user=request.user,
            action='VERIFY',
            model_name='Customer',
            object_id=str(customer.id),
            object_repr=str(customer),
            description=f'Marked customer as verified {customer.first_name} {customer.last_name}',
            ip_address=self.get_client_ip(request),
            institution=customer.institution
        )
        
        return Response({'status': 'customer marked as verified'})

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class VerificationRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for VerificationRequest model"""
    queryset = VerificationRequest.objects.all()
    serializer_class = VerificationRequestSerializer
    permission_classes = [IsAuthenticated, IsInstitutionScopedObject]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'verification_method']
    search_fields = ['verification_code', 'customer__first_name', 'customer__last_name', 'customer__email']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAuthenticated, IsPlatformAdmin]
        elif self.action in ['approve', 'reject']:
            permission_classes = [IsAuthenticated, IsMfiAdmin]
        else:
            permission_classes = [IsAuthenticated, IsInstitutionScopedObject]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return VerificationRequest.objects.none()
        if getattr(user, 'is_superuser', False):
            return VerificationRequest.objects.all()
        membership = getattr(user, 'institution_membership', None)
        if membership and membership.is_active:
            return VerificationRequest.objects.filter(requesting_institution_id=membership.institution_id)
        return VerificationRequest.objects.none()

    def get_object(self):
        """
        Override to ensure customer belongs to the verification's institution.
        This provides defense-in-depth against data corruption or edge cases.
        """
        obj = super().get_object()
        
        # Validate that customer's institution matches verification's requesting_institution
        if obj.customer.institution_id != obj.requesting_institution_id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Verification request customer does not belong to the requesting institution. "
                "Data integrity issue detected."
            )
        
        return obj

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending verification requests"""
        pending = self.get_queryset().filter(status='PENDING')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a verification request"""
        verification = self.get_object()
        verification.status = 'APPROVED'
        verification.verified_by = request.user
        verification.verified_at = timezone.now()
        verification.save()
        
        # Mark customer as verified
        verification.customer.is_verified = True
        verification.customer.save()
        
        # Log action
        AuditLog.objects.create(
            user=request.user,
            action='VERIFY',
            model_name='VerificationRequest',
            object_id=str(verification.id),
            object_repr=str(verification),
            description=f'Approved verification request {verification.verification_code}',
            ip_address=self.get_client_ip(request),
            institution=verification.requesting_institution
        )
        
        return Response({
            'status': 'verification approved',
            'data': self.get_serializer(verification).data
        })

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a verification request"""
        verification = self.get_object()
        reason = request.data.get('reason', 'No reason provided')
        
        verification.status = 'REJECTED'
        verification.rejection_reason = reason
        verification.verified_by = request.user
        verification.verified_at = timezone.now()
        verification.save()
        
        # Log action
        AuditLog.objects.create(
            user=request.user,
            action='REJECT',
            model_name='VerificationRequest',
            object_id=str(verification.id),
            object_repr=str(verification),
            description=f'Rejected verification request {verification.verification_code}: {reason}',
            ip_address=self.get_client_ip(request),
            institution=verification.requesting_institution
        )
        
        return Response({
            'status': 'verification rejected',
            'data': self.get_serializer(verification).data
        })

    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Get all expired verification requests"""
        now = timezone.now()
        expired = self.get_queryset().filter(expires_at__lt=now, status__in=['PENDING', 'IN_PROGRESS'])
        serializer = self.get_serializer(expired, many=True)
        return Response(serializer.data)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AuditLog model (Read-only)"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsMfiAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'model_name', 'user']
    search_fields = ['description', 'object_repr', 'user__username']
    ordering_fields = ['created_at', 'action']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return AuditLog.objects.none()
        if getattr(user, 'is_superuser', False):
            return AuditLog.objects.all()
        membership = getattr(user, 'institution_membership', None)
        if membership and membership.is_active:
            return AuditLog.objects.filter(institution_id=membership.institution_id)
        return AuditLog.objects.none()

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent audit logs from last 24 hours"""
        yesterday = timezone.now() - timedelta(days=1)
        recent_logs = self.get_queryset().filter(created_at__gte=yesterday)
        serializer = self.get_serializer(recent_logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Get audit logs for a specific user"""
        username = request.query_params.get('username')
        if not username:
            return Response({'error': 'username parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        logs = self.get_queryset().filter(user__username=username)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
