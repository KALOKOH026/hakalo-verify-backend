from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Institution, InstitutionMembership, Customer, VerificationRequest


class Command(BaseCommand):
    help = 'Create synthetic development data for local testing only.'

    def handle(self, *args, **options):
        if not self._is_dev_environment():
            self.stderr.write('This command is only allowed in development environments.')
            return

        institution_a, _ = Institution.objects.get_or_create(
            code='MFIA',
            defaults={'name': 'Demo MFI A', 'country': 'Kenya', 'email': 'demo-a@example.com'}
        )
        institution_b, _ = Institution.objects.get_or_create(
            code='MFIB',
            defaults={'name': 'Demo MFI B', 'country': 'Kenya', 'email': 'demo-b@example.com'}
        )

        admin_user, _ = User.objects.get_or_create(username='demo-admin', defaults={'email': 'demo-admin@example.com'})
        if not admin_user.has_usable_password():
            admin_user.set_password('demo1234')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        staff_user, _ = User.objects.get_or_create(username='demo-staff', defaults={'email': 'demo-staff@example.com'})
        if not staff_user.has_usable_password():
            staff_user.set_password('demo1234')
        staff_user.is_staff = True
        staff_user.save()

        InstitutionMembership.objects.get_or_create(user=admin_user, institution=institution_a, defaults={'role': 'MFI_ADMIN'})
        InstitutionMembership.objects.get_or_create(user=staff_user, institution=institution_a, defaults={'role': 'MFI_STAFF'})

        for index, institution in enumerate([institution_a, institution_b], start=1):
            Customer.objects.get_or_create(
                national_id=f'DEMO{index}',
                defaults={
                    'institution': institution,
                    'first_name': f'Demo{index}',
                    'last_name': 'Customer',
                    'email': f'demo{index}@example.com',
                    'phone': f'+2547000000{index}',
                    'date_of_birth': '1990-01-01',
                    'gender': 'M',
                    'address': '123 Demo Street',
                    'city': 'Nairobi',
                    'country': 'Kenya',
                },
            )

        customer = Customer.objects.filter(institution=institution_a).first()
        if customer:
            VerificationRequest.objects.get_or_create(
                verification_code='DEMO-VER-001',
                defaults={
                    'customer': customer,
                    'status': 'PENDING',
                    'requested_by': staff_user,
                    'requesting_institution': institution_a,
                },
            )

        self.stdout.write(self.style.SUCCESS('Synthetic development data created.'))

    def _is_dev_environment(self):
        return True
