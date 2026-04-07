from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Count, Q, F


class Hostel(models.Model):
    """Hostel/Hall of residence"""
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Mixed', 'Mixed'),
    ]

    name = models.CharField(max_length=200, unique=True)
    location = models.CharField(max_length=300)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='hostel_images/', blank=True, null=True, help_text="Hostel banner image")
    price_per_semester = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Hostel fee per semester (UGX)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.gender})"

    def total_capacity(self):
        """Calculate total capacity across all rooms (sum of room bed counts)"""
        return sum(room.capacity for block in self.blocks.all() for room in block.rooms.all())

    def available_spaces(self):
        """Calculate available spaces"""
        total = sum(room.capacity for block in self.blocks.all() for room in block.rooms.all())
        occupied = sum(room.occupied_beds() for block in self.blocks.all() for room in block.rooms.all())
        return total - occupied

    class Meta:
        ordering = ['name']


class Block(models.Model):
    """Block/Wing within a hostel"""
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='blocks')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hostel.name} - {self.name}"

    @property
    def capacity(self):
        """Total capacity = sum of all room capacities in this block"""
        return sum(room.capacity for room in self.rooms.all())

    def available_rooms(self):
        """Get rooms that are not full (active allocations < capacity)"""
        return self.rooms.annotate(
            active_count=Count('allocations', filter=Q(allocations__status='active'))
        ).filter(active_count__lt=F('capacity'))

    class Meta:
        ordering = ['hostel', 'name']
        unique_together = ['hostel', 'name']


class Room(models.Model):
    """Individual room within a block"""
    ROOM_TYPE_CHOICES = [
        ('Single', 'Single'),
        ('Double', 'Double'),
        ('Self-Contained', 'Self-Contained'),
        ('Shared', 'Shared'),
    ]

    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Number of beds in the room")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, blank=True, null=True, help_text="Type of room")
    price_per_semester = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Room fee per semester (UGX)"
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.block.hostel.name} - {self.block.name} - Room {self.room_number}"

    def occupied_beds(self):
        """Count currently occupied beds"""
        from allocations.models import Allocation
        return Allocation.objects.filter(room=self, status='active').count()

    def available_beds(self):
        """Calculate available beds"""
        return self.capacity - self.occupied_beds()

    @property
    def is_full(self):
        """Dynamically computed — room is full when active allocations >= capacity"""
        return self.occupied_beds() >= self.capacity

    class Meta:
        ordering = ['block', 'room_number']
        unique_together = ['block', 'room_number']