from django.core.management.base import BaseCommand
from django.utils.text import slugify
from building.models.building import Building
from building.models.images import Images
from datetime import date
import uuid
import random


class Command(BaseCommand):
    help = "Populate 100 Building entries with deterministic parameters"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing buildings before populating",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing buildings...")
            Building.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared all buildings"))

        cities_states = [
            ("New York", "NY", 10001, 40.7128, -74.0060),
            ("Brooklyn", "NY", 11201, 40.6782, -73.9442),
            ("Queens", "NY", 11372, 40.7282, -73.7949),
            ("Jersey City", "NJ", 7302, 40.7282, -74.0776),
            ("Hoboken", "NJ", 7030, 40.7453, -74.0278),
        ]

        building_prefixes = [
            "Skyline",
            "Green Valley",
            "Ocean View",
            "Sunrise",
            "Royal",
            "Metro",
            "Paradise",
            "Golden",
            "Silver Oak",
            "Crystal",
            "Diamond",
            "Emerald",
            "Parkway",
            "Summit",
            "Ridgeview",
        ]

        created_count = 0
        for i in range(100):
            # Seed generator specifically for this index to keep it deterministic
            rng = random.Random(i)

            building_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"building-{i}")
            city, state, pin, base_lat, base_lng = rng.choice(cities_states)

            prefix = rng.choice(building_prefixes)
            name = f"{prefix} Tower {i+1}"
            slug = slugify(f"{name}-{i}")

            building_data = {
                "id": building_id,
                "name": name,
                "address": f"{100 + i} Grand Ave, {city}",
                "slug": slug,
                "city": city,
                "state": state,
                "Pin_code": pin + (i % 10),
                "latitude": base_lat + rng.uniform(-0.02, 0.02),
                "longitude": base_lng + rng.uniform(-0.02, 0.02),
                "built_year": date(rng.randint(1995, 2024), 1, 1),
                "no_of_units": rng.randint(20, 200),
                "no_of_floors": rng.randint(5, 40),
                "is_gym": rng.choice([True, False]),
                "is_swimming": rng.choice([True, False]),
                "is_garden": rng.choice([True, False]),
                "is_elevator": True,
                "is_RERA_verified": rng.choice([True, False]),
                "review_count": 10,
                "avg_rating": round(rng.uniform(3.0, 5.0), 1),
            }

            building, created = Building.objects.get_or_create(
                id=building_id, defaults=building_data
            )

            if created:
                created_count += 1
                img_url = f"https://images.unsplash.com/photo-{rng.choice(['1545324418-cc1a3fa10c00', '1564013799919-ab600027ffc6', '1580587771525-78b9dba3b914'])}?w=800"
                Images.objects.create(image=img_url, build_ID=building)

            if (i + 1) % 20 == 0:
                self.stdout.write(f"Processed {i+1}/100 buildings...")

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {created_count} buildings.")
        )
