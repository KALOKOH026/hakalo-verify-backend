from django.contrib import admin
from django.contrib.auth.models import User
from .models import Institution, InstitutionMembership, Customer, VerificationRequest, AuditLog


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'country', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'email']
    list_filter = ['is_active', 'created_at', 'country']
    readonly_fields = ['created_at', 'updated_at']

    def has_module_permission(self, request):
        return request.user.is_active and (request.user.is_superuser or self._is_institution_admin(request.user))

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request) and (request.user.is_superuser or self._can_access_institution(request.user, obj))

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request) and (request.user.is_superuser or self._can_access_institution(request.user, obj))

    def has_add_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        membership = getattr(request.user, 'institution_membership', None)
        if membership and membership.is_active:
            return qs.filter(pk=membership.institution_id)
        return qs.none()

    def _is_institution_admin(self, user):
        membership = getattr(user, 'institution_membership', None)
        return bool(membership and membership.is_active and membership.role == 'MFI_ADMIN')

    def _can_access_institution(self, user, obj):
        if user.is_superuser:
            return True
        membership = getattr(user, 'institution_membership', None)
        if not membership or not membership.is_active:
            return False
        if obj is None:
            return True
        return obj.pk == membership.institution_id
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


@admin.register(InstitutionMembership)
class InstitutionMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'institution', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'institution']
    search_fields = ['user__username', 'user__email', 'institution__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'national_id', 'institution', 'is_verified', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'national_id']
    list_filter = ['is_verified', 'created_at', 'gender', 'institution']
    readonly_fields = ['created_at', 'updated_at']

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            readonly_fields.append('institution')
        return readonly_fields

    def has_module_permission(self, request):
        return request.user.is_active and (request.user.is_superuser or self._is_institution_admin(request.user))

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request) and (request.user.is_superuser or self._can_access_customer(request.user, obj))

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request) and (request.user.is_superuser or self._can_access_customer(request.user, obj))

    def has_add_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        membership = getattr(request.user, 'institution_membership', None)
        if membership and membership.is_active:
            return qs.filter(institution_id=membership.institution_id)
        return qs.none()

    def _is_institution_admin(self, user):
        membership = getattr(user, 'institution_membership', None)
        return bool(membership and membership.is_active and membership.role == 'MFI_ADMIN')

    def _can_access_customer(self, user, obj):
        if user.is_superuser:
            return True
        membership = getattr(user, 'institution_membership', None)
        if not membership or not membership.is_active:
            return False
        if obj is None:
            return True
        return obj.institution_id == membership.institution_id
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

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser
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
