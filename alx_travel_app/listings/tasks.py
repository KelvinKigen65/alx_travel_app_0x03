from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Booking

@shared_task
def send_booking_confirmation_email(booking_id):
    """
    Send booking confirmation email asynchronously
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        
        subject = f'Booking Confirmation - {booking.listing.title}'
        
        # Create email content
        message = f"""
        Dear {booking.guest.first_name or booking.guest.username},
        
        Your booking has been confirmed!
        
        Booking Details:
        - Property: {booking.listing.title}
        - Check-in: {booking.check_in_date}
        - Check-out: {booking.check_out_date}
        - Total Price: ${booking.total_price}
        
        Thank you for choosing our service!
        
        Best regards,
        ALX Travel Team
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.guest.email],
            fail_silently=False,
        )
        
        # Also send notification to host
        send_host_notification_email.delay(booking_id)
        
        return f"Email sent successfully to {booking.guest.email}"
        
    except Booking.DoesNotExist:
        return f"Booking with ID {booking_id} not found"
    except Exception as e:
        return f"Error sending email: {str(e)}"

@shared_task
def send_booking_status_update_email(booking_id, new_status):
    """
    Send booking status update email
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        
        status_messages = {
            'confirmed': 'Your booking has been confirmed!',
            'cancelled': 'Your booking has been cancelled.',
            'completed': 'Your booking has been completed. Thank you for staying with us!',
            'pending': 'Your booking is pending confirmation.'
        }
        
        subject = f'Booking Status Update - {booking.listing.title}'
        message = f"""
        Dear {booking.guest.first_name or booking.guest.username},
        
        {status_messages.get(new_status, 'Your booking status has been updated.')}
        
        Booking Details:
        - Property: {booking.listing.title}
        - Check-in: {booking.check_in_date}
        - Check-out: {booking.check_out_date}
        - Status: {new_status.upper()}
        - Total Price: ${booking.total_price}
        
        If you have any questions, please contact us.
        
        Best regards,
        ALX Travel Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.guest.email],
            fail_silently=False,
        )
        
        return f"Status update email sent to {booking.guest.email}"
        
    except Exception as e:
        return f"Error sending status update email: {str(e)}"

@shared_task
def send_booking_reminder_email(booking_id):
    """
    Send booking reminder email (example of additional task)
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        
        subject = f'Booking Reminder - {booking.listing.title}'
        message = f"""
        Dear {booking.guest.first_name or booking.guest.username},
        
        This is a reminder about your upcoming booking:
        
        - Property: {booking.listing.title}
        - Check-in: {booking.check_in_date}
        - Check-out: {booking.check_out_date}
        
        We look forward to hosting you!
        
        Best regards,
        ALX Travel Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.guest.email],
            fail_silently=False,
        )
        
        return f"Reminder email sent to {booking.guest.email}"
        
    except Exception as e:
        return f"Error sending reminder email: {str(e)}"

@shared_task
def send_host_notification_email(booking_id):
    """
    Send notification email to host when new booking is created
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        
        subject = f'New Booking - {booking.listing.title}'
        message = f"""
        Dear {booking.listing.owner.first_name or booking.listing.owner.username},
        
        You have received a new booking for your property!
        
        Booking Details:
        - Property: {booking.listing.title}
        - Guest: {booking.guest.first_name} {booking.guest.last_name}
        - Check-in: {booking.check_in_date}
        - Check-out: {booking.check_out_date}
        - Total Price: ${booking.total_price}
        - Status: {booking.status.upper()}
        
        Please log in to your dashboard to manage this booking.
        
        Best regards,
        ALX Travel Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.listing.owner.email],
            fail_silently=False,
        )
        
        return f"Host notification email sent to {booking.listing.owner.email}"
        
    except Exception as e:
        return f"Error sending host notification email: {str(e)}"