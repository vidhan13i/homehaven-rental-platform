from django.core.management.base import BaseCommand
# ✅ FIXED: Reviews is a separate microservice — it CANNOT import Building model
# from building_service. In microservices, services communicate via APIs, not imports.
# Review.building_ID is a plain UUIDField (not a ForeignKey), so we use UUIDs directly.
from reviews.models.reviews import Review
from datetime import date, timedelta
import random
import uuid


class Command(BaseCommand):
    help = 'Populate Review entries for existing buildings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Total number of reviews to create'
        )
        parser.add_argument(
            '--per-building',
            type=int,
            default=None,
            help='Number of reviews per building (overrides --count)'
        )
        parser.add_argument(
            '--building-id',
            type=str,
            default=None,
            help='Create reviews only for a specific building UUID'
        )
        parser.add_argument(
            '--building-ids',
            type=str,
            default=None,
            help='Comma-separated list of real building UUIDs from building_service'
        )

    def handle(self, *args, **options):
        count = options['count']
        per_building = options['per_building']
        building_id = options['building_id']
        building_ids_raw = options['building_ids']

        # ── Determine which building UUIDs to use ──────────────────────────
        # In microservices, reviews_service doesn't have access to the building DB.
        # You can pass real building UUIDs from building_service via --building-ids,
        # or we generate random UUIDs for seeding/testing purposes.
        if building_id:
            building_uuids = [uuid.UUID(building_id)]
        elif building_ids_raw:
            building_uuids = [uuid.UUID(b.strip()) for b in building_ids_raw.split(',')]
        else:
            # Generate 10 random UUIDs (for dev/testing when building_service data isn't known)
            building_uuids = [uuid.uuid4() for _ in range(10)]
            self.stdout.write(
                self.style.WARNING(
                    'No --building-ids provided. Using random UUIDs for seeding.\n'
                    'Tip: Pass real building IDs with --building-ids=<uuid1>,<uuid2>,...'
                )
            )

        self.stdout.write(f'Seeding reviews for {len(building_uuids)} building(s)...')

        # Review content templates
        titles = [
            'Great place to live!',
            'Good experience overall',
            'Could be better',
            'Excellent maintenance',
            'Average apartment',
            'Loved living here',
            'Not recommended',
            'Perfect for families',
            'Nice amenities',
            'Value for money',
            'Disappointing experience',
            'Highly recommended',
            'Decent place',
            'Outstanding community',
            'Below expectations'
        ]

        pros_list = [
            'Well maintained building, friendly neighbors, good security',
            'Excellent location, close to metro station and shopping centers',
            'Spacious apartments, good natural light, peaceful environment',
            'Responsive management, clean common areas, regular maintenance',
            'Great amenities, professional staff, safe neighborhood',
            'Good connectivity, nearby schools and hospitals, park view',
            'Modern facilities, helpful caretaker, water supply regular',
            'Affordable rent, good community, kids play area available',
            'Clean surroundings, timely garbage collection, elevator always works',
            'Pet-friendly society, rooftop access, gym facilities'
        ]

        cons_list = [
            'Parking space is limited, walls need repainting',
            'Water pressure issues on higher floors, elevator maintenance needed',
            'Noise from main road, need better soundproofing',
            'Garbage collection timing inconsistent, lift breaks down often',
            'High maintenance charges, poor mobile network coverage',
            'No visitor parking, intercom system not working',
            'Slow maintenance response, outdated gym equipment',
            'Power backup insufficient, drainage issues during monsoon',
            'Limited storage space, no balcony space',
            'Rent increased too much, deposit refund delayed'
        ]

        advice_list = [
            'Great for long-term stay, recommend checking water pressure before moving in',
            'Read the lease agreement carefully, clarify deposit terms upfront',
            'Visit during peak hours to check parking availability',
            'Meet neighbors before deciding, check mobile network strength',
            'Inspect the apartment thoroughly, take photos before moving in',
            'Negotiate rent and maintenance charges, get everything in writing',
            'Check water supply timings, ask about power backup capacity',
            'Verify RERA certification, speak with current residents',
            'Document all existing damages, keep communication with landlord in email',
            'Consider the floor number carefully, higher floors may have water issues'
        ]

        created_count = 0

        if per_building:
            for b_uuid in building_uuids:
                for _ in range(per_building):
                    self._create_review(b_uuid, titles, pros_list, cons_list, advice_list)
                    created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created {per_building} reviews for building: {b_uuid}')
                )
        else:
            for i in range(count):
                b_uuid = random.choice(building_uuids)
                self._create_review(b_uuid, titles, pros_list, cons_list, advice_list)
                created_count += 1
                if (i + 1) % 10 == 0:
                    self.stdout.write(self.style.SUCCESS(f'Created {i + 1}/{count} reviews...'))

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully created {created_count} reviews across {len(building_uuids)} building(s)'
            )
        )

        # Show distribution
        self.stdout.write('\n📊 Review Distribution:')
        for b_uuid in building_uuids:
            review_count = Review.objects.filter(building_ID=b_uuid).count()
            self.stdout.write(f'  - Building {b_uuid}: {review_count} reviews')

    def _create_review(self, building_uuid, titles, pros_list, cons_list, advice_list):
        """
        Create a single review for a given building UUID.
        Reviews service is a microservice — it doesn't have access to Building model.
        We store only the building_ID (UUID) and generate realistic fake context.
        """
        # Generate random dates
        move_in = date.today() - timedelta(days=random.randint(365, 1825))  # 1-5 years ago
        move_out = move_in + timedelta(days=random.randint(180, 1095))  # 6 months to 3 years later

        # Generate correlated ratings (realistic - if one is high, others tend to be high)
        base_rating = random.uniform(2.0, 5.0)
        variance = 0.5

        cleanliness = max(0.0, min(5.0, base_rating + random.uniform(-variance, variance)))
        garbage = max(0.0, min(5.0, base_rating + random.uniform(-variance, variance)))
        neighbours = max(0.0, min(5.0, base_rating + random.uniform(-variance, variance)))
        water = max(0.0, min(5.0, base_rating + random.uniform(-variance, variance)))
        maintenance = max(0.0, min(5.0, base_rating + random.uniform(-variance, variance)))

        # Round to 1 decimal place
        cleanliness = round(cleanliness, 1)
        garbage = round(garbage, 1)
        neighbours = round(neighbours, 1)
        water = round(water, 1)
        maintenance = round(maintenance, 1)

        # Generate rent — randomised since we don't have access to building city data
        # (reviews_service is isolated — no access to building_service database)
        starting_rent = random.randint(8000, 50000)

        rent_increase_percent = random.uniform(0.05, 0.15)  # 5-15% increase
        ending_rent = starting_rent * (1 + rent_increase_percent)

        total_deposit = starting_rent * random.randint(2, 6)  # 2-6 months deposit
        is_received = random.choice([True, True, True, False])  # 75% got deposit back

        if is_received:
            # Small deduction in some cases
            deposit_withheld = random.choice([0, 0, 0, random.randint(500, 5000)])
        else:
            deposit_withheld = None

        # Generate unit number (random since we don't know building's actual floors)
        max_floor = random.randint(5, 30)
        floor = random.randint(1, max_floor)
        unit_letter = chr(65 + random.randint(0, 7))  # A-H
        unit_no = f"{floor}{unit_letter}-{random.randint(101, 199)}"

        # Generate a plausible address (no actual building data available in this service)
        cities = ['Mumbai', 'Delhi', 'Bangalore', 'Pune', 'Hyderabad', 'Chennai', 'Kolkata']
        city = random.choice(cities)
        full_address = f"Unit {unit_no}, {random.randint(1, 999)} MG Road, {city}"

        # Determine status (mostly submitted for aggregation to work)
        status = random.choices(
            [Review.Status.SUBMITTED, Review.Status.DRAFT, Review.Status.INPROGRESS],
            weights=[85, 10, 5]  # 85% submitted, 10% draft, 5% in progress
        )[0]

        review_data = {
            'profile_ID': uuid.uuid4(),      # Random user UUID
            'building_ID': building_uuid,     # ✅ The UUID passed in (from building_service)
            'full_address': full_address,
            'cleanliness_rating': cleanliness,
            'garbage_management_rating': garbage,
            'neighbours_rating': neighbours,
            'water_supply_rating': water,
            'building_maintenance_rating': maintenance,
            'Title': random.choice(titles),
            'Pros': random.choice(pros_list),
            'Cons': random.choice(cons_list),
            'Advice': random.choice(advice_list),
            'move_in_date': move_in,
            'move_out_date': move_out,
            'is_received_deposit': is_received,
            'total_deposit': total_deposit,
            'deposit_withheld': deposit_withheld if is_received else None,
            'is_pet_friendly': random.choice([True, False]),
            'starting_rent': starting_rent,
            'ending_rent': round(ending_rent, 2),
            'unit_no': unit_no,
            'status': status,
        }

        Review.objects.create(**review_data)