"""
Script to create sample data for testing the Hostel Management System
Run with: python manage.py shell < create_sample_data.py
"""

from users.models import CustomUser
from hostels.models import Hostel, Block, Room

print("Creating sample data...")

# Create sample hostels
hostel1 = Hostel.objects.create(
    name="Unity Hall",
    location="North Campus",
    gender="Male",
    description="Modern male hostel with excellent facilities"
)

hostel2 = Hostel.objects.create(
    name="Queens Hall",
    location="South Campus",
    gender="Female",
    description="Comfortable female hostel near the library"
)

hostel3 = Hostel.objects.create(
    name="International Hall",
    location="East Campus",
    gender="Mixed",
    description="Mixed gender hostel for international students"
)

print(f"✓ Created {Hostel.objects.count()} hostels")

# Create blocks for Unity Hall
block1 = Block.objects.create(hostel=hostel1, name="Block A", capacity=50)
block2 = Block.objects.create(hostel=hostel1, name="Block B", capacity=50)

# Create blocks for Queens Hall
block3 = Block.objects.create(hostel=hostel2, name="Block A", capacity=40)
block4 = Block.objects.create(hostel=hostel2, name="Block B", capacity=40)

# Create blocks for International Hall
block5 = Block.objects.create(hostel=hostel3, name="Block A", capacity=60)

print(f"✓ Created {Block.objects.count()} blocks")

# Create rooms for each block
room_count = 0

# Unity Hall - Block A (Rooms 101-110)
for i in range(1, 11):
    Room.objects.create(block=block1, room_number=f"10{i}", capacity=4)
    room_count += 1

# Unity Hall - Block B (Rooms 201-210)
for i in range(1, 11):
    Room.objects.create(block=block2, room_number=f"20{i}", capacity=4)
    room_count += 1

# Queens Hall - Block A (Rooms 101-108)
for i in range(1, 9):
    Room.objects.create(block=block3, room_number=f"10{i}", capacity=4)
    room_count += 1

# Queens Hall - Block B (Rooms 201-208)
for i in range(1, 9):
    Room.objects.create(block=block4, room_number=f"20{i}", capacity=4)
    room_count += 1

# International Hall - Block A (Rooms 101-115)
for i in range(1, 16):
    Room.objects.create(block=block5, room_number=f"10{i}", capacity=4)
    room_count += 1

print(f"✓ Created {room_count} rooms")

# Create sample students
students = [
    {"username": "john_doe", "first_name": "John", "last_name": "Doe", "email": "john@student.com", 
     "student_id": "STU001", "department": "Computer Science", "level": "300", "gender": "Male"},
    {"username": "jane_smith", "first_name": "Jane", "last_name": "Smith", "email": "jane@student.com",
     "student_id": "STU002", "department": "Engineering", "level": "200", "gender": "Female"},
    {"username": "mike_johnson", "first_name": "Mike", "last_name": "Johnson", "email": "mike@student.com",
     "student_id": "STU003", "department": "Business", "level": "400", "gender": "Male"},
    {"username": "sarah_williams", "first_name": "Sarah", "last_name": "Williams", "email": "sarah@student.com",
     "student_id": "STU004", "department": "Medicine", "level": "100", "gender": "Female"},
    {"username": "david_brown", "first_name": "David", "last_name": "Brown", "email": "david@student.com",
     "student_id": "STU005", "department": "Law", "level": "300", "gender": "Male"},
]

for student_data in students:
    user = CustomUser.objects.create_user(
        username=student_data["username"],
        email=student_data["email"],
        password="student123",
        first_name=student_data["first_name"],
        last_name=student_data["last_name"],
        is_student=True,
        student_id=student_data["student_id"],
        department=student_data["department"],
        level=student_data["level"],
        gender=student_data["gender"]
    )

print(f"✓ Created {len(students)} sample students")
print("\n" + "="*50)
print("Sample data created successfully!")
print("="*50)
print("\nLogin Credentials:")
print("-" * 50)
print("ADMIN:")
print("  Username: admin")
print("  Password: admin123")
print("\nSTUDENTS (all use password: student123):")
for s in students:
    print(f"  - {s['username']} ({s['first_name']} {s['last_name']})")
print("\n" + "="*50)
