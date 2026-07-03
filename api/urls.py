from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InstitutionViewSet, CustomerViewSet, VerificationRequestViewSet,
    AuditLogViewSet
)

router = DefaultRouter()
router.register(r'institutions', InstitutionViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'verifications', VerificationRequestViewSet)
router.register(r'audit-logs', AuditLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
