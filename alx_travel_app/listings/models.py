"""
Models for the listings app.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Listing(models.Model):
    """
    Model representing a travel listing
    """
    LISTING_TYPES = (
        ('hotel', 'Hotel'),
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('resort', 'Resort'),
        ('hostel', 'Hostel'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPES)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255)
    address = models.TextField()
    max_guests = models.PositiveIntegerField()
    bedrooms = models.PositiveIntegerField()
    bathrooms = models.PositiveIntegerField()
    amenities = models.TextField(blank=True)  # Store as comma-separated values
    
    # Owner information
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    
    # Meta information
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class ListingImage(models.Model):
    """
    Model for storing images related to a listing
    """
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listings/')
    is_primary = models.BooleanField(default=False)
    caption = models.CharField(max_length=200, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'upload_date']
    
    def __str__(self):
        return f"Image for {self.listing.title}"


class Booking(models.Model):
    """
    Model representing a booking for a listing
    """
    BOOKING_STATUS = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_guests = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    
    # Special requests or notes
    special_requests = models.TextField(blank=True)
    
    # Booking metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Booking for {self.listing.title} by {self.guest.username}"
    
    def save(self, *args, **kwargs):
        # Calculate total price if not provided
        if not self.total_price and self.check_in_date and self.check_out_date:
            nights = (self.check_out_date - self.check_in_date).days
            self.total_price = nights * self.listing.price_per_night
        super().save(*args, **kwargs)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate check-in is before check-out
        if self.check_in_date and self.check_out_date:
            if self.check_in_date >= self.check_out_date:
                raise ValidationError("Check-in date must be before check-out date")
        
        # Validate number of guests doesn't exceed listing capacity
        if self.number_of_guests and self.listing and self.number_of_guests > self.listing.max_guests:
            raise ValidationError(f"Number of guests ({self.number_of_guests}) exceeds listing capacity ({self.listing.max_guests})")


class Review(models.Model):
    """
    Model representing a review for a listing
    """
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review', null=True, blank=True)
    
    # Review content
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    
    # Review metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        # Ensure one review per user per listing
        unique_together = ['listing', 'reviewer']
    
    def __str__(self):
        return f"Review for {self.listing.title} by {self.reviewer.username} - {self.rating}/5"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Ensure reviewer is not the listing owner
        if self.reviewer == self.listing.owner:
            raise ValidationError("Listing owner cannot review their own listing")