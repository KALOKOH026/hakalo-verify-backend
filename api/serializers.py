from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Institution, Customer, VerificationRequest, AuditLog


class InstitutionSerializer(serializers.ModelSerializer):
    """Serializer for Institution model"""
    class Meta:
        model = Institution
        fields = ['id', 'name', 'code', 'country', 'website', 'email', 'phone', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model"""
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = ['id', 'institution', 'institution_name', 'full_name', 'first_name', 'last_name', 
                  'email', 'phone', 'national_id', 'date_of_birth', 'gender', 'address', 'city', 
                  'country', 'is_verified', 'created_at', 'updated_at']
        read_only_fields = ['id', 'institution', 'created_at', 'updated_at', 'is_verified']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = getattr(request.user, 'institution_membership', None)
            institution_id = self.initial_data.get('institution')
            if request.user.is_superuser and institution_id:
                validated_data['institution'] = Institution.objects.get(pk=institution_id)
            elif membership and membership.is_active:
                validated_data['institution'] = membership.institution
            elif institution_id:
                validated_data['institution'] = Institution.objects.get(pk=institution_id)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('institution', None)
        return super().update(instance, validated_data)


class VerificationRequestSerializer(serializers.ModelSerializer):
    """Serializer for VerificationRequest model"""
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    verified_by_username = serializers.CharField(source='verified_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = VerificationRequest
        fields = ['id', 'customer', 'customer_name', 'verification_code', 'status', 'verification_method',
                  'verification_data', 'requested_by', 'requesting_institution', 'verified_by', 'verified_by_username', 'verified_at', 
                  'rejection_reason', 'expires_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'requested_by', 'requesting_institution', 'verification_code', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = getattr(request.user, 'institution_membership', None)
            validated_data['requested_by'] = request.user
            if membership and membership.is_active:
                validated_data['requesting_institution'] = membership.institution
            elif 'customer' in validated_data and validated_data['customer'].institution_id:
                validated_data['requesting_institution'] = validated_data['customer'].institution
            elif request.data.get('requesting_institution'):
                validated_data['requesting_institution'] = Institution.objects.get(pk=request.data.get('requesting_institution'))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('requested_by', None)
        validated_data.pop('requesting_institution', None)
        return super().update(instance, validated_data)


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model"""
    username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'institution', 'username', 'action', 'action_display', 'model_name', 'object_id', 
                  'object_repr', 'old_values', 'new_values', 'ip_address', 'user_agent', 
                  'description', 'created_at']
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
        read_only_fields = ['id']
