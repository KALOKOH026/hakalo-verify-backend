from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Institution, Customer, VerificationRequest, AuditLog


class InstitutionAPITests(APITestCase):
    """Test cases for Institution API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="adminpass123",
            email="admin@example.com"
        )
        self.institution = Institution.objects.create(
            name="Test Bank",
            code="TSB001",
            country="Kenya",
            email="info@testbank.com"
        )

    def test_institution_list_requires_auth(self):
        """Test institution list requires authentication"""
        response = self.client.get("/api/institutions/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_institution_list_authenticated_user(self):
        """Test institution list for authenticated user"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/institutions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_institution_create_requires_admin(self):
        """Test institution creation requires admin permission"""
        self.client.force_authenticate(user=self.user)
        data = {
            "name": "New Bank",
            "code": "NB001",
            "country": "Kenya"
        }
        response = self.client.post("/api/institutions/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_institution_create_by_admin(self):
        """Test institution creation by admin user"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "name": "New Bank",
            "code": "NB001",
            "country": "Kenya",
            "email": "info@newbank.com"
        }
        response = self.client.post("/api/institutions/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Institution.objects.count(), 2)

    def test_institution_detail_view(self):
        """Test institution detail view"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/institutions/{self.institution.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Bank")

    def test_institution_search(self):
        """Test institution search functionality"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/institutions/?search=Test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_institution_filter_by_country(self):
        """Test institution filter by country"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/institutions/?country=Kenya")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)


class CustomerAPITests(APITestCase):
    """Test cases for Customer API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="adminpass123",
            email="admin@example.com"
        )
        self.institution = Institution.objects.create(
            name="Test Bank",
            code="TSB001",
            country="Kenya"
        )
        self.customer = Customer.objects.create(
            institution=self.institution,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+254700000000",
            national_id="12345678",
            date_of_birth="1990-01-15",
            gender="M",
            address="123 Main St",
            city="Nairobi",
            country="Kenya"
        )

    def test_customer_list_requires_auth(self):
        """Test customer list requires authentication"""
        response = self.client.get("/api/customers/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_list_authenticated_user(self):
        """Test customer list for authenticated user"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/customers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_customer_create_by_admin(self):
        """Test customer creation by admin user"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "institution": self.institution.id,
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "phone": "+254700000001",
            "national_id": "87654321",
            "date_of_birth": "1991-02-20",
            "gender": "F",
            "address": "456 Oak St",
            "city": "Mombasa",
            "country": "Kenya"
        }
        response = self.client.post("/api/customers/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), 2)

    def test_customer_unverified_endpoint(self):
        """Test get unverified customers endpoint"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/customers/unverified/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_customer_mark_verified(self):
        """Test mark customer as verified"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f"/api/customers/{self.customer.id}/mark_verified/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.is_verified)

    def test_customer_search_by_email(self):
        """Test customer search by email"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/customers/?search=john")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)


class VerificationRequestAPITests(APITestCase):
    """Test cases for VerificationRequest API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="adminpass123",
            email="admin@example.com"
        )
        self.institution = Institution.objects.create(
            name="Test Bank",
            code="TSB001",
            country="Kenya"
        )
        self.customer = Customer.objects.create(
            institution=self.institution,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+254700000000",
            national_id="12345678",
            date_of_birth="1990-01-15",
            gender="M",
            address="123 Main St",
            city="Nairobi",
            country="Kenya"
        )
        self.verification = VerificationRequest.objects.create(
            customer=self.customer,
            verification_code="VER-2026-000001",
            status="PENDING"
        )

    def test_verification_pending_endpoint(self):
        """Test get pending verifications endpoint"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/verifications/pending/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_verification_approve(self):
        """Test approve verification endpoint"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f"/api/verifications/{self.verification.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, "APPROVED")
        self.assertEqual(self.verification.verified_by, self.admin_user)

    def test_verification_reject(self):
        """Test reject verification endpoint"""
        self.client.force_authenticate(user=self.admin_user)
        data = {"reason": "Missing documents"}
        response = self.client.post(
            f"/api/verifications/{self.verification.id}/reject/",
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, "REJECTED")
        self.assertEqual(self.verification.rejection_reason, "Missing documents")

    def test_verification_approve_marks_customer_verified(self):
        """Test that approving verification marks customer as verified"""
        self.client.force_authenticate(user=self.admin_user)
        self.client.post(f"/api/verifications/{self.verification.id}/approve/")
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.is_verified)


class AuditLogAPITests(APITestCase):
    """Test cases for AuditLog API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="adminpass123",
            email="admin@example.com"
        )
        self.audit_log = AuditLog.objects.create(
            user=self.admin_user,
            action="CREATE",
            model_name="Customer",
            object_id="1",
            object_repr="John Doe",
            description="Created new customer"
        )

    def test_audit_log_requires_admin(self):
        """Test audit log list requires admin permission"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/audit-logs/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_audit_log_list_by_admin(self):
        """Test audit log list for admin user"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/audit-logs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_audit_log_recent_endpoint(self):
        """Test get recent audit logs endpoint"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/audit-logs/recent/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_audit_log_by_user_endpoint(self):
        """Test get audit logs by user endpoint"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/audit-logs/by_user/?username=admin")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_audit_log_read_only(self):
        """Test audit logs cannot be created via API"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "action": "CREATE",
            "model_name": "Customer",
            "object_id": "2"
        }
        response = self.client.post("/api/audit-logs/", data)
        # Should not allow POST (read-only)
        self.assertIn(response.status_code, [status.HTTP_405_METHOD_NOT_ALLOWED])
