from django.core.management.base import BaseCommand
from profiles_app.models.profile import Profile
from datetime import date
import uuid
import random


class Command(BaseCommand):
    help = "Populate 100 Profile entries with deterministic UUIDs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing profiles before populating",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing profiles...")
            Profile.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared all profiles"))

        first_names = [
            "James",
            "Mary",
            "John",
            "Patricia",
            "Robert",
            "Jennifer",
            "Michael",
            "Linda",
            "William",
            "Elizabeth",
            "David",
            "Barbara",
            "Richard",
            "Susan",
            "Joseph",
            "Jessica",
            "Thomas",
            "Sarah",
            "Charles",
            "Karen",
        ]
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Brown",
            "Jones",
            "Miller",
            "Davis",
            "Garcia",
            "Rodriguez",
            "Wilson",
            "Martinez",
            "Anderson",
            "Taylor",
            "Thomas",
            "Hernandez",
            "Moore",
            "Martin",
            "Jackson",
            "Martin",
            "Lee",
        ]
        genders = ["M", "F", "O", "P"]
        ethnicities = ["Caucasian", "Asian", "Hispanic", "African American", "Other"]

        created_count = 0
        for i in range(100):
            profile_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"profile-{i}")
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}.{i}@example.com"

            profile_data = {
                "id": profile_id,
                "userID": f"renter_{i}",
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "DOB": date(
                    random.randint(1975, 2005),
                    random.randint(1, 12),
                    random.randint(1, 28),
                ),
                "phone_number": random.randint(1000000, 9999999),
                "gender": random.choice(genders),
                "ethnicity": random.choice(ethnicities),
                "is_email_verified": random.choice([True, True, False]),  # 66% verified
            }

            profile, created = Profile.objects.get_or_create(
                id=profile_id, defaults=profile_data
            )
            if created:
                created_count += 1

            if (i + 1) % 20 == 0:
                self.stdout.write(f"Processed {i+1}/100 profiles...")

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {created_count} profiles.")
        )
