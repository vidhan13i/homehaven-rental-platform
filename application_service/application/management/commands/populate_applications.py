from django.core.management.base import BaseCommand
from application.models.applicant import Applicant
from application.models.application import Application
from application.models.document import Document
from datetime import date, timedelta
import uuid
import random

class Command(BaseCommand):
    help = 'Populate Coordinated Applicant and Application entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing applications before populating'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing applications, applicants, and documents...')
            Document.objects.all().delete()
            Application.objects.all().delete()
            Applicant.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared all application tables'))

        employers = ['Google', 'Meta', 'Amazon', 'Apple', 'Netflix', 'Microsoft', 'Stripe', 'Uber', 'Airbnb', 'Dunder Mifflin']
        job_titles = ['Software Engineer', 'Product Manager', 'Data Scientist', 'Designer', 'HR Specialist', 'Sales Exec', 'Marketing Manager']

        created_applicants = 0
        created_applications = 0

        self.stdout.write("Generating 50 applicant profiles and applications...")

        for j in range(50):
            rng = random.Random(f"application-{j}")
            profile_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"profile-{j}")
            
            employer = rng.choice(employers)
            job = rng.choice(job_titles)
            
            applicant, created = Applicant.objects.get_or_create(
                profile_ID=profile_id,
                defaults={
                    'employer': employer,
                    'job_title': job,
                    'job_start_date': date(rng.randint(2018, 2024), 1, 1),
                    'credit_score': rng.randint(650, 820),
                    'income': rng.randint(60000, 200000),
                    'savings': rng.randint(5000, 50000),
                    'expected_movein_date': date(2026, 7, 1) + timedelta(days=rng.randint(0, 30)),
                    'reason': 'Relocating to a new area for work.',
                    'has_rented_before': True,
                    'rental_history': {
                        'address': f"{rng.randint(10, 99)} Pine St, New York, NY",
                        'move_in': '2022-01-01',
                        'move_out': '2026-06-30'
                    },
                    'marital_status': rng.choice([True, False]),
                    'children': rng.choice([True, False]),
                    'emergency_info': {
                        'name': f"Emergency Contact {j}",
                        'email': f"emergency{j}@example.com",
                        'phone': f"555-010-00{j:02d}",
                        'relationship': rng.choice(['Parent', 'Sibling', 'Spouse', 'Friend'])
                    }
                }
            )

            if created:
                created_applicants += 1
                
                # Create corresponding document labels
                Document.objects.create(
                    applicant_ID=applicant,
                    label={
                        'employment_letter': f'employment_letter_user_{j}.pdf',
                        'aadhar_card': f'aadhar_user_{j}.pdf',
                        'pan_card': f'pan_user_{j}.pdf',
                        'ITR': f'itr_user_{j}.pdf',
                        'bank_statement': f'bank_statement_user_{j}.pdf'
                    }
                )

            # Map index j to unit index j * 10
            unit_idx = j * 10
            unit_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"unit-{unit_idx}")
            building_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"building-{unit_idx % 100}")

            application_status = rng.choice([
                Application.ApplicationStatus.DRAFT,
                Application.ApplicationStatus.SUBMITTED,
                Application.ApplicationStatus.APPROVED,
                Application.ApplicationStatus.REJECTED
            ])

            application, app_created = Application.objects.get_or_create(
                applicant_ID=applicant,
                unit_ID=unit_id,
                building_ID=building_id,
                defaults={
                    'lease_term': f"{rng.choice([6, 12, 24])} months",
                    'resident_info': {
                        'name': f"Applicant Renter {j}",
                        'gender': rng.choice(['male', 'female', 'other']),
                        'dob': f"199{rng.randint(0,9)}-05-15"
                    },
                    'application_status': application_status
                }
            )

            if app_created:
                created_applications += 1

            if (j + 1) % 10 == 0:
                self.stdout.write(f"Processed {j+1}/50 applications...")

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_applicants} applicants and {created_applications} applications."))
