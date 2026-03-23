from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.db import models
from .models import Allocation, BookingRequest
from hostels.models import Room, Hostel
from .forms import AllocationForm
from users.decorators import manager_required, student_required

User = get_user_model()


@login_required
@manager_required
def allocation_list(request):
    """List all allocations — managers only. Supports search and status filter."""
    qs = Allocation.objects.select_related('user', 'room__block__hostel').all()
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    if q:
        qs = qs.filter(
            models.Q(user__first_name__icontains=q) |
            models.Q(user__last_name__icontains=q) |
            models.Q(user__username__icontains=q) |
            models.Q(user__student_id__icontains=q) |
            models.Q(room__room_number__icontains=q) |
            models.Q(room__block__hostel__name__icontains=q)
        )
    if status_filter:
        qs = qs.filter(status=status_filter)
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'allocations/allocation_list.html', {'page_obj': page_obj})


@login_required
@manager_required
def create_allocation(request):
    """Create new allocation — managers only.
    Accepts optional query params ?student=<pk>&hostel=<pk> from booking request workflow.
    """
    if request.method == 'POST':
        form = AllocationForm(request.POST)
        if form.is_valid():
            try:
                allocation = form.save()
                # Mark related booking request as approved, if any
                BookingRequest.objects.filter(
                    student=allocation.user,
                    status='pending'
                ).update(status='approved')
                messages.success(request, f'Allocation created successfully for {allocation.user.get_full_name() or allocation.user.username}')
                return redirect('allocation_list')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        # Pre-fill form from booking request query params
        initial = {}
        student_pk = request.GET.get('student')
        if student_pk:
            initial['user'] = student_pk
        form = AllocationForm(initial=initial)

    from django.db.models import Count, Q, F
    available_rooms = Room.objects.annotate(
        active_count=Count('allocations', filter=Q(allocations__status='active'))
    ).filter(active_count__lt=F('capacity')).select_related('block__hostel')

    # Pass prefill hints for the template
    prefill_student = request.GET.get('student')
    prefill_hostel = request.GET.get('hostel')

    return render(request, 'allocations/create_allocation.html', {
        'form': form,
        'available_rooms': available_rooms,
        'prefill_student': prefill_student,
        'prefill_hostel': prefill_hostel,
    })


@login_required
@manager_required
def available_rooms(request):
    """Show available rooms — managers only."""
    hostels = Hostel.objects.prefetch_related('blocks__rooms__allocations').all()
    return render(request, 'allocations/available_rooms.html', {'hostels': hostels})


@login_required
@manager_required
def vacate_allocation(request, allocation_id):
    """Mark an active allocation as 'left' — managers only."""
    from django.utils import timezone
    allocation = get_object_or_404(Allocation, id=allocation_id, status='active')
    if request.method == 'POST':
        allocation.status = 'left'
        allocation.date_left = timezone.now()
        # Use update() to bypass full_clean so we don't re-trigger capacity checks
        Allocation.objects.filter(pk=allocation.pk).update(
            status='left',
            date_left=timezone.now()
        )
        messages.success(
            request,
            f'{allocation.user.get_full_name()} has been marked as vacated from Room {allocation.room.room_number}.'
        )
        return redirect('allocation_list')
    return redirect('allocation_list')


# ─────────────────────────────────────────────────────────
#  STUDENT HOSTEL BROWSING & BOOKING REQUESTS
# ─────────────────────────────────────────────────────────

@login_required
@student_required
def student_hostels(request):
    """Hostel listing for logged-in students — shows rooms, prices, and booking option."""
    hostels = Hostel.objects.prefetch_related('blocks__rooms__allocations').order_by('name')

    # Student's current active allocation (if any)
    active_allocation = Allocation.objects.filter(
        user=request.user, status='active'
    ).select_related('room__block__hostel').first()

    # Student's active booking request (pending or approved)
    active_request = BookingRequest.objects.filter(
        student=request.user, status__in=['pending', 'approved']
    ).select_related('preferred_hostel').first()

    hostel_data = []
    for hostel in hostels:
        total = hostel.total_capacity()
        available = hostel.available_spaces()

        # Room type breakdown
        room_types = {}
        for block in hostel.blocks.all():
            for room in block.rooms.all():
                key = room.room_type or 'Other'
                if key not in room_types:
                    room_types[key] = {
                        'label': room.room_type or 'Other',
                        'price': room.price_per_semester,
                        'total_beds': 0,
                        'available_beds': 0,
                    }
                room_types[key]['total_beds'] += room.capacity
                room_types[key]['available_beds'] += room.available_beds()
                if room_types[key]['price'] is None and room.price_per_semester:
                    room_types[key]['price'] = room.price_per_semester

        hostel_data.append({
            'hostel': hostel,
            'total_capacity': total,
            'available_spaces': available,
            'occupied': total - available,
            'occupancy_pct': round((total - available) / total * 100) if total > 0 else 0,
            'room_types': list(room_types.values()),
            'is_requested': active_request and active_request.preferred_hostel_id == hostel.pk,
        })

    context = {
        'hostel_data': hostel_data,
        'active_allocation': active_allocation,
        'active_request': active_request,
    }
    return render(request, 'allocations/student_hostels.html', context)


@login_required
@student_required
def create_booking_request(request, hostel_id):
    """Student submits a booking request for a hostel."""
    hostel = get_object_or_404(Hostel, pk=hostel_id)

    # Block if already allocated
    if Allocation.objects.filter(user=request.user, status='active').exists():
        messages.warning(request, 'You already have an active room allocation.')
        return redirect('student_hostels')

    # Block if already has a pending/approved request
    existing = BookingRequest.objects.filter(
        student=request.user, status__in=['pending', 'approved']
    ).first()
    if existing:
        messages.warning(
            request,
            f'You already have a {existing.status} booking request for {existing.preferred_hostel.name}. '
            'Cancel it first to request a different hostel.'
        )
        return redirect('student_hostels')

    if request.method == 'POST':
        academic_year = request.POST.get('academic_year', '').strip()
        note = request.POST.get('message', '').strip()
        if not academic_year:
            messages.error(request, 'Please enter your academic year.')
            return render(request, 'allocations/booking_request_form.html', {'hostel': hostel})

        BookingRequest.objects.create(
            student=request.user,
            preferred_hostel=hostel,
            academic_year=academic_year,
            message=note or None,
        )
        messages.success(
            request,
            f'Booking request for {hostel.name} submitted successfully! '
            'The hostel office will review your request.'
        )
        return redirect('student_hostels')

    return render(request, 'allocations/booking_request_form.html', {'hostel': hostel})


@login_required
@student_required
def cancel_booking_request(request, request_id):
    """Student cancels their own pending booking request."""
    booking = get_object_or_404(BookingRequest, pk=request_id, student=request.user)
    if request.method == 'POST':
        if booking.status == 'pending':
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, 'Booking request cancelled.')
        else:
            messages.warning(request, f'Cannot cancel a request with status: {booking.status}.')
    return redirect('student_hostels')


@login_required
@manager_required
def booking_requests_admin(request):
    """Admin view — list all booking requests."""
    status_filter = request.GET.get('status', 'pending')
    qs = BookingRequest.objects.select_related(
        'student', 'preferred_hostel', 'reviewed_by'
    ).all()
    if status_filter:
        qs = qs.filter(status=status_filter)

    pending_count = BookingRequest.objects.filter(status='pending').count()
    context = {
        'requests': qs,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'request_statuses': [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')],
    }
    return render(request, 'allocations/booking_requests_admin.html', context)
