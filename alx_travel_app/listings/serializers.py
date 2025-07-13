"""
Serializers for the listings app.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Listing, ListingImage, Booking, Review


class ListingImageSerializer(serializers.ModelSerializer):
    """
    Serializer for listing images
    """
    class Meta:
        model = ListingImage
        fields = ['id', 'image', 'is_primary', 'caption', 'upload_date']


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for reviews
    """
    reviewer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'reviewer', 'reviewer_name', 
                 'created_at', 'updated_at']
        read_only_fields = ['reviewer', 'created_at', 'updated_at']
    
    def get_reviewer_name(self, obj):
        return obj.reviewer.get_full_name() if obj.reviewer.get_full_name() else obj.reviewer.username


class ListingSerializer(serializers.ModelSerializer):
    """
    Serializer for listings
    """
    images = ListingImageSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    owner_name = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = ['id', 'title', 'description', 'listing_type', 'price_per_night',
                 'location', 'address', 'max_guests', 'bedrooms', 'bathrooms',
                 'amenities', 'owner', 'owner_name', 'is_active', 'created_at',
                 'updated_at', 'images', 'reviews', 'average_rating', 'review_count']
        read_only_fields = ['owner', 'created_at', 'updated_at']
    
    def get_owner_name(self, obj):
        return obj.owner.get_full_name() if obj.owner.get_full_name() else obj.owner.username
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0
    
    def get_review_count(self, obj):
        return obj.reviews.count()


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for bookings
    """
    guest_name = serializers.SerializerMethodField()
    listing_title = serializers.SerializerMethodField()
    nights_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = ['id', 'listing', 'listing_title', 'guest', 'guest_name',
                 'check_in_date', 'check_out_date', 'number_of_guests',
                 'total_price', 'status', 'special_requests', 'nights_count',
                 'created_at', 'updated_at']
        read_only_fields = ['guest', 'total_price', 'created_at', 'updated_at']
    
    def get_guest_name(self, obj):
        return obj.guest.get_full_name() if obj.guest.get_full_name() else obj.guest.username
    
    def get_listing_title(self, obj):
        return obj.listing.title
    
    def get_nights_count(self, obj):
        if obj.check_in_date and obj.check_out_date:
            return (obj.check_out_date - obj.check_in_date).days
        return 0
    
    def validate(self, data):
        """
        Check that check_in_date is before check_out_date and validate guest capacity
        """
        if data.get('check_in_date') and data.get('check_out_date'):
            if data['check_in_date'] >= data['check_out_date']:
                raise serializers.ValidationError(
                    "Check-in date must be before check-out date"
                )
        
        if data.get('number_of_guests') and data.get('listing'):
            if data['number_of_guests'] > data['listing'].max_guests:
                raise serializers.ValidationError(
                    f"Number of guests ({data['number_of_guests']}) exceeds "
                    f"listing capacity ({data['listing'].max_guests})"
                )
        
        return data
    
    def create(self, validated_data):
        # Calculate total price
        if 'check_in_date' in validated_data and 'check_out_date' in validated_data:
            nights = (validated_data['check_out_date'] - validated_data['check_in_date']).days
            validated_data['total_price'] = nights * validated_data['listing'].price_per_night
        
        return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model (for nested representations)
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = ['id', 'username']
    
    def get_full_name(self, obj):
        return obj.get_full_name() if obj.get_full_name() else obj.username