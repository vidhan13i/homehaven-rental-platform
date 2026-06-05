"""
Management command to populate the database with sample listing data

Usage:
    python manage.py populate_listings
    python manage.py populate_listings --count 100
    python manage.py populate_listings --clear
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from listings.models.listing import Listing
from listings.models.unit import Unit


class Command(BaseCommand):
    help = 'Populates the database with sample listing data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of listings-service to create (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing listings-service before populating'
        )

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']

        if clear:
            self.stdout.write('Clearing existing listings-service...')
            Listing.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared all listings-service'))

        # First, ensure we have some units
        self.create_sample_units()

        # Create listings-service
        self.stdout.write(f'Creating {count} sample listings-service...')

        units = list(Unit.objects.all())
        if not units:
            self.stdout.write(self.style.ERROR('No units available. Please create units first.'))
            return

        listings_created = 0
        for i in range(count):
            listing = self.create_sample_listing(units)
            if listing:
                listings_created += 1
                if listings_created % 10 == 0:
                    self.stdout.write(f'Created {listings_created} listings-service...')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {listings_created} listings-service')
        )

    def create_sample_units(self):
        """Create sample units if they don't exist"""
        if Unit.objects.count() > 0:
            return

        self.stdout.write('Creating sample units...')

        # First, ensure we have at least one agent
        from listings.models.agent import Agent

        agent = Agent.objects.first()
        if not agent:
            self.stdout.write('Creating sample agent...')
            agent = Agent.objects.create(
                first_name='John',
                last_name='Smith',
                email='john.smith@realestate.com',
                phone_number=555123,
                agent_organization='Prime Realty Group',
                agent_experience=5,
                is_agent_verified=True
            )
            self.stdout.write(self.style.SUCCESS('Created sample agent'))

        unit_data = [
            {'full_address': '123 Main St, New York, NY 10001', 'unit_no': '4B', 'bedrooms': 2, 'bathrooms': 1},
            {'full_address': '456 Park Ave, Brooklyn, NY 11201', 'unit_no': '12', 'bedrooms': 3, 'bathrooms': 2},
            {'full_address': '789 Broadway, Queens, NY 11372', 'unit_no': '3A', 'bedrooms': 1, 'bathrooms': 1},
            {'full_address': '321 Elm St, Bronx, NY 10451', 'unit_no': '5C', 'bedrooms': 2, 'bathrooms': 2},
            {'full_address': '654 Oak Ave, Manhattan, NY 10002', 'unit_no': '2D', 'bedrooms': 3, 'bathrooms': 2},
            {'full_address': '987 Pine Rd, Staten Island, NY 10301', 'unit_no': '8F', 'bedrooms': 2, 'bathrooms': 1},
            {'full_address': '147 Maple Dr, Brooklyn, NY 11215', 'unit_no': '6E', 'bedrooms': 1, 'bathrooms': 1},
            {'full_address': '258 Cedar Ln, Queens, NY 11375', 'unit_no': '9G', 'bedrooms': 4, 'bathrooms': 3},
            {'full_address': '369 Birch St, Bronx, NY 10461', 'unit_no': '1H', 'bedrooms': 2, 'bathrooms': 1},
            {'full_address': '741 Walnut Ave, Manhattan, NY 10003', 'unit_no': '7I', 'bedrooms': 3, 'bathrooms': 2},
        ]

        created_count = 0
        for data in unit_data:
            try:
                # Create unique slug
                slug = f"{data['full_address'].split(',')[0].lower().replace(' ', '-')}-{data['unit_no'].lower()}"

                Unit.objects.create(
                    full_address=data['full_address'],
                    unit_no=data['unit_no'],
                    unit_slug=slug,
                    no_bedrooms=data['bedrooms'],
                    no_bathrooms=data['bathrooms'],
                    description=f"Beautiful {data['bedrooms']} bedroom, {data['bathrooms']} bathroom apartment in a prime location.",
                    is_furnished=random.choice([True, False]),
                    is_semi_furnished=False,  # Can't be both furnished and semi-furnished
                    agent_ID=agent
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating unit: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'Created {created_count} sample units'))

    def create_sample_listing(self, units):
        """Create a single sample listing with realistic data"""
        try:
            # Random rent between $800 and $5000
            rent = random.randint(800, 5000)

            # Deposit is typically 1-2 months rent
            deposit_multiplier = random.choice([1, 1.5, 2])
            deposit_amount = int(rent * deposit_multiplier)

            # Lease term in months (6, 12, or 24 months typical)
            lease_term = random.choice([6, 12, 24])

            # Available date between now and 90 days from now
            days_until_available = random.randint(0, 90)
            available_date = timezone.now().date() + timedelta(days=days_until_available)

            # Publish date between 30 days ago and now
            days_since_published = random.randint(0, 30)
            publish_date = timezone.now().date() - timedelta(days=days_since_published)

            # Closing date 30-90 days after available date
            days_until_closing = random.randint(30, 90)
            closing_date = available_date + timedelta(days=days_until_closing)

            # 70% of listings-service are verified
            is_listing_verified = random.random() < 0.7

            # Random unit
            unit = random.choice(units)

            listing = Listing.objects.create(
                rent=rent,
                deposit_amount=deposit_amount,
                available_date=available_date,
                publish_date=publish_date,
                closing_date=closing_date,
                lease_term=lease_term,
                is_listing_verified=is_listing_verified,
                unit_ID=unit
            )

            return listing

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating listing: {str(e)}')
            )
            return None