from django.core.management.base import BaseCommand
from ..building.models.building import Building
from reviews.reviews.models.reviews import Review
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
            help='Total number of reviews to create across all buildings'
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
            help='Create reviews only for specific building ID'
        )

    def handle(self, *args, **options):
        count = options['count']
        per_building = options['per_building']
        building_id = options['building_id']

        # Fetch buildings from database
        if building_id:
            # Create reviews for specific building
            buildings = Building.objects.filter(id=building_id)
            if not buildings.exists():
                self.stdout.write(
                    self.style.ERROR(f'Building with ID {building_id} not found!')
                )
                return
        else:
            # Get all buildings
            buildings = Building.objects.all()

        if not buildings.exists():
            self.stdout.write(
                self.style.ERROR('No buildings found! Please create buildings first.')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Found {buildings.count()} buildings in database')
        )

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
            # Create specific number of reviews per building
            for building in buildings:
                for _ in range(per_building):
                    self._create_review(
                        building, titles, pros_list, cons_list, advice_list
                    )
                    created_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created {per_building} reviews for: {building.name} (ID: {building.id})'
                    )
                )
        else:
            # Distribute reviews across buildings
            buildings_list = list(buildings)
            for i in range(count):
                # Randomly select a building but with weighted distribution
                # (some buildings get more reviews than others - more realistic)
                building = random.choice(buildings_list)

                self._create_review(
                    building, titles, pros_list, cons_list, advice_list
                )
                created_count += 1

                if (i + 1) % 10 == 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created {i + 1}/{count} reviews...')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully created {created_count} reviews across {buildings.count()} buildings'
            )
        )

        # Show distribution
        self.stdout.write('\n📊 Review Distribution:')
        for building in buildings:
            review_count = Review.objects.filter(building_ID=building.id).count()
            self.stdout.write(f'  - {building.name}: {review_count} reviews')

    def _create_review(self, building, titles, pros_list, cons_list, advice_list):
        """
        Create a single review for the given building
        Uses actual building data from the database
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

        # Generate financial data based on city/location
        # More expensive in metros
        if building.city in ['Mumbai', 'Delhi', 'Bangalore']:
            starting_rent = random.randint(15000, 50000)
        elif building.city in ['Pune', 'Hyderabad', 'Chennai']:
            starting_rent = random.randint(10000, 35000)
        else:
            starting_rent = random.randint(8000, 25000)

        rent_increase_percent = random.uniform(0.05, 0.15)  # 5-15% increase
        ending_rent = starting_rent * (1 + rent_increase_percent)

        total_deposit = starting_rent * random.randint(2, 6)  # 2-6 months deposit
        is_received = random.choice([True, True, True, False])  # 75% got deposit back

        if is_received:
            # Small deduction in some cases
            deposit_withheld = random.choice([0, 0, 0, random.randint(500, 5000)])
        else:
            deposit_withheld = None

        # Generate realistic unit number based on building data
        max_floor = building.no_of_floors if building.no_of_floors else 10
        floor = random.randint(1, max_floor)
        unit_letter = chr(65 + random.randint(0, 7))  # A-H
        unit_no = f"{floor}{unit_letter}-{random.randint(101, 199)}"

        # Create full address with unit
        full_address = f"Unit {unit_no}, {building.name}, {building.address}, {building.city}, {building.state} - {building.Pin_code}"

        # Determine status (mostly submitted for aggregation to work)
        status = random.choices(
            [Review.Status.SUBMITTED, Review.Status.DRAFT, Review.Status.INPROGRESS],
            weights=[85, 10, 5]  # 85% submitted, 10% draft, 5% in progress
        )[0]

        review_data = {
            'profile_ID': uuid.uuid4(),  # Random user ID
            'building_ID': building.id,  # ✅ ACTUAL building ID from database
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