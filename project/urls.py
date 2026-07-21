from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse

@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'service': 'Hakalo Verify Backend',
        'version': '1.0.0'
    })

@api_view(['GET'])
def api_root(request):
    """API root with documentation"""
    return Response({
        'message': 'Hakalo Microfinance Loan Borrower Verification Platform',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/',
            'institutions': '/api/institutions/',
            'customers': '/api/customers/',
            'verifications': '/api/verifications/',
            'audit_logs': '/api/audit-logs/',
            'token': {
                'obtain': '/api/token/',
                'refresh': '/api/token/refresh/',
            }
        },
        'authentication': 'JWT Bearer Token',
        'documentation': 'See endpoints above'
    })

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Health check
    path("health/", health_check, name="health_check"),
    
    # API Root
    path("", api_root, name="api_root"),

    # JWT endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # API routes
    path("api/", include("api.urls")),
]
