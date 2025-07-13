"""
URLs for the listings app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, ListingImageViewSet, BookingViewSet, ReviewViewSet
from .views import InitiatePaymentView, PaymentWebhookView


# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'listing-images', ListingImageViewSet, basename='listingimage')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'reviews', ReviewViewSet, basename='review')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('api/', include(router.urls)),
    path('bookings/<int:booking_id>/pay/', InitiatePaymentView.as_view(), name='initiate-payment'),
    path('payments/webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
]