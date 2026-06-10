from django.core.management.base import BaseCommand
from reviews.models.reviews import Review
from datetime import date, timedelta
import uuid
import random

class Command(BaseCommand):
    help = 'Populate 10 reviews for each of the 100 buildings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing reviews before populating'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing reviews...')
            Review.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared all reviews'))

        titles = [
            'Great place to live!', 'Good experience overall', 'Could be better',
            'Excellent maintenance', 'Average apartment', 'Loved living here',
            'Not recommended', 'Perfect for families', 'Nice amenities',
            'Value for money', 'Disappointing experience', 'Highly recommended',
            'Decent place', 'Outstanding community', 'Below expectations'
        ]

        pros_list = [
            'Well maintained building, friendly neighbors, good security.',
            'Excellent location, close to metro station and shopping centers.',
            'Spacious apartments, good natural light, peaceful environment.',
            'Responsive management, clean common areas, regular maintenance.',
            'Great amenities, professional staff, safe neighborhood.',
            'Good connectivity, nearby schools and hospitals, park view.',
            'Modern facilities, helpful caretaker, water supply regular.',
            'Affordable rent, good community, kids play area available.',
            'Clean surroundings, timely garbage collection, elevator works fine.',
            'Pet-friendly society, rooftop access, gym facilities.'
        ]

        cons_list = [
            'Parking space is limited, walls need repainting.',
            'Water pressure issues on higher floors, elevator maintenance needed.',
            'Noise from main road, need better soundproofing.',
            'Garbage collection timing inconsistent, lift breaks down occasionally.',
            'High maintenance charges, poor mobile network coverage in basement.',
            'No visitor parking, intercom system sometimes malfunctions.',
            'Slow maintenance response for non-emergencies, outdated gym equipment.',
            'Power backup takes a minute to kick in, drainage slow in monsoon.',
            'Limited storage space in bedrooms, no balcony space.',
            'Rent increased slightly, security deposit refund delayed by a week.'
        ]

        advice_list = [
            'Great for long-term stay. Recommend checking water pressure before moving in.',
            'Read the lease agreement carefully, clarify deposit terms upfront.',
            'Visit during peak hours to check parking availability.',
            'Meet neighbors before deciding, check mobile network strength inside.',
            'Inspect the apartment thoroughly, take photos before moving in.',
            'Negotiate rent and maintenance charges, get everything in writing.',
            'Check water supply timings, ask about power backup capacity.',
            'Verify details, speak with current residents in the lobby.',
            'Document all existing damages, keep communication with landlord in email.',
            'Consider the floor number carefully, higher floors may have lower water pressure.'
        ]

        created_count = 0
        self.stdout.write("Generating 10 reviews per building for 100 buildings (1000 reviews)...")

        for i in range(100):
            building_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"building-{i}")
            
            for r in range(10):
                # Ensure each review is deterministic
                rng = random.Random(f"review-{i}-{r}")
                
                # Link review to one of the 100 profiles deterministically
                profile_idx = (i * 10 + r) % 100
                profile_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"profile-{profile_idx}")
                
                # Varied ratings based on review index and building index
                base_rating = rng.uniform(2.5, 5.0)
                cleanliness = round(max(1.0, min(5.0, base_rating + rng.uniform(-0.5, 0.5))), 1)
                garbage = round(max(1.0, min(5.0, base_rating + rng.uniform(-0.5, 0.5))), 1)
                neighbours = round(max(1.0, min(5.0, base_rating + rng.uniform(-0.5, 0.5))), 1)
                water = round(max(1.0, min(5.0, base_rating + rng.uniform(-0.5, 0.5))), 1)
                maintenance = round(max(1.0, min(5.0, base_rating + rng.uniform(-0.5, 0.5))), 1)

                move_in = date.today() - timedelta(days=rng.randint(365, 1800))
                move_out = move_in + timedelta(days=rng.randint(180, 1000))
                
                starting_rent = rng.randint(1500, 5000)
                ending_rent = round(starting_rent * rng.uniform(1.0, 1.15), 2)
                total_deposit = starting_rent * rng.randint(1, 2)
                
                unit_no = f"{1 + (r % 5)}F-{100 + (i % 10)}"

                review_data = {
                    'profile_ID': profile_id,
                    'building_ID': building_id,
                    'full_address': f"Unit {unit_no}, {100 + i} Grand Ave",
                    'cleanliness_rating': cleanliness,
                    'garbage_management_rating': garbage,
                    'neighbours_rating': neighbours,
                    'water_supply_rating': water,
                    'building_maintenance_rating': maintenance,
                    'Title': rng.choice(titles),
                    'Pros': rng.choice(pros_list),
                    'Cons': rng.choice(cons_list),
                    'Advice': rng.choice(advice_list),
                    'move_in_date': move_in,
                    'move_out_date': move_out,
                    'is_received_deposit': True,
                    'total_deposit': total_deposit,
                    'deposit_withheld': rng.choice([0.0, 0.0, 100.0, 200.0]),
                    'is_pet_friendly': rng.choice([True, False]),
                    'starting_rent': starting_rent,
                    'ending_rent': ending_rent,
                    'unit_no': unit_no,
                    'status': 'submitted',
                }

                Review.objects.create(**review_data)
                created_count += 1

            if (i + 1) % 20 == 0:
                self.stdout.write(f"Processed reviews for {i+1}/100 buildings...")

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} reviews."))