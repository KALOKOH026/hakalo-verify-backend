from django.contrib import admin
from .models import Institution, Customer, VerificationRequest, AuditLog


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'country', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'email']
    list_filter = ['is_active', 'created_at', 'country']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'country')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'website')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'national_id', 'institution', 'is_verified', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'national_id']
    list_filter = ['is_verified', 'created_at', 'gender', 'institution']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'national_id', 'date_of_birth', 'gender')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone')
        }),
        ('Address', {
            'fields': ('address', 'city', 'country')
        }),
        ('Institution & Verification', {
            'fields': ('institution', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Full Name'


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ['verification_code', 'customer_name', 'status', 'verification_method', 'created_at']
    search_fields = ['verification_code', 'customer__first_name', 'customer__last_name', 'customer__email']
    list_filter = ['status', 'verification_method', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'verification_code']
    fieldsets = (
        ('Verification Details', {
            'fields': ('customer', 'verification_code', 'status', 'verification_method')
        }),
        ('Verification Data', {
            'fields': ('verification_data',)
        }),
        ('Verification Result', {
            'fields': ('verified_by', 'verified_at', 'rejection_reason')
        }),
        ('Expiration', {
            'fields': ('expires_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"
    customer_name.short_description = 'Customer'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'model_name', 'object_repr', 'username', 'created_at']
    search_fields = ['user__username', 'action', 'model_name', 'object_repr', 'description']
    list_filter = ['action', 'model_name', 'created_at']
    readonly_fields = ['created_at', 'user', 'action', 'model_name', 'object_id', 'old_values', 'new_values', 'ip_address', 'user_agent', 'description']
    fieldsets = (
        ('Action Information', {
            'fields': ('action', 'user', 'model_name')
        }),
        ('Object Details', {
            'fields': ('object_id', 'object_repr')
        }),
        ('Change Data', {
            'fields': ('old_values', 'new_values')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Additional Info', {
            'fields': ('description', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Audit logs should only be created programmatically
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of audit logs for compliance
        return False

    def has_change_permission(self, request, obj=None):
        # Audit logs should be read-only
        return False

    def username(self, obj):
        return obj.user.username if obj.user else 'System'
    username.short_description = 'User'
