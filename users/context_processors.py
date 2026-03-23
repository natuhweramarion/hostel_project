def sidebar_counts(request):
    """Inject sidebar badge counts into every authenticated manager's context."""
    if not request.user.is_authenticated:
        return {}
    if not (request.user.is_manager or request.user.is_staff):
        return {}

    from payments.models import Payment
    from allocations.models import BookingRequest

    return {
        'pending_payments_count': Payment.objects.filter(status='pending').count(),
        'pending_booking_requests_count': BookingRequest.objects.filter(status='pending').count(),
    }
