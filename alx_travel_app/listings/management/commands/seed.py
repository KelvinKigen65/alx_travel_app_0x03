"""
Management command to seed the database with sample data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import random
from listings.models import Listing, Booking, Review


class Command(BaseCommand):
    help = 'Seed the database with sample listings, bookings, and reviews'

    def add_arguments(self, parser):
        parser.add_argument(
            '--listings',
            type=int,
            default=20,
            help='Number of listings to create (default: 20)'
        )
        parser.add_argument(
            '--bookings',
            type=int,
            default=50,
            help='Number of bookings to create (default: 50)'
        )
        parser.add_argument(
            '--reviews',
            type=int,
            default=30,
            help='Number of reviews to create (default: 30)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Review.objects.all().delete()
            Booking.objects.all().delete()
            Listing.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        # Create users if they don't exist
        self.create_users()
        
        # Create listings
        self.create_listings(options['listings'])
        
        # Create bookings
        self.create_bookings(options['bookings'])
        
        # Create reviews
        self.create_reviews(options['reviews'])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded database with '
                f'{options["listings"]} listings, '
                f'{options["bookings"]} bookings, and '
                f'{options["reviews"]} reviews.'
            )
        )

    def create_users(self):
        """Create sample users"""
        sample_users = [
            {'username': 'host1', 'email': 'host1@example.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'username': 'host2', 'email': 'host2@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'username': 'host3', 'email': 'host3@example.com', 'first_name': 'Bob', 'last_name': 'Johnson'},
            {'username': 'guest1', 'email': 'guest1@example.com', 'first_name': 'Alice', 'last_name': 'Wilson'},
            {'username': 'guest2', 'email': 'guest2@example.com', 'first_name': 'Charlie', 'last_name': 'Brown'},
            {'username': 'guest3', 'email': 'guest3@example.com', 'first_name': 'Diana', 'last_name': 'Davis'},
            {'username': 'guest4', 'email': 'guest4@example.com', 'first_name': 'Eva', 'last_name': 'Miller'},
            {'username': 'guest5', 'email': 'guest5@example.com', 'first_name': 'Frank', 'last_name': 'Garcia'},
        ]
        
        for user_data in sample_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {user.username}')

    def create_listings(self, count):
        """Create sample listings"""
        hosts = User.objects.filter(username__startswith='host')
        
        sample_listings = [
            {
                'title': 'Cozy Downtown Apartment',
                'description': 'Beautiful apartment in the heart of the city with modern amenities.',
                'listing_type': 'apartment',
                'location': 'Downtown',
                'address': '123 Main St, City Center',
                'price_per_night': 120.00,
                'max_guests': 4,
                'bedrooms': 2,
                'bathrooms': 1,
                'amenities': 'WiFi, Kitchen, Air Conditioning, TV'
            },
            {
                'title': 'Luxury Beach Villa',
                'description': 'Stunning villa with ocean views and private beach access.',
                'listing_type': 'villa',
                'location': 'Beachfront',
                'address': '456 Ocean Drive, Beach City',
                'price_per_night': 350.00,
                'max_guests': 8,
                'bedrooms': 4,
                'bathrooms': 3,
                'amenities': 'Pool, Beach Access, WiFi, Kitchen, BBQ'
            },
            {
                'title': 'Mountain Resort Suite',
                'description': 'Peaceful retreat in the mountains with hiking trails nearby.',
                'listing_type': 'resort',
                'location': 'Mountain View',
                'address': '789 Mountain Rd, Alpine Valley',
                'price_per_night': 200.00,
                'max_guests': 6,
                'bedrooms': 3,
                'bathrooms': 2,
                'amenities': 'Spa, Gym, Restaurant, WiFi, Fireplace'
            },
            {
                'title': 'Historic City Hotel',
                'description': 'Classic hotel in historic district with vintage charm.',
                'listing_type': 'hotel',
                'location': 'Historic District',
                'address': '321 Heritage Ave, Old Town',
                'price_per_night': 180.00,
                'max_guests': 2,
                'bedrooms': 1,
                'bathrooms': 1,
                'amenities': 'Concierge, Restaurant, WiFi, Room Service'
            },
            {
                'title': 'Budget Friendly Hostel',
                'description': 'Clean and safe hostel for budget travelers.',
                'listing_type': 'hostel',
                'location': 'Student Quarter',
                'address': '654 College St, University Area',
                'price_per_night': 45.00,
                'max_guests': 1,
                'bedrooms': 1,
                'bathrooms': 1,
                'amenities': 'Shared Kitchen, WiFi, Laundry, Common Room'
            },
        ]
        
        # Generate additional listings
        locations = ['Downtown', 'Beachfront', 'Mountain View', 'Historic District', 'Suburbs', 'City Center']
        listing_types = ['hotel', 'apartment', 'villa', 'resort', 'hostel']
        
        for i in range(count):
            if i < len(sample_listings):
                listing_data = sample_listings[i].copy()
            else:
                listing_data = {
                    'title': f'Sample Listing {i+1}',
                    'description': f'This is a sample listing #{i+1} with great amenities.',
                    'listing_type': random.choice(listing_types),
                    'location': random.choice(locations),
                    'address': f'{random.randint(100, 999)} Sample St, Location {i+1}',
                    'price_per_night': random.randint(50, 400),
                    'max_guests': random.randint(1, 8),
                    'bedrooms': random.randint(1, 4),
                    'bathrooms': random.randint(1, 3),
                    'amenities': 'WiFi, Kitchen, TV'
                }
            
            listing_data['owner'] = random.choice(hosts)
            
            listing = Listing.objects.create(**listing_data)
            self.stdout.write(f'Created listing: {listing.title}')

    def create_bookings(self, count):
        """Create sample bookings"""
        listings = list(Listing.objects.all())
        guests = User.objects.filter(username__startswith='guest')
        
        if not listings or not guests:
            self.stdout.write(self.style.WARNING('No listings or guests found. Skipping booking creation.'))
            return
        
        statuses = ['pending', 'confirmed', 'cancelled', 'completed']
        
        for i in range(count):
            listing = random.choice(listings)
            guest = random.choice(guests)
            
            # Generate random dates
            start_date = timezone.now().date() + timedelta(days=random.randint(-30, 60))
            end_date = start_date + timedelta(days=random.randint(1, 7))
            
            booking_data = {
                'listing': listing,
                'guest': guest,
                'check_in_date': start_date,
                'check_out_date': end_date,
                'number_of_guests': random.randint(1, listing.max_guests),
                'status': random.choice(statuses),
                'special_requests': random.choice([
                    '', 
                    'Late check-in requested',
                    'Extra towels needed',
                    'Quiet room preferred',
                    'Airport pickup required'
                ])
            }
            
            try:
                booking = Booking.objects.create(**booking_data)
                self.stdout.write(f'Created booking: {booking}')
            except Exception as e:
                self.stdout.write(f'Failed to create booking: {e}')

    def create_reviews(self, count):
        """Create sample reviews"""
        # Get completed bookings for reviews
        completed_bookings = list(Booking.objects.filter(status='completed'))
        
        if not completed_bookings:
            # Create some reviews without bookings
            listings = list(Listing.objects.all())
            guests = User.objects.filter(username__startswith='guest')
            
            if not listings or not guests:
                self.stdout.write(self.style.WARNING('No listings or guests found. Skipping review creation.'))
                return
        
        review_comments = [
            'Amazing place! Highly recommended.',
            'Great location and clean facilities.',
            'Perfect for a weekend getaway.',
            'Host was very responsive and helpful.',
            'Beautiful views and comfortable stay.',
            'Good value for money.',
            'Could use some improvements but overall decent.',
            'Not as described, disappointing experience.',
            'Excellent service and amenities.',
            'Will definitely book again!'
        ]
        
        created_reviews = 0
        attempts = 0
        max_attempts = count * 3
        
        while created_reviews < count and attempts < max_attempts:
            attempts += 1
            
            if completed_bookings and random.choice([True, False]):
                # Create review from booking
                booking = random.choice(completed_bookings)
                if hasattr(booking, 'review'):
                    continue  # Skip if review already exists
                
                review_data = {
                    'listing': booking.listing,
                    'reviewer': booking.guest,
                    'booking': booking,
                    'rating': random.randint(1, 5),
                    'comment': random.choice(review_comments)
                }
            else:
                # Create standalone review
                listings = list(Listing.objects.all())
                guests = User.objects.filter(username__startswith='guest')
                
                if not listings or not guests:
                    break
                
                listing = random.choice(listings)
                reviewer = random.choice(guests)
                
                # Check if review already exists
                if Review.objects.filter(listing=listing, reviewer=reviewer).exists():
                    continue
                
                # Don't let owner review their own listing
                if reviewer == listing.owner:
                    continue
                
                review_data = {
                    'listing': listing,
                    'reviewer': reviewer,
                    'rating': random.randint(1, 5),
                    'comment': random.choice(review_comments)
                }
            
            try:
                review = Review.objects.create(**review_data)
                self.stdout.write(f'Created review: {review}')
                created_reviews += 1
            except Exception as e:
                self.stdout.write(f'Failed to create review: {e}')
        
        if created_reviews < count:
            self.stdout.write(
                self.style.WARNING(
                    f'Only created {created_reviews} reviews out of {count} requested.'
                )
            )