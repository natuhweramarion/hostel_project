from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Q
import csv
from allocations.models import Allocation
from payments.models import Payment
from hostels.models import Hostel, Room
from users.decorators import manager_required


@login_required
@manager_required
def reports_dashboard(request):
    """Reports dashboard — managers only."""
    return render(request, 'reports/reports_dashboard.html')


@login_required
@manager_required
def allocation_report(request):
    """Generate allocation report — managers only. Supports academic year filter."""
    allocations = Allocation.objects.select_related('user', 'room__block__hostel').all()

    # Academic year filter
    academic_years = (
        Allocation.objects.exclude(academic_year__isnull=True)
        .exclude(academic_year='')
        .values_list('academic_year', flat=True)
        .order_by('academic_year')
        .distinct()
    )
    selected_year = request.GET.get('year', '').strip()
    if selected_year:
        allocations = allocations.filter(academic_year=selected_year)

    if request.GET.get('format') == 'csv':
        return export_allocations_csv(allocations)

    return render(request, 'reports/allocation_report.html', {
        'allocations': allocations,
        'academic_years': academic_years,
        'selected_year': selected_year,
    })


@login_required
@manager_required
def payment_report(request):
    """Generate payment report — managers only. Supports academic year filter."""
    payments = Payment.objects.select_related('user', 'verified_by').all()

    # Academic year filter
    academic_years = (
        Payment.objects.exclude(academic_year__isnull=True)
        .exclude(academic_year='')
        .values_list('academic_year', flat=True)
        .order_by('academic_year')
        .distinct()
    )
    selected_year = request.GET.get('year', '').strip()
    if selected_year:
        payments = payments.filter(academic_year=selected_year)

    # Use SQL aggregation instead of Python loops
    totals = payments.aggregate(
        total_amount=Sum('amount'),
        verified_amount=Sum('amount', filter=Q(status='verified')),
        pending_amount=Sum('amount', filter=Q(status='pending')),
    )

    if request.GET.get('format') == 'csv':
        return export_payments_csv(payments)

    context = {
        'payments': payments,
        'total_amount': totals['total_amount'] or 0,
        'verified_amount': totals['verified_amount'] or 0,
        'pending_amount': totals['pending_amount'] or 0,
        'academic_years': academic_years,
        'selected_year': selected_year,
    }
    return render(request, 'reports/payment_report.html', context)


@login_required
@manager_required
def hostel_occupancy_report(request):
    """Generate hostel occupancy report — managers only."""

    # Prefetch allocations so room.occupied_beds() uses cache, avoiding N+1 queries
    hostels = Hostel.objects.prefetch_related('blocks__rooms__allocations').all()

    hostel_data = []
    for hostel in hostels:
        total_capacity = sum(room.capacity for block in hostel.blocks.all() for room in block.rooms.all())
        # occupied_beds() uses self.allocations.all() which hits the prefetch cache
        occupied = sum(room.occupied_beds() for block in hostel.blocks.all() for room in block.rooms.all())
        available = total_capacity - occupied
        occupancy_rate = round(occupied / total_capacity * 100, 1) if total_capacity > 0 else 0

        hostel_data.append({
            'hostel': hostel,
            'total_capacity': total_capacity,
            'occupied': occupied,
            'available': available,
            'occupancy_rate': occupancy_rate,
        })

    return render(request, 'reports/hostel_occupancy_report.html', {'hostel_data': hostel_data})

def export_allocations_csv(allocations):
    """Export allocations to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="allocations_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Student ID', 'Hostel', 'Block', 'Room', 'Status', 'Date Allocated', 'Academic Year'])

    for allocation in allocations:
        writer.writerow([
            allocation.user.get_full_name(),
            allocation.user.student_id or allocation.user.username,
            allocation.room.block.hostel.name,
            allocation.room.block.name,
            allocation.room.room_number,
            allocation.status,
            allocation.date_allocated.strftime('%Y-%m-%d'),
            allocation.academic_year or 'N/A',
        ])

    return response

def export_payments_csv(payments):
    """Export payments to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payments_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Student ID', 'Amount', 'Reference Number', 'Payment Method', 'Status', 'Date Paid', 'Verified By'])

    for payment in payments:
        writer.writerow([
            payment.user.get_full_name(),
            payment.user.student_id or payment.user.username,
            payment.amount,
            payment.reference_number,
            payment.payment_method or 'N/A',
            payment.status,
            payment.date_paid.strftime('%Y-%m-%d'),
            payment.verified_by.username if payment.verified_by else 'N/A',
        ])

    return response
