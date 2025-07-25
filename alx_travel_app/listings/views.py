"""
Views for the listings app.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Listing, ListingImage, Booking, Review
from .serializers import ListingSerializer, ListingImageSerializer, BookingSerializer, ReviewSerializer


class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing listings
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        """Assign the current user as the owner when creating a listing"""
        serializer.save(owner=self.request.user)
    
    def get_queryset(self):
        """
        Optionally restricts the returned listings by filtering
        against query parameters in the URL.
        """
        queryset = Listing.objects.filter(is_active=True)
        
        # Filter by listing type
        listing_type = self.request.query_params.get('type')
        if listing_type:
            queryset = queryset.filter(listing_type=listing_type)
            
        # Filter by location
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
            
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        if min_price:
            try:
                queryset = queryset.filter(price_per_night__gte=float(min_price))
            except ValueError:
                pass  # Ignore invalid price values
            
        max_price = self.request.query_params.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(price_per_night__lte=float(max_price))
            except ValueError:
                pass  # Ignore invalid price values
            
        # Filter by number of guests
        guests = self.request.query_params.get('guests')
        if guests:
            try:
                queryset = queryset.filter(max_guests__gte=int(guests))
            except ValueError:
                pass  # Ignore invalid guest values
            
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )
            
        return queryset
    
    def perform_update(self, serializer):
        """Only allow owners to update their own listings"""
        if serializer.instance.owner != self.request.user:
            # This won't work as expected - we need to override the update method
            # perform_update doesn't return responses
            pass
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        """Override update to check ownership"""
        instance = self.get_object()
        if instance.owner != request.user:
            return Response(
                {'error': 'You can only update your own listings'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to check ownership"""
        instance = self.get_object()
        if instance.owner != request.user:
            return Response(
                {'error': 'You can only update your own listings'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only allow owners to delete their own listings"""
        instance = self.get_object()
        if instance.owner != request.user:
            return Response(
                {'error': 'You can only delete your own listings'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get all reviews for a specific listing"""
        listing = self.get_object()
        reviews = listing.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None):
        """Get all bookings for a specific listing (owner only)"""
        listing = self.get_object()
        if request.user != listing.owner:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        bookings = listing.bookings.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)


class ListingImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing listing images
    """
    queryset = ListingImage.objects.all()
    serializer_class = ListingImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        """Set the listing when creating an image"""
        listing_id = self.request.data.get('listing')
        if listing_id:
            try:
                listing = get_object_or_404(Listing, id=listing_id)
                # Check if user owns the listing
                if listing.owner != self.request.user:
                    return Response(
                        {'error': 'You can only add images to your own listings'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                serializer.save(listing=listing)
            except:
                serializer.save()
        else:
            serializer.save()
    
    def get_queryset(self):
        """Filter images by listing if specified"""
        queryset = ListingImage.objects.all()
        listing_id = self.request.query_params.get('listing')
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
        return queryset


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing bookings
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """Assign the current user as the guest when creating a booking"""
        serializer.save(guest=self.request.user)
    
    def get_queryset(self):
        """
        Users can only see their own bookings (as guest) or bookings for their listings (as owner)
        """
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Booking.objects.none()
        
        # Handle unauthenticated users
        if not self.request.user.is_authenticated:
            return Booking.objects.none()
        
        user = self.request.user
        return Booking.objects.filter(
            Q(guest=user) | Q(listing__owner=user)
        ).distinct()
    
    def update(self, request, *args, **kwargs):
        """Check permissions before updating booking"""
        instance = self.get_object()
        user = request.user
        
        # Only guest or listing owner can update booking
        if instance.guest != user and instance.listing.owner != user:
            return Response(
                {'error': 'You can only update your own bookings or bookings for your listings'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Check permissions before partially updating booking"""
        instance = self.get_object()
        user = request.user
        
        # Only guest or listing owner can update booking
        if instance.guest != user and instance.listing.owner != user:
            return Response(
                {'error': 'You can only update your own bookings or bookings for your listings'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only allow guests or listing owners to cancel bookings"""
        instance = self.get_object()
        user = request.user
        
        # Only guest or listing owner can cancel booking
        if instance.guest != user and instance.listing.owner != user:
            return Response(
                {'error': 'You can only cancel your own bookings or bookings for your listings'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update booking status (owner only)"""
        booking = self.get_object()
        
        # Only listing owner can update booking status
        if request.user != booking.listing.owner:
            return Response(
                {'error': 'Only listing owner can update booking status'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        if new_status not in ['pending', 'confirmed', 'cancelled', 'completed']:
            return Response(
                {'error': 'Invalid status. Must be one of: pending, confirmed, cancelled, completed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = new_status
        booking.save()
        
        serializer = BookingSerializer(booking)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing reviews
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """Assign the current user as the reviewer when creating a review"""
        serializer.save(reviewer=self.request.user)
    
    def get_queryset(self):
        """
        Filter reviews by listing if specified
        """
        queryset = Review.objects.all()
        listing_id = self.request.query_params.get('listing')
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
        return queryset
    
    def update(self, request, *args, **kwargs):
        """Only allow users to update their own reviews"""
        instance = self.get_object()
        if instance.reviewer != request.user:
            return Response(
                {'error': 'You can only update your own reviews'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Only allow users to partially update their own reviews"""
        instance = self.get_object()
        if instance.reviewer != request.user:
            return Response(
                {'error': 'You can only update your own reviews'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only allow users to delete their own reviews"""
        instance = self.get_object()
        if instance.reviewer != request.user:
            return Response(
                {'error': 'You can only delete your own reviews'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)