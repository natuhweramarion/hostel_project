from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import Http404
from .models import Payment
from .forms import PaymentForm
from users.decorators import manager_required, student_required

@login_required
@manager_required
def payment_list(request):
    """List all payments — managers only. Paginated at 20 per page."""
    qs = Payment.objects.select_related('user', 'verified_by').all()
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'payments/payment_list.html', {'page_obj': page_obj})

@login_required
@student_required
def create_payment(request):
    """Create new payment record — students only."""
    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.save()
            messages.success(request, 'Payment record created successfully. Awaiting verification.')
            return redirect('student_dashboard')
    else:
        form = PaymentForm()
    
    return render(request, 'payments/create_payment.html', {'form': form})

@login_required
@manager_required
def verify_payment(request, payment_id):
    """Verify a payment — managers only."""
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        from users.models import create_notification
        if action == 'verify':
            payment.status = 'verified'
            payment.verified_by = request.user
            payment.date_verified = timezone.now()
            payment.save()
            create_notification(
                user=payment.user,
                message=(
                    f'Your payment of UGX {payment.amount:,.0f} '
                    f'(Ref: {payment.reference_number}) has been verified. '
                    f'You are now eligible for room allocation.'
                ),
                notif_type='payment',
                link='/dashboard/student/',
            )
            messages.success(request, f'Payment {payment.reference_number} verified successfully.')
        elif action == 'reject':
            payment.status = 'rejected'
            payment.verified_by = request.user
            payment.date_verified = timezone.now()
            payment.save()
            create_notification(
                user=payment.user,
                message=(
                    f'Your payment (Ref: {payment.reference_number}) was rejected. '
                    f'Please check your transaction reference number and resubmit.'
                ),
                notif_type='payment',
                link='/payments/create/',
            )
            messages.warning(request, f'Payment {payment.reference_number} rejected.')

        return redirect('payment_list')
    
    return render(request, 'payments/verify_payment.html', {'payment': payment})


@login_required
def payment_receipt(request, payment_id):
    """Printable payment + allocation receipt — accessible by the owning student or any manager."""
    payment = get_object_or_404(Payment, id=payment_id)

    # Only the student who made the payment, or a manager, can view the receipt
    is_manager = request.user.is_manager or request.user.is_staff
    if not is_manager and payment.user != request.user:
        raise Http404

    # Get the student's active (or most recent) allocation
    from allocations.models import Allocation
    allocation = Allocation.objects.filter(
        user=payment.user
    ).select_related('room__block__hostel').order_by('-date_allocated').first()

    context = {
        'payment': payment,
        'allocation': allocation,
        'student': payment.user,
        'is_manager': is_manager,
    }
    return render(request, 'payments/payment_receipt.html', context)
