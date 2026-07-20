"""Seeds the location/travel-fee list used by the booking form's location
dropdown, matching the original frontend's lib/data.js `locations` array.

Usage: python manage.py seed_locations
"""
from django.core.management.base import BaseCommand

from bookings.models import Location

LOCATIONS = [
    ('Law Gate', 0), ('Phagwara', 0), ('Jalandhar', 0), ('Phillaur', 500), ('Nakodar', 700),
    ('Kapurthala', 800), ('Hoshiarpur', 1000), ('Nawanshahr', 1000), ('Ludhiana', 1500),
    ('Ropar', 1800), ('Chandigarh', 2500), ('Mohali', 2500), ('Panchkula', 2700),
    ('Patiala', 3000), ('Ambala', 3000), ('Amritsar', 3000), ('Pathankot', 4000),
    ('Shimla', 5000), ('Delhi NCR', 5000), ('Gurugram', 5500), ('Noida', 5500),
    ('Faridabad', 5500), ('Jaipur', 8000),
]


class Command(BaseCommand):
    help = 'Seeds the booking location / travel-fee list.'

    def handle(self, *args, **options):
        for i, (name, fee) in enumerate(LOCATIONS):
            Location.objects.update_or_create(name=name, defaults={'travel_fee': fee, 'order': i})
        self.stdout.write(self.style.SUCCESS(f'Locations: {len(LOCATIONS)}'))
