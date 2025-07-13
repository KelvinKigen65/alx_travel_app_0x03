"""
Views for the listings app.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Listing, ListingImage, Booking, Review, Booking, Payment
from .serializers import ListingSerializer, ListingImageSerializer, BookingSerializer, ReviewSerializer, PaymentSerializer
from rest_framework.views import APIView
from .services import ChapaService
import uuid
import logging

logger = logging.getLogger(__name__)


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
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Check availability for a specific listing"""
        listing = self.get_object()
        check_in = request.query_params.get('check_in')
        check_out = request.query_params.get('check_out')
        
        if not check_in or not check_out:
            return Response(
                {'error': 'check_in and check_out dates are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for overlapping bookings
        overlapping_bookings = listing.bookings.filter(
            status__in=['confirmed', 'pending'],
            check_in__lt=check_out,
            check_out__gt=check_in
        )
        
        is_available = not overlapping_bookings.exists()
        
        return Response({
            'available': is_available,
            'listing_id': listing.id,
            'check_in': check_in,
            'check_out': check_out
        })


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
    
    def destroy(self, request, *args, **kwargs):
        """Only allow listing owners to delete images"""
        instance = self.get_object()
        if instance.listing.owner != request.user:
            return Response(
                {'error': 'You can only delete images from your own listings'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing bookings
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """Assign the current user as the guest when creating a booking"""
        booking = serializer.save(guest=self.request.user)
        
        # Import here to avoid circular imports
        from .tasks import send_booking_confirmation_email
        
        # Trigger email task asynchronously
        send_booking_confirmation_email.delay(booking.id)
        
        return booking
    
    def create(self, request, *args, **kwargs):
        """Create booking and trigger email notification"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check availability before creating booking
        listing_id = serializer.validated_data.get('listing').id
        check_in = serializer.validated_data.get('check_in')
        check_out = serializer.validated_data.get('check_out')
        
        overlapping_bookings = Booking.objects.filter(
            listing_id=listing_id,
            status__in=['confirmed', 'pending'],
            check_in__lt=check_out,
            check_out__gt=check_in
        )
        
        if overlapping_bookings.exists():
            return Response(
                {'error': 'Listing is not available for the selected dates'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking = self.perform_create(serializer)
        
        return Response(
            {
                'message': 'Booking created successfully. Confirmation email will be sent shortly.',
                'booking': BookingSerializer(booking).data
            },
            status=status.HTTP_201_CREATED
        )
    
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
        
        # Send status update email if booking is confirmed
        if new_status == 'confirmed':
            from .tasks import send_booking_status_update_email
            send_booking_status_update_email.delay(booking.id, new_status)
        
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
        # Check if user has a completed booking for this listing
        listing = serializer.validated_data.get('listing')
        has_booking = Booking.objects.filter(
            guest=self.request.user,
            listing=listing,
            status='completed'
        ).exists()
        
        if not has_booking:
            return Response(
                {'error': 'You can only review listings you have booked and completed'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save(reviewer=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create review with booking validation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if user has a completed booking for this listing
        listing = serializer.validated_data.get('listing')
        has_booking = Booking.objects.filter(
            guest=request.user,
            listing=listing,
            status='completed'
        ).exists()
        
        if not has_booking:
            return Response(
                {'error': 'You can only review listings you have booked and completed'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user has already reviewed this listing
        existing_review = Review.objects.filter(
            reviewer=request.user,
            listing=listing
        ).exists()
        
        if existing_review:
            return Response(
                {'error': 'You have already reviewed this listing'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
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


class InitiatePaymentView(APIView):
    """
    API view to initiate payment for a booking
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, booking_id):
        try:
            booking = get_object_or_404(Booking, id=booking_id)
            
            # Check if user is the guest for this booking
            if booking.guest != request.user:
                return Response(
                    {'error': 'You can only initiate payment for your own bookings'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if booking is confirmed
            if booking.status != 'confirmed':
                return Response(
                    {'error': 'Booking must be confirmed before payment'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if payment already exists
            existing_payment = Payment.objects.filter(
                booking=booking,
                status='completed'
            ).first()
            
            if existing_payment:
                return Response(
                    {'error': 'Payment already completed for this booking'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            tx_ref = f"alx-travel-{uuid.uuid4().hex}"
            
            response = ChapaService.initiate_payment(
                amount=booking.total_price,
                email=request.user.email,
                tx_ref=tx_ref,
                first_name=request.user.first_name,
                last_name=request.user.last_name,
            )
            
            # Create or update payment record
            payment, created = Payment.objects.get_or_create(
                booking=booking,
                defaults={
                    'transaction_id': tx_ref,
                    'amount': booking.total_price,
                    'status': 'pending'
                }
            )
            
            if not created:
                payment.transaction_id = tx_ref
                payment.status = 'pending'
                payment.save()
            
            return Response({
                "checkout_url": response['data']['checkout_url'],
                "transaction_id": tx_ref
            })
            
        except Exception as e:
            logger.error(f"Payment initiation failed: {str(e)}")
            return Response(
                {'error': f'Payment initiation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentWebhookView(APIView):
    """
    API view to handle payment webhook from Chapa
    """
    permission_classes = []  # No authentication required for webhooks
    
    def post(self, request):
        try:
            tx_ref = request.data.get('tx_ref')
            status_received = request.data.get('status')
            
            if not tx_ref:
                return Response(
                    {'error': 'Transaction reference is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            payment = get_object_or_404(Payment, transaction_id=tx_ref)
            
            # Update payment status
            if status_received == 'successful':
                payment.status = 'completed'
                payment.booking.status = 'confirmed'  # Update booking status
                payment.booking.save()
            elif status_received == 'failed':
                payment.status = 'failed'
            else:
                payment.status = 'pending'
            
            payment.save()
            
            # Send payment confirmation email if payment is successful
            if status_received == 'successful':
                from .tasks import send_payment_confirmation_email
                send_payment_confirmation_email.delay(payment.booking.id)
            
            return Response({"status": "success"})
            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for transaction: {tx_ref}")
            return Response(
                {'error': 'Payment not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Payment webhook error: {str(e)}")
            return Response(
                {'error': f'Webhook processing failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentStatusView(APIView):
    """
    API view to check payment status
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, booking_id):
        try:
            booking = get_object_or_404(Booking, id=booking_id)
            
            # Check if user is the guest for this booking
            if booking.guest != request.user:
                return Response(
                    {'error': 'You can only check payment status for your own bookings'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            try:
                payment = Payment.objects.get(booking=booking)
                serializer = PaymentSerializer(payment)
                return Response(serializer.data)
            except Payment.DoesNotExist:
                return Response(
                    {'error': 'No payment found for this booking'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
        except Exception as e:
            logger.error(f"Payment status check failed: {str(e)}")
            return Response(
                {'error': f'Payment status check failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MyListingsView(APIView):
    """
    API view to get current user's listings
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        listings = Listing.objects.filter(owner=request.user)
        serializer = ListingSerializer(listings, many=True)
        return Response(serializer.data)


class MyBookingsView(APIView):
    """
    API view to get current user's bookings
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        bookings = Booking.objects.filter(guest=request.user)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)


class MyReviewsView(APIView):
    """
    API view to get current user's reviews
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        reviews = Review.objects.filter(reviewer=request.user)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class DashboardStatsView(APIView):
    """
    API view to get dashboard statistics for listing owners
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get user's listings
        listings = Listing.objects.filter(owner=user)
        
        # Get bookings for user's listings
        bookings = Booking.objects.filter(listing__owner=user)
        
        # Calculate statistics
        stats = {
            'total_listings': listings.count(),
            'active_listings': listings.filter(is_active=True).count(),
            'total_bookings': bookings.count(),
            'pending_bookings': bookings.filter(status='pending').count(),
            'confirmed_bookings': bookings.filter(status='confirmed').count(),
            'completed_bookings': bookings.filter(status='completed').count(),
            'cancelled_bookings': bookings.filter(status='cancelled').count(),
            'total_revenue': sum(
                booking.total_price for booking in bookings.filter(status='completed')
            ),
            'recent_bookings': BookingSerializer(
                bookings.order_by('-created_at')[:5], many=True
            ).data
        }
        
        return Response(stats)