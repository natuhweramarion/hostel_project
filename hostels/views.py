from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Hostel, Block, Room
from .forms import HostelForm, BlockForm, RoomForm
from users.decorators import manager_required


def public_hostels(request):
    """Public hostel listing — no login required. Shows availability and pricing."""
    hostels = Hostel.objects.prefetch_related('blocks__rooms').order_by('name')
    hostel_data = []
    for hostel in hostels:
        total = hostel.total_capacity()
        available = hostel.available_spaces()

        # Build room-type breakdown with prices
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
                # Use the first non-null price found for this type
                if room_types[key]['price'] is None and room.price_per_semester:
                    room_types[key]['price'] = room.price_per_semester

        hostel_data.append({
            'hostel': hostel,
            'total_capacity': total,
            'available_spaces': available,
            'occupied': total - available,
            'occupancy_pct': round((total - available) / total * 100) if total > 0 else 0,
            'room_types': list(room_types.values()),
        })
    return render(request, 'hostels/public_hostels.html', {'hostel_data': hostel_data})


@login_required
@manager_required
def hostel_list(request):
    """List all hostels with block/room counts."""
    hostels = Hostel.objects.prefetch_related('blocks__rooms').all()
    return render(request, 'hostels/hostel_list.html', {'hostels': hostels})


@login_required
@manager_required
def hostel_create(request):
    """Create a new hostel."""
    if request.method == 'POST':
        form = HostelForm(request.POST)
        if form.is_valid():
            hostel = form.save()
            messages.success(request, f'Hostel "{hostel.name}" created successfully.')
            return redirect('hostel_detail', hostel_id=hostel.pk)
    else:
        form = HostelForm()
    return render(request, 'hostels/hostel_form.html', {'form': form, 'title': 'Add New Hostel'})


@login_required
@manager_required
def hostel_edit(request, hostel_id):
    """Edit an existing hostel."""
    hostel = get_object_or_404(Hostel, pk=hostel_id)
    if request.method == 'POST':
        form = HostelForm(request.POST, instance=hostel)
        if form.is_valid():
            form.save()
            messages.success(request, f'Hostel "{hostel.name}" updated.')
            return redirect('hostel_detail', hostel_id=hostel.pk)
    else:
        form = HostelForm(instance=hostel)
    return render(request, 'hostels/hostel_form.html', {'form': form, 'hostel': hostel, 'title': f'Edit {hostel.name}'})


@login_required
@manager_required
def hostel_detail(request, hostel_id):
    """View hostel with all blocks and rooms."""
    hostel = get_object_or_404(Hostel, pk=hostel_id)
    blocks = hostel.blocks.prefetch_related('rooms').all()
    return render(request, 'hostels/hostel_detail.html', {'hostel': hostel, 'blocks': blocks})


@login_required
@manager_required
def block_create(request, hostel_id):
    """Add a block to a hostel."""
    hostel = get_object_or_404(Hostel, pk=hostel_id)
    if request.method == 'POST':
        form = BlockForm(request.POST)
        if form.is_valid():
            block = form.save(commit=False)
            block.hostel = hostel
            block.save()
            messages.success(request, f'Block "{block.name}" added to {hostel.name}.')
            return redirect('hostel_detail', hostel_id=hostel.pk)
    else:
        form = BlockForm()
    return render(request, 'hostels/block_form.html', {'form': form, 'hostel': hostel})


@login_required
@manager_required
def room_create(request, hostel_id, block_id):
    """Add a room to a block."""
    hostel = get_object_or_404(Hostel, pk=hostel_id)
    block = get_object_or_404(Block, pk=block_id, hostel=hostel)
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.block = block
            room.save()
            messages.success(request, f'Room {room.room_number} added to Block {block.name}.')
            return redirect('hostel_detail', hostel_id=hostel.pk)
    else:
        form = RoomForm()
    return render(request, 'hostels/room_form.html', {'form': form, 'hostel': hostel, 'block': block})
