# pyrefly: ignore [missing-import]
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from building.models.building import Building
from datetime import date
import random


class Command(BaseCommand):
    help = 'Populate Building entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of buildings to create'
        )

        parser.add_argument(
            '--database',
            type=str,
            default= 'building',
        )

    def handle(self, *args, **options):
        count = options['count']

        cities_states = [
            ('Mumbai', 'Maharashtra'),
            ('Delhi', 'Delhi'),
            ('Bangalore', 'Karnataka'),
            ('Hyderabad', 'Telangana'),
            ('Chennai', 'Tamil Nadu'),
            ('Kolkata', 'West Bengal'),
            ('Pune', 'Maharashtra'),
            ('Ahmedabad', 'Gujarat'),
        ]

        building_names = [
            'Sky Tower', 'Green Valley Apartments', 'Ocean View Residency',
            'Sunrise Heights', 'Royal Palace', 'Metro Homes',
            'Paradise Residency', 'Golden Heights', 'Silver Oak Apartments',
            'Crystal Palace', 'Diamond Heights', 'Emerald Towers'
        ]

        created_count = 0

        for i in range(count):
            city, state = random.choice(cities_states)
            name = f"{random.choice(building_names)} {i + 1}"

            building_data = {
                'name': name,
                'address': f'{random.randint(1, 999)} MG Road, {city}',
                'slug': slugify(name),
                'city': city,
                'state': state,
                'Pin_code': random.randint(100000, 999999),
                'latitude': round(random.uniform(8.0, 35.0), 6),
                'longitude': round(random.uniform(68.0, 97.0), 6),
                'built_year': date(random.randint(2000, 2024), 1, 1),
                'no_of_units': random.randint(20, 200),
                'no_of_floors': random.randint(5, 30),
                'is_gym': random.choice([True, False]),
                'is_swimming': random.choice([True, False]),
                'is_garden': random.choice([True, False]),
                'is_elevator': random.choice([True, True, False]),  # More likely to have elevator
                'is_RERA_verified': random.choice([True, False]),
                'review_count': random.randint(0, 500),
                'avg_rating': round(random.uniform(2.5, 5.0), 1),
            }

            building, created = Building.objects.get_or_create(
                slug=building_data['slug'],
                defaults=building_data
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {building.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Already exists: {building.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} buildings')
        )