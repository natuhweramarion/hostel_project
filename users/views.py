from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum, Q
from .forms import StudentRegistrationForm, ProfileEditForm
from .decorators import manager_required, student_required


def home(request):
    """Home page / landing."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'users/home.html')


def register(request):
    """Student self-registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_student = True
            user.save()
            messages.success(request, 'Registration successful! You can now sign in.')
            return redirect('login')
    else:
        form = StudentRegistrationForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """Login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logout — POST only to prevent CSRF logout attacks."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'You have been signed out.')
        return redirect('home')
    return redirect('dashboard')


@login_required
def dashboard(request):
    """Dispatcher: redirects to role-appropriate dashboard."""
    if request.user.is_manager or request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('student_dashboard')


@login_required
@student_required
def student_dashboard(request):
    """Student dashboard — students only."""
    from allocations.models import Allocation, BookingRequest
    from payments.models import Payment

    allocation = Allocation.objects.filter(
        user=request.user, status='active'
    ).select_related('room__block__hostel').first()

    booking_request = BookingRequest.objects.filter(
        student=request.user, status__in=['pending', 'approved']
    ).select_related('preferred_hostel').first()

    all_payments = Payment.objects.filter(user=request.user).order_by('-date_paid')
    recent_payments = all_payments[:5]
    payment_summary = all_payments.aggregate(
        total=Sum('amount'),
        verified=Sum('amount', filter=Q(status='verified')),
    )
    all_allocations = Allocation.objects.filter(user=request.user).select_related('room__block__hostel').order_by('-date_allocated')

    # Pending items that need the student's attention
    pending_payments = all_payments.filter(status='pending')
    rejected_payments = all_payments.filter(status='rejected')
    all_booking_requests = BookingRequest.objects.filter(
        student=request.user
    ).select_related('preferred_hostel').order_by('-created_at')

    # Unread notifications (latest 8 for dashboard widget)
    from users.models import Notification
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:8]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        'allocation': allocation,
        'booking_request': booking_request,
        'payments': recent_payments,
        'all_allocations': all_allocations,
        'payment_total': payment_summary['total'] or 0,
        'payment_verified': payment_summary['verified'] or 0,
        'pending_payments': pending_payments,
        'rejected_payments': rejected_payments,
        'all_booking_requests': all_booking_requests,
        'notifications': notifications,
        'unread_notif_count': unread_count,
    }
    return render(request, 'users/student_dashboard.html', context)


@login_required
@manager_required
def admin_dashboard(request):
    """Admin/Manager dashboard — managers only."""
    from hostels.models import Hostel, Room
    from allocations.models import Allocation
    from payments.models import Payment
    from django.contrib.auth import get_user_model

    User = get_user_model()

    total_students = User.objects.filter(is_student=True).count()
    total_hostels = Hostel.objects.count()
    total_rooms = Room.objects.count()
    active_allocations = Allocation.objects.filter(status='active').count()
    from allocations.models import BookingRequest
    pending_booking_requests = BookingRequest.objects.filter(status='pending').count()
    pending_payments = Payment.objects.filter(status='pending').count()
    verified_payments = Payment.objects.filter(status='verified').count()
    rejected_payments = Payment.objects.filter(status='rejected').count()

    all_rooms = Room.objects.all()
    total_beds = sum(r.capacity for r in all_rooms)
    available_beds = max(total_beds - active_allocations, 0)

    totals = Payment.objects.aggregate(
        total=Sum('amount'),
        verified=Sum('amount', filter=Q(status='verified')),
    )

    recent_allocations = Allocation.objects.select_related(
        'user', 'room__block__hostel'
    ).order_by('-date_allocated')[:8]
    recent_payments = Payment.objects.select_related('user').order_by('-date_paid')[:8]

    context = {
        'total_students': total_students,
        'total_hostels': total_hostels,
        'total_rooms': total_rooms,
        'active_allocations': active_allocations,
        'pending_payments': pending_payments,
        'available_beds': available_beds,
        'recent_allocations': recent_allocations,
        'recent_payments': recent_payments,
        # Chart data (passed to JS)
        'chart_occupied': active_allocations,
        'chart_available': available_beds,
        'chart_pay_verified': verified_payments,
        'chart_pay_pending': pending_payments,
        'chart_pay_rejected': rejected_payments,
        'total_revenue': totals['verified'] or 0,
    }
    return render(request, 'users/admin_dashboard.html', context)


def about_us(request):
    """Public About Us page."""
    return render(request, 'users/about.html')


def contact_us(request):
    """Public Contact Us page."""
    return render(request, 'users/contact.html')


@login_required
def profile(request):
    """Student/User profile — view and edit."""
    from allocations.models import Allocation
    from payments.models import Payment

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)

    allocation = Allocation.objects.filter(
        user=request.user, status='active'
    ).select_related('room__block__hostel').first()
    allocation_history = Allocation.objects.filter(
        user=request.user
    ).select_related('room__block__hostel').order_by('-date_allocated')

    context = {
        'form': form,
        'allocation': allocation,
        'allocation_history': allocation_history,
    }
    return render(request, 'users/profile.html', context)


@login_required
def notifications_view(request):
    """Full notifications list — marks all as read on visit."""
    from users.models import Notification
    # Mark all unread as read when the page is opened
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'users/notifications.html', {'notifications': notifications})


@login_required
def mark_notification_read(request, notif_id):
    """Mark a single notification as read and redirect to its link."""
    from users.models import Notification
    notif = get_object_or_404(Notification, pk=notif_id, user=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('notifications')
