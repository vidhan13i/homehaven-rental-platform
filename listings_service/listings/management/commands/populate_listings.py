from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
import uuid

from listings.models.listing import Listing
from listings.models.unit import Unit
from listings.models.agent import Agent
from listings.models.image import Images

class Command(BaseCommand):
    help = 'Populates the listings database with 1000 units and listings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing listings and units before populating'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing listings and units...')
            Listing.objects.all().delete()
            Unit.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared all listings and units'))

        # Ensure we have a few agents
        agents = []
        agent_names = [
            ('John', 'Smith', 'Prime Realty'),
            ('Sarah', 'Connor', 'Apex Management'),
            ('David', 'Miller', 'Metro Housing'),
            ('Emma', 'Wilson', 'Summit Properties')
        ]
        
        for fname, lname, org in agent_names:
            agent_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"agent-{fname}-{lname}")
            agent, created = Agent.objects.get_or_create(
                id=agent_id,
                defaults={
                    'first_name': fname,
                    'last_name': lname,
                    'email': f"{fname.lower()}.{lname.lower()}@example.com",
                    'phone_number': random.randint(1000000, 9999999),
                    'agent_organization': org,
                    'agent_experience': random.randint(2, 15),
                    'is_agent_verified': True
                }
            )
            agents.append(agent)

        cities_states = [
            ('New York', 'NY', 10001, 40.7128, -74.0060),
            ('Brooklyn', 'NY', 11201, 40.6782, -73.9442),
            ('Queens', 'NY', 11372, 40.7282, -73.7949),
            ('Jersey City', 'NJ', 7302, 40.7282, -74.0776),
            ('Hoboken', 'NJ', 7030, 40.7453, -74.0278),
        ]

        created_units = 0
        created_listings = 0

        self.stdout.write("Generating 1000 units and listings...")

        for k in range(1000):
            # Deterministically identify the building index this unit belongs to
            b_idx = k % 100
            
            # Recreate building random generator to get matching address details
            rng_building = random.Random(b_idx)
            city, state, pin, _, _ = rng_building.choice(cities_states)
            building_address = f"{100 + b_idx} Grand Ave, {city}"
            
            # General RNG for unit specific fields
            rng_unit = random.Random(k)
            
            unit_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"unit-{k}")
            floor = (k // 100) + 1
            room = 100 + (k % 10)
            unit_no = f"{floor}F-{room}"
            slug = f"unit-{k}-{unit_no.lower()}"
            
            bedrooms = rng_unit.choice([1, 2, 3, 4])
            bathrooms = rng_unit.choice([1, 2])
            
            # Setup furnished condition (is_furnished and is_semi_furnished cannot both be true)
            is_furnished = rng_unit.choice([True, False])
            is_semi_furnished = False if is_furnished else rng_unit.choice([True, False])

            unit, unit_created = Unit.objects.get_or_create(
                id=unit_id,
                defaults={
                    'full_address': f"{building_address}, {state} {pin + (b_idx % 10)}",
                    'unit_no': unit_no,
                    'unit_slug': slug,
                    'no_bedrooms': bedrooms,
                    'no_bathrooms': bathrooms,
                    'description': f"Beautiful {bedrooms} bedroom, {bathrooms} bathroom unit in a premium building.",
                    'is_furnished': is_furnished,
                    'is_semi_furnished': is_semi_furnished,
                    'agent_ID': rng_unit.choice(agents)
                }
            )

            if unit_created:
                created_units += 1
                img_url = f"https://images.unsplash.com/photo-{rng_unit.choice(['1522708323590-d24dbb6b0267', '1502672260266-1c1ef2d93688', '1493809842364-78817add7ffb'])}?w=800"
                Images.objects.create(
                    image_url=img_url,
                    unit_ID=unit
                )

            # Create Listing
            listing_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"listing-{k}")
            rent = rng_unit.randint(1500, 6000)
            deposit_amount = int(rent * rng_unit.choice([1, 1.5, 2]))
            
            listing, listing_created = Listing.objects.get_or_create(
                id=listing_id,
                defaults={
                    'rent': rent,
                    'deposit_amount': deposit_amount,
                    'available_date': timezone.now().date() + timedelta(days=rng_unit.randint(5, 60)),
                    'publish_date': timezone.now().date() - timedelta(days=rng_unit.randint(1, 15)),
                    'closing_date': timezone.now().date() + timedelta(days=rng_unit.randint(60, 120)),
                    'lease_term': rng_unit.choice([6, 12, 24]),
                    'is_listing_verified': rng_unit.choice([True, True, False]), # 66% verified
                    'unit_ID': unit
                }
            )

            if listing_created:
                created_listings += 1

            if (k + 1) % 200 == 0:
                self.stdout.write(f"Processed {k+1}/1000 units and listings...")

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_units} units and {created_listings} listings."))