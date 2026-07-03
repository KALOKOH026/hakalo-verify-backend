from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import datetime, timedelta
from .models import Institution, Customer, VerificationRequest, AuditLog


class InstitutionModelTests(TestCase):
    """Test cases for Institution model"""

    def setUp(self):
        self.institution = Institution.objects.create(
            name="Test Bank",
            code="TSB001",
            country="Kenya",
            email="info@testbank.com",
            phone="+254700000000",
            website="https://testbank.example.com"
        )

    def test_institution_creation(self):
        """Test institution is created with correct attributes"""
        self.assertEqual(self.institution.name, "Test Bank")
        self.assertEqual(self.institution.code, "TSB001")
        self.assertEqual(self.institution.country, "Kenya")
        self.assertTrue(self.institution.is_active)

    def test_institution_str(self):
        """Test institution string representation"""
        self.assertEqual(str(self.institution), "Test Bank (TSB001)")

    def test_institution_unique_name(self):
        """Test institution name must be unique"""
        with self.assertRaises(Exception):
            Institution.objects.create(
                name="Test Bank",  # Duplicate name
                code="TSB002",
                country="Kenya"
            )

    def test_institution_unique_code(self):
        """Test institution code must be unique"""
        with self.assertRaises(Exception):
            Institution.objects.create(
                name="Another Bank",
                code="TSB001",  # Duplicate code
                country="Kenya"
            )

    def test_institution_timestamps(self):
        """Test institution timestamps are set correctly"""
        self.assertIsNotNone(self.institution.created_at)
        self.assertIsNotNone(self.institution.updated_at)
        self.assertEqual(self.institution.created_at, self.institution.updated_at)


class CustomerModelTests(TestCase):
    """Test cases for Customer model"""

    def setUp(self):
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

    def test_customer_creation(self):
        """Test customer is created with correct attributes"""
        self.assertEqual(self.customer.first_name, "John")
        self.assertEqual(self.customer.last_name, "Doe")
        self.assertEqual(self.customer.email, "john@example.com")
        self.assertFalse(self.customer.is_verified)

    def test_customer_str(self):
        """Test customer string representation"""
        self.assertEqual(str(self.customer), "John Doe (12345678)")

    def test_customer_unique_email(self):
        """Test customer email must be unique"""
        with self.assertRaises(Exception):
            Customer.objects.create(
                institution=self.institution,
                first_name="Jane",
                last_name="Doe",
                email="john@example.com",  # Duplicate email
                phone="+254700000001",
                national_id="87654321",
                date_of_birth="1991-02-20",
                gender="F",
                address="456 Oak St",
                city="Mombasa",
                country="Kenya"
            )

    def test_customer_unique_national_id(self):
        """Test customer national_id must be unique per institution"""
        with self.assertRaises(Exception):
            Customer.objects.create(
                institution=self.institution,
                first_name="Jane",
                last_name="Doe",
                email="jane@example.com",
                phone="+254700000001",
                national_id="12345678",  # Duplicate national_id in same institution
                date_of_birth="1991-02-20",
                gender="F",
                address="456 Oak St",
                city="Mombasa",
                country="Kenya"
            )

    def test_customer_gender_choices(self):
        """Test customer gender must be from valid choices"""
        self.assertIn(self.customer.gender, ['M', 'F', 'O'])


class VerificationRequestModelTests(TestCase):
    """Test cases for VerificationRequest model"""

    def setUp(self):
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
            status="PENDING",
            verification_method="EMAIL"
        )

    def test_verification_creation(self):
        """Test verification request is created with correct attributes"""
        self.assertEqual(self.verification.customer, self.customer)
        self.assertEqual(self.verification.status, "PENDING")
        self.assertEqual(self.verification.verification_method, "EMAIL")

    def test_verification_str(self):
        """Test verification string representation"""
        self.assertEqual(str(self.verification), "Verification VER-2026-000001 - PENDING")

    def test_verification_status_choices(self):
        """Test verification status must be from valid choices"""
        valid_statuses = ['PENDING', 'IN_PROGRESS', 'APPROVED', 'REJECTED', 'EXPIRED']
        self.assertIn(self.verification.status, valid_statuses)

    def test_verification_unique_code(self):
        """Test verification code must be unique"""
        with self.assertRaises(Exception):
            VerificationRequest.objects.create(
                customer=self.customer,
                verification_code="VER-2026-000001",  # Duplicate code
                status="PENDING"
            )


class AuditLogModelTests(TestCase):
    """Test cases for AuditLog model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.audit_log = AuditLog.objects.create(
            user=self.user,
            action="CREATE",
            model_name="Customer",
            object_id="1",
            object_repr="John Doe (12345678)",
            description="Created new customer",
            ip_address="192.168.1.1"
        )

    def test_audit_log_creation(self):
        """Test audit log is created with correct attributes"""
        self.assertEqual(self.audit_log.user, self.user)
        self.assertEqual(self.audit_log.action, "CREATE")
        self.assertEqual(self.audit_log.model_name, "Customer")

    def test_audit_log_str(self):
        """Test audit log string representation"""
        self.assertIn("CREATE", str(self.audit_log))
        self.assertIn("Customer", str(self.audit_log))

    def test_audit_log_action_choices(self):
        """Test audit log action must be from valid choices"""
        valid_actions = ['CREATE', 'UPDATE', 'DELETE', 'VIEW', 'VERIFY', 'REJECT', 'EXPORT']
        self.assertIn(self.audit_log.action, valid_actions)

    def test_audit_log_json_fields(self):
        """Test audit log can store JSON data"""
        self.audit_log.old_values = {"email": "old@example.com"}
        self.audit_log.new_values = {"email": "new@example.com"}
        self.audit_log.save()
        self.assertEqual(self.audit_log.old_values["email"], "old@example.com")
        self.assertEqual(self.audit_log.new_values["email"], "new@example.com")
