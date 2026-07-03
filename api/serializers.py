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
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_verified']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class VerificationRequestSerializer(serializers.ModelSerializer):
    """Serializer for VerificationRequest model"""
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    verified_by_username = serializers.CharField(source='verified_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = VerificationRequest
        fields = ['id', 'customer', 'customer_name', 'verification_code', 'status', 'verification_method',
                  'verification_data', 'verified_by', 'verified_by_username', 'verified_at', 
                  'rejection_reason', 'expires_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'verification_code', 'created_at', 'updated_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model"""
    username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'username', 'action', 'action_display', 'model_name', 'object_id', 
                  'object_repr', 'old_values', 'new_values', 'ip_address', 'user_agent', 
                  'description', 'created_at']
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
        read_only_fields = ['id']
