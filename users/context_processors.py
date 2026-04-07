def sidebar_counts(request):
    """Inject sidebar badge counts and notification count into every authenticated page."""
    if not request.user.is_authenticated:
        return {}

    from users.models import Notification
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    ctx = {'unread_notifications': unread_notifications}

    if request.user.is_manager or request.user.is_staff:
        from payments.models import Payment
        from allocations.models import BookingRequest
        ctx['pending_payments_count'] = Payment.objects.filter(status='pending').count()
        ctx['pending_booking_requests_count'] = BookingRequest.objects.filter(status='pending').count()

    return ctx
