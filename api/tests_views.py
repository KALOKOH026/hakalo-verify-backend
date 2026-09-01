from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import RequestFactory
from .admin import CustomerAdmin, InstitutionAdmin
from .models import Institution, InstitutionMembership, Customer, VerificationRequest, AuditLog


class AdminPermissionTests(APITestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.institution_a = Institution.objects.create(name='Admin MFI A', code='ADMFA', country='Kenya')
        self.institution_b = Institution.objects.create(name='Admin MFI B', code='ADMFB', country='Kenya')
        self.admin_user = User.objects.create_user(username='adminuser', password='testpass123')
        self.staff_user = User.objects.create_user(username='staffuser', password='testpass123')
        InstitutionMembership.objects.create(user=self.admin_user, institution=self.institution_a, role='MFI_ADMIN')
        InstitutionMembership.objects.create(user=self.staff_user, institution=self.institution_a, role='MFI_STAFF')
        self.customer = Customer.objects.create(
            institution=self.institution_a,
            first_name='Ada',
            last_name='Lovelace',
            email='ada@example.com',
            phone='000',
            national_id='ADA1',
            date_of_birth='1990-01-01',
            gender='F',
            address='x',
            city='n',
            country='Kenya',
        )
        self.other_customer = Customer.objects.create(
            institution=self.institution_b,
            first_name='Grace',
            last_name='Hopper',
            email='grace@example.com',
            phone='111',
            national_id='GH1',
            date_of_birth='1990-01-02',
            gender='F',
            address='x',
            city='n',
            country='Kenya',
        )

    def make_request(self, user):
        request = self.factory.get('/admin/')
        request.user = user
        return request

    def test_mfi_admin_can_manage_own_institution_records(self):
        customer_admin = CustomerAdmin(model=Customer, admin_site=self.site)
        request = self.make_request(self.admin_user)
        self.assertTrue(customer_admin.has_module_permission(request))
        self.assertTrue(customer_admin.has_view_permission(request, self.customer))
        self.assertTrue(customer_admin.has_change_permission(request, self.customer))
        self.assertFalse(customer_admin.has_change_permission(request, self.other_customer))

    def test_mfi_staff_cannot_access_admin_ui(self):
        customer_admin = CustomerAdmin(model=Customer, admin_site=self.site)
        request = self.make_request(self.staff_user)
        self.assertFalse(customer_admin.has_module_permission(request))
        self.assertFalse(customer_admin.has_view_permission(request, self.customer))
        self.assertFalse(customer_admin.has_change_permission(request, self.customer))

    def test_institution_admin_queryset_is_scoped_to_own_institution(self):
        institution_admin = InstitutionAdmin(model=Institution, admin_site=self.site)
        request = self.make_request(self.admin_user)
        queryset = institution_admin.get_queryset(request)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().id, self.institution_a.id)


class SeedCommandTests(APITestCase):
    def test_seed_dev_data_creates_synthetic_records(self):
        call_command('seed_dev_data')
        self.assertGreaterEqual(Institution.objects.count(), 2)
        self.assertGreaterEqual(Customer.objects.count(), 2)
        self.assertGreaterEqual(VerificationRequest.objects.count(), 1)


class AdminPolicyFixtureMatrixTests(APITestCase):
    fixtures = ['admin_policy_matrix']

    def setUp(self):
        self.platform_admin = User.objects.get(username='platform-admin')
        self.mfi_admin = User.objects.get(username='mfi-admin')
        self.mfi_staff = User.objects.get(username='mfi-staff')
        self.institution_a = Institution.objects.get(code='MFIA')
        self.institution_b = Institution.objects.get(code='MFIB')
        self.own_customer = Customer.objects.get(national_id='MFIA-001')
        self.other_customer = Customer.objects.get(national_id='MFIB-001')
        self.audit_log = AuditLog.objects.get(description='Synthetic audit for MFI A')

    def _request_for(self, user):
        request = RequestFactory().get('/admin/')
        request.user = user
        return request

    def test_platform_admin_has_authorized_platform_level_access(self):
        request = self._request_for(self.platform_admin)
        institution_admin = InstitutionAdmin(model=Institution, admin_site=admin.site)
        customer_admin = CustomerAdmin(model=Customer, admin_site=admin.site)
        audit_admin = admin.site._registry[AuditLog]

        self.assertTrue(institution_admin.has_module_permission(request))
        self.assertTrue(customer_admin.has_module_permission(request))
        self.assertTrue(customer_admin.has_view_permission(request, self.other_customer))
        self.assertTrue(audit_admin.has_view_permission(request, self.audit_log))
        self.assertTrue(institution_admin.has_add_permission(request))

    def test_mfi_admin_is_restricted_to_their_institution(self):
        request = self._request_for(self.mfi_admin)
        institution_admin = InstitutionAdmin(model=Institution, admin_site=admin.site)
        customer_admin = CustomerAdmin(model=Customer, admin_site=admin.site)
        queryset = customer_admin.get_queryset(request)

        self.assertTrue(customer_admin.has_view_permission(request, self.own_customer))
        self.assertFalse(customer_admin.has_view_permission(request, self.other_customer))
        self.assertEqual(queryset.count(), 1)
        self.assertTrue(queryset.filter(pk=self.own_customer.pk).exists())
        self.assertFalse(queryset.filter(pk=self.other_customer.pk).exists())
        self.assertEqual(institution_admin.get_queryset(request).count(), 1)

    def test_mfi_staff_cannot_perform_mfi_admin_actions(self):
        request = self._request_for(self.mfi_staff)
        customer_admin = CustomerAdmin(model=Customer, admin_site=admin.site)
        institution_admin = InstitutionAdmin(model=Institution, admin_site=admin.site)

        self.assertFalse(customer_admin.has_change_permission(request, self.own_customer))
        self.assertFalse(customer_admin.has_add_permission(request))
        self.assertFalse(customer_admin.has_delete_permission(request, self.own_customer))
        self.assertFalse(institution_admin.has_change_permission(request, self.institution_a))
        self.assertFalse(institution_admin.has_delete_permission(request, self.institution_a))

    def test_mfi_users_cannot_access_another_institutions_admin_data(self):
        request = self._request_for(self.mfi_admin)
        customer_admin = CustomerAdmin(model=Customer, admin_site=admin.site)
        institution_admin = InstitutionAdmin(model=Institution, admin_site=admin.site)

        self.assertFalse(customer_admin.has_view_permission(request, self.other_customer))
        self.assertFalse(institution_admin.has_view_permission(request, self.institution_b))
        self.assertTrue(customer_admin.get_queryset(request).filter(pk=self.own_customer.pk).exists())
        self.assertFalse(customer_admin.get_queryset(request).filter(pk=self.other_customer.pk).exists())

    def test_audit_logs_cannot_be_modified_or_deleted_by_mfi_users(self):
        request = self._request_for(self.mfi_admin)
        audit_admin = admin.site._registry[AuditLog]

        self.assertFalse(audit_admin.has_module_permission(request))
        self.assertFalse(audit_admin.has_view_permission(request, self.audit_log))
        self.assertFalse(audit_admin.has_change_permission(request, self.audit_log))
        self.assertFalse(audit_admin.has_delete_permission(request, self.audit_log))

    def test_institution_ownership_cannot_be_changed_by_unauthorized_mfi_users(self):
        request = self._request_for(self.mfi_admin)
        customer_admin = CustomerAdmin(model=Customer, admin_site=admin.site)

        self.assertIn('institution', customer_admin.get_readonly_fields(request, self.own_customer))
        self.assertIn('institution', customer_admin.get_readonly_fields(request, self.other_customer))


class InstitutionIsolationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.institution_a = Institution.objects.create(name='MFI A', code='MFIA', country='Kenya')
        self.institution_b = Institution.objects.create(name='MFI B', code='MFIB', country='Kenya')
        self.staff_user = User.objects.create_user(username='staffa', password='testpass123')
        self.admin_user = User.objects.create_user(username='admina', password='testpass123')
        self.platform_admin = User.objects.create_superuser(username='platform', password='platformpass123', email='platform@example.com')
        InstitutionMembership.objects.create(user=self.staff_user, institution=self.institution_a, role='MFI_STAFF')
        InstitutionMembership.objects.create(user=self.admin_user, institution=self.institution_a, role='MFI_ADMIN')

    def test_mfi_staff_can_only_view_own_institution(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/institutions/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.institution_a.id)

    def test_mfi_staff_cannot_access_other_institution_detail(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f'/api/institutions/{self.institution_b.id}/')
        self.assertIn(response.status_code, [403, 404])

    def test_customer_isolation_for_mfi_user(self):
        customer_a = Customer.objects.create(institution=self.institution_a, first_name='A', last_name='User', email='a@example.com', phone='123', national_id='A1', date_of_birth='1990-01-01', gender='M', address='x', city='n', country='Kenya')
        Customer.objects.create(institution=self.institution_b, first_name='B', last_name='User', email='b@example.com', phone='456', national_id='B1', date_of_birth='1990-01-01', gender='M', address='x', city='n', country='Kenya')
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/customers/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], customer_a.id)

    def test_customer_detail_cross_institution_denied(self):
        other_customer = Customer.objects.create(institution=self.institution_b, first_name='B', last_name='User', email='b2@example.com', phone='789', national_id='B2', date_of_birth='1990-01-01', gender='M', address='x', city='n', country='Kenya')
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f'/api/customers/{other_customer.id}/')
        self.assertIn(response.status_code, [403, 404])

    def test_verification_isolation_for_mfi_user(self):
        customer_a = Customer.objects.create(institution=self.institution_a, first_name='A', last_name='User', email='a2@example.com', phone='111', national_id='A2', date_of_birth='1990-01-01', gender='M', address='x', city='n', country='Kenya')
        verification_a = VerificationRequest.objects.create(customer=customer_a, verification_code='V1', status='PENDING', requesting_institution=self.institution_a, requested_by=self.staff_user)
        customer_b = Customer.objects.create(institution=self.institution_b, first_name='B', last_name='User', email='b3@example.com', phone='222', national_id='B3', date_of_birth='1990-01-01', gender='M', address='x', city='n', country='Kenya')
        VerificationRequest.objects.create(customer=customer_b, verification_code='V2', status='PENDING', requesting_institution=self.institution_b, requested_by=self.staff_user)
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/verifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], verification_a.id)

    def test_staff_cannot_approve_verification(self):
        customer_a = Customer.objects.create(institution=self.institution_a, first_name='A', last_name='User', email='a3@example.com', phone='333', national_id='A3', date_of_birth='1990-01-01', gender='M', address='x', city='n', country='Kenya')
        verification = VerificationRequest.objects.create(customer=customer_a, verification_code='V3', status='PENDING', requesting_institution=self.institution_a, requested_by=self.staff_user)
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(f'/api/verifications/{verification.id}/approve/')
        self.assertEqual(response.status_code, 403)

    def test_admin_can_approve_verification(self):
        customer_a = Customer.objects.create(institution=self.institution_a, first_name='A', last_name='User', email='a4@example.com', phone='444', national_id='A4', date_of_birth='1990-01-01', gender='M', address='x', city='n', country='Kenya')
        verification = VerificationRequest.objects.create(customer=customer_a, verification_code='V4', status='PENDING', requesting_institution=self.institution_a, requested_by=self.admin_user)
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/verifications/{verification.id}/approve/')
        self.assertEqual(response.status_code, 200)

    def test_platform_admin_can_access_all_institutions(self):
        self.client.force_authenticate(user=self.platform_admin)
        response = self.client.get('/api/institutions/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)


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
        InstitutionMembership.objects.create(
            user=self.user,
            institution=self.institution,
            role='MFI_STAFF'
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
        self.assertEqual(response.data["count"], 1)

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
        self.assertEqual(response.data["count"], 1)

    def test_institution_filter_by_country(self):
        """Test institution filter by country"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/institutions/?country=Kenya")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)


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
        InstitutionMembership.objects.create(
            user=self.user,
            institution=self.institution,
            role='MFI_STAFF'
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
        self.assertEqual(response.data["count"], 1)

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

    def test_customer_mark_verified_creates_audit_log(self):
        """Test that marking customer as verified creates audit log (Stage 3)"""
        self.client.force_authenticate(user=self.admin_user)
        initial_audit_count = AuditLog.objects.count()
        response = self.client.post(f"/api/customers/{self.customer.id}/mark_verified/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AuditLog.objects.count(), initial_audit_count + 1)
        audit_log = AuditLog.objects.latest('id')
        self.assertEqual(audit_log.action, 'VERIFY')
        self.assertEqual(audit_log.model_name, 'Customer')
        self.assertEqual(audit_log.object_id, str(self.customer.id))

    def test_customer_search_by_email(self):
        """Test customer search by email"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/customers/?search=john")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)


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

    def test_verification_approve_creates_audit_log(self):
        """Test that approving verification creates audit log (Stage 3)"""
        self.client.force_authenticate(user=self.admin_user)
        initial_audit_count = AuditLog.objects.count()
        self.client.post(f"/api/verifications/{self.verification.id}/approve/")
        self.assertEqual(AuditLog.objects.count(), initial_audit_count + 1)
        audit_log = AuditLog.objects.latest('id')
        self.assertEqual(audit_log.action, 'VERIFY')
        self.assertEqual(audit_log.model_name, 'VerificationRequest')

    def test_verification_reject_creates_audit_log(self):
        """Test that rejecting verification creates audit log (Stage 3)"""
        self.client.force_authenticate(user=self.admin_user)
        initial_audit_count = AuditLog.objects.count()
        self.client.post(
            f"/api/verifications/{self.verification.id}/reject/",
            {"reason": "Missing documents"}
        )
        self.assertEqual(AuditLog.objects.count(), initial_audit_count + 1)
        audit_log = AuditLog.objects.latest('id')
        self.assertEqual(audit_log.action, 'REJECT')


class Stage3SecurityTests(APITestCase):
    """Stage 3: Tests for controlled verification workflow security"""

    def setUp(self):
        self.client = APIClient()
        
        # Create two institutions
        self.institution_a = Institution.objects.create(name='Institution A', code='INSTA', country='Kenya')
        self.institution_b = Institution.objects.create(name='Institution B', code='INSTB', country='Kenya')
        
        # Create users for institution A
        self.staff_a = User.objects.create_user(username='staff_a', password='pass123')
        self.admin_a = User.objects.create_user(username='admin_a', password='pass123')
        
        # Create user for institution B
        self.admin_b = User.objects.create_user(username='admin_b', password='pass123')
        
        # Set up memberships
        InstitutionMembership.objects.create(user=self.staff_a, institution=self.institution_a, role='MFI_STAFF')
        InstitutionMembership.objects.create(user=self.admin_a, institution=self.institution_a, role='MFI_ADMIN')
        InstitutionMembership.objects.create(user=self.admin_b, institution=self.institution_b, role='MFI_ADMIN')
        
        # Create customers
        self.customer_a = Customer.objects.create(
            institution=self.institution_a, first_name='A', last_name='Cust',
            email='a@example.com', phone='111', national_id='A001',
            date_of_birth='1990-01-01', gender='M', address='x', city='n', country='Kenya'
        )
        self.customer_b = Customer.objects.create(
            institution=self.institution_b, first_name='B', last_name='Cust',
            email='b@example.com', phone='222', national_id='B001',
            date_of_birth='1990-01-01', gender='M', address='x', city='n', country='Kenya'
        )

    def test_stage3_cross_institution_verification_denied(self):
        """Test: User cannot create verification for another institution's customer (Requirement #1)"""
        self.client.force_authenticate(user=self.admin_a)
        data = {
            'customer': self.customer_b.id,  # Customer from Institution B
            'verification_code': 'VER-CROSS-001',
            'status': 'PENDING'
        }
        response = self.client.post('/api/verifications/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Customer must belong to your institution', str(response.data))

    def test_stage3_verification_requested_by_enforcement(self):
        """Test: requested_by is always set from authenticated user, not client (Requirement #2)"""
        self.client.force_authenticate(user=self.admin_a)
        data = {
            'customer': self.customer_a.id,
            'verification_code': 'VER-REQBY-001',
            'status': 'PENDING',
            'requested_by': 999  # Try to override - should be ignored
        }
        response = self.client.post('/api/verifications/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        verification = VerificationRequest.objects.get(verification_code='VER-REQBY-001')
        self.assertEqual(verification.requested_by, self.admin_a)  # Should be the authenticated user

    def test_stage3_requesting_institution_derived_from_user(self):
        """Test: requesting_institution is derived from user's institution, not client input (Requirement #3)"""
        self.client.force_authenticate(user=self.admin_a)
        data = {
            'customer': self.customer_a.id,
            'verification_code': 'VER-INST-001',
            'status': 'PENDING',
            'requesting_institution': self.institution_b.id  # Try to set to another institution
        }
        response = self.client.post('/api/verifications/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        verification = VerificationRequest.objects.get(verification_code='VER-INST-001')
        self.assertEqual(verification.requesting_institution, self.institution_a)  # Should be user's institution

    def test_stage3_staff_cannot_browse_other_institution_customers(self):
        """Test: Staff user cannot see another institution's customers (Requirement #4)"""
        self.client.force_authenticate(user=self.staff_a)
        response = self.client.get(f'/api/customers/{self.customer_b.id}/')
        self.assertIn(response.status_code, [403, 404])

    def test_stage3_staff_cannot_see_sensitive_verification_fields(self):
        """Test: Staff users cannot see sensitive fields like verification_data, rejection_reason (Requirement #5)"""
        verification = VerificationRequest.objects.create(
            customer=self.customer_a,
            verification_code='VER-STAFF-001',
            status='PENDING',
            requesting_institution=self.institution_a,
            requested_by=self.staff_a,
            verification_data={'test': 'data'},
            rejection_reason='Some reason'
        )
        self.client.force_authenticate(user=self.staff_a)
        response = self.client.get(f'/api/verifications/{verification.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Staff should NOT see these fields
        self.assertNotIn('verification_data', response.data)
        self.assertNotIn('rejection_reason', response.data)
        self.assertNotIn('verified_by', response.data)
        self.assertNotIn('verified_at', response.data)

    def test_stage3_admin_can_see_all_verification_fields(self):
        """Test: Admin users can see all fields including sensitive data (Requirement #5)"""
        verification = VerificationRequest.objects.create(
            customer=self.customer_a,
            verification_code='VER-ADMIN-001',
            status='REJECTED',
            requesting_institution=self.institution_a,
            requested_by=self.admin_a,
            verification_data={'test': 'data'},
            rejection_reason='Incomplete documents'
        )
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.get(f'/api/verifications/{verification.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Admin SHOULD see all fields
        self.assertIn('verification_data', response.data)
        self.assertIn('rejection_reason', response.data)
        self.assertEqual(response.data['rejection_reason'], 'Incomplete documents')

    def test_stage3_only_admin_can_approve_verification(self):
        """Test: Only MFI_ADMIN can approve verification (Requirement #6)"""
        verification = VerificationRequest.objects.create(
            customer=self.customer_a, verification_code='VER-APPROVE-001',
            status='PENDING', requesting_institution=self.institution_a, requested_by=self.staff_a
        )
        
        # Staff cannot approve
        self.client.force_authenticate(user=self.staff_a)
        response = self.client.post(f'/api/verifications/{verification.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin can approve
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.post(f'/api/verifications/{verification.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stage3_only_admin_can_reject_verification(self):
        """Test: Only MFI_ADMIN can reject verification (Requirement #6)"""
        verification = VerificationRequest.objects.create(
            customer=self.customer_a, verification_code='VER-REJECT-001',
            status='PENDING', requesting_institution=self.institution_a, requested_by=self.staff_a
        )
        
        # Staff cannot reject
        self.client.force_authenticate(user=self.staff_a)
        response = self.client.post(f'/api/verifications/{verification.id}/reject/', {'reason': 'test'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin can reject
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.post(f'/api/verifications/{verification.id}/reject/', {'reason': 'Missing docs'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stage3_approve_creates_audit_trail(self):
        """Test: Approve action creates audit log entry (Requirement #7)"""
        verification = VerificationRequest.objects.create(
            customer=self.customer_a, verification_code='VER-AUDIT-APPROVE',
            status='PENDING', requesting_institution=self.institution_a, requested_by=self.admin_a
        )
        initial_count = AuditLog.objects.filter(action='VERIFY').count()
        
        self.client.force_authenticate(user=self.admin_a)
        self.client.post(f'/api/verifications/{verification.id}/approve/')
        
        self.assertEqual(AuditLog.objects.filter(action='VERIFY').count(), initial_count + 1)
        audit = AuditLog.objects.filter(action='VERIFY').latest('id')
        self.assertEqual(audit.model_name, 'VerificationRequest')
        self.assertEqual(audit.institution, self.institution_a)

    def test_stage3_reject_creates_audit_trail(self):
        """Test: Reject action creates audit log entry (Requirement #7)"""
        verification = VerificationRequest.objects.create(
            customer=self.customer_a, verification_code='VER-AUDIT-REJECT',
            status='PENDING', requesting_institution=self.institution_a, requested_by=self.admin_a
        )
        initial_count = AuditLog.objects.filter(action='REJECT').count()
        
        self.client.force_authenticate(user=self.admin_a)
        self.client.post(f'/api/verifications/{verification.id}/reject/', {'reason': 'Docs incomplete'})
        
        self.assertEqual(AuditLog.objects.filter(action='REJECT').count(), initial_count + 1)
        audit = AuditLog.objects.filter(action='REJECT').latest('id')
        self.assertEqual(audit.model_name, 'VerificationRequest')

    def test_stage3_customer_verification_mismatch_detected(self):
        """Test: System detects and rejects verification if customer doesn't match institution (Requirement #8)"""
        # Manually corrupt data (shouldn't happen normally, but defense-in-depth)
        verification = VerificationRequest.objects.create(
            customer=self.customer_a,  # From Institution A
            verification_code='VER-CORRUPT-001',
            status='PENDING',
            requesting_institution=self.institution_b  # Mismatch!
        )
        
        # Try to access - should fail
        self.client.force_authenticate(user=self.admin_b)
        response = self.client.get(f'/api/verifications/{verification.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stage3_cross_institution_admin_cannot_approve_others_verification(self):
        """Test: Admin from Institution B cannot approve verification from Institution A (Requirement #6, #9)"""
        verification = VerificationRequest.objects.create(
            customer=self.customer_a, verification_code='VER-CROSS-ADMIN-001',
            status='PENDING', requesting_institution=self.institution_a, requested_by=self.admin_a
        )
        
        self.client.force_authenticate(user=self.admin_b)
        response = self.client.post(f'/api/verifications/{verification.id}/approve/')
        self.assertIn(response.status_code, [403, 404])


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
        self.assertEqual(response.data["count"], 1)

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
