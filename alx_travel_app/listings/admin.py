"""
Admin configuration for the listings app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Listing, ListingImage, Booking, Review


class ListingImageInline(admin.TabularInline):
    """Inline admin for listing images"""
    model = ListingImage
    extra = 1
    fields = ['image', 'is_primary', 'caption']
    readonly_fields = ['upload_date']


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    """Admin configuration for Listing model"""
    list_display = [
        'title', 
        'listing_type', 
        'location', 
        'price_per_night', 
        'max_guests',
        'owner',
        'is_active',
        'created_at'
    ]
    list_filter = [
        'listing_type', 
        'is_active', 
        'created_at', 
        'max_guests',
        'bedrooms',
        'bathrooms'
    ]
    search_fields = ['title', 'location', 'description', 'owner__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'listing_type', 'is_active')
        }),
        ('Location & Pricing', {
            'fields': ('location', 'address', 'price_per_night')
        }),
        ('Property Details', {
            'fields': ('max_guests', 'bedrooms', 'bathrooms', 'amenities')
        }),
        ('Ownership', {
            'fields': ('owner',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ListingImageInline]
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('owner')


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    """Admin configuration for ListingImage model"""
    list_display = ['listing', 'is_primary', 'caption', 'upload_date', 'image_preview']
    list_filter = ['is_primary', 'upload_date']
    search_fields = ['listing__title', 'caption']
    readonly_fields = ['upload_date', 'image_preview']
    
    def image_preview(self, obj):
        """Display image preview in admin"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Preview"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin configuration for Booking model"""
    list_display = [
        'listing',
        'guest',
        'check_in_date',
        'check_out_date',
        'number_of_guests',
        'total_price',
        'status',
        'created_at'
    ]
    list_filter = [
        'status',
        'check_in_date',
        'check_out_date',
        'created_at',
        'number_of_guests'
    ]
    search_fields = [
        'listing__title',
        'guest__username',
        'guest__email',
        'special_requests'
    ]
    readonly_fields = ['created_at', 'updated_at', 'nights_count', 'calculated_total']
    date_hierarchy = 'check_in_date'
    
    fieldsets = (
        ('Booking Details', {
            'fields': ('listing', 'guest', 'status')
        }),
        ('Dates & Guests', {
            'fields': ('check_in_date', 'check_out_date', 'number_of_guests')
        }),
        ('Pricing', {
            'fields': ('total_price', 'calculated_total', 'nights_count')
        }),
        ('Additional Information', {
            'fields': ('special_requests',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def nights_count(self, obj):
        """Calculate number of nights"""
        if obj.check_in_date and obj.check_out_date:
            return (obj.check_out_date - obj.check_in_date).days
        return "N/A"
    nights_count.short_description = "Nights"
    
    def calculated_total(self, obj):
        """Show calculated total price"""
        if obj.check_in_date and obj.check_out_date and obj.listing:
            nights = (obj.check_out_date - obj.check_in_date).days
            return f"${nights * obj.listing.price_per_night}"
        return "N/A"
    calculated_total.short_description = "Calculated Total"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('listing', 'guest')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin configuration for Review model"""
    list_display = [
        'listing',
        'reviewer',
        'rating',
        'rating_stars',
        'created_at',
        'has_booking'
    ]
    list_filter = [
        'rating',
        'created_at',
        'updated_at'
    ]
    search_fields = [
        'listing__title',
        'reviewer__username',
        'comment'
    ]
    readonly_fields = ['created_at', 'updated_at', 'rating_stars']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Review Information', {
            'fields': ('listing', 'reviewer', 'booking')
        }),
        ('Review Content', {
            'fields': ('rating', 'rating_stars', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def rating_stars(self, obj):
        """Display rating as stars"""
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html(
            '<span style="color: gold; font-size: 16px;">{}</span>',
            stars
        )
    rating_stars.short_description = "Rating"
    
    def has_booking(self, obj):
        """Check if review is linked to a booking"""
        return bool(obj.booking)
    has_booking.short_description = "Has Booking"
    has_booking.boolean = True
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('listing', 'reviewer', 'booking')


# Additional admin customizations
admin.site.site_header = "Travel App Administration"
admin.site.site_title = "Travel App Admin"
admin.site.index_title = "Welcome to Travel App Administration"