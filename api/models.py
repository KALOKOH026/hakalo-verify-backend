from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        now = timezone.now()
        if self._state.adding:
            if not getattr(self, 'created_at', None):
                self.created_at = now
            self.updated_at = self.created_at or now
        else:
            self.updated_at = now
        super().save(*args, **kwargs)


class Institution(TimestampedModel):
    """Model representing financial institutions"""
    name = models.CharField(max_length=255, unique=True, null=False)
    code = models.CharField(max_length=50, unique=True, null=False)
    country = models.CharField(max_length=100)
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Institution'
        verbose_name_plural = 'Institutions'

    def __str__(self):
        return f"{self.name} ({self.code})"


class InstitutionMembership(TimestampedModel):
    """Link a Django user to exactly one institution with a role."""
    ROLE_CHOICES = [
        ('MFI_STAFF', 'MFI Staff'),
        ('MFI_ADMIN', 'MFI Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='institution_membership')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MFI_STAFF')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Institution Membership'
        verbose_name_plural = 'Institution Memberships'
        constraints = [
            models.UniqueConstraint(fields=['user', 'institution'], name='unique_user_institution_membership')
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.institution.name} ({self.role})"


class Customer(TimestampedModel):
    """Model representing customers/borrowers"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='customers')
    first_name = models.CharField(max_length=100, null=False)
    last_name = models.CharField(max_length=100, null=False)
    email = models.EmailField(unique=True, null=False)
    phone = models.CharField(max_length=20, null=False)
    national_id = models.CharField(max_length=50, unique=True, null=False)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        unique_together = ['institution', 'national_id']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.national_id})"


class VerificationRequest(TimestampedModel):
    """Model for customer verification requests"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='verification_requests')
    verification_code = models.CharField(max_length=100, unique=True, null=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    verification_method = models.CharField(max_length=50, default='EMAIL')
    verification_data = models.JSONField(null=True, blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='requested_verifications')
    requesting_institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, related_name='verification_requests')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_requests')
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Verification Request'
        verbose_name_plural = 'Verification Requests'

    def __str__(self):
        return f"Verification {self.verification_code} - {self.status}"


class AuditLog(TimestampedModel):
    """Model for audit trail and compliance logging"""
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('VERIFY', 'Verify'),
        ('REJECT', 'Reject'),
        ('EXPORT', 'Export'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=255, blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        return f"{self.action} - {self.model_name}({self.object_id}) - {self.created_at}"
