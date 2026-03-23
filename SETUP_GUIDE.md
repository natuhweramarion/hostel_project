# Quick Setup Guide

## Step-by-Step Setup Instructions

### 1. Delete Existing Database (IMPORTANT!)
Since we're using a custom user model, you must delete the existing database:

```powershell
Remove-Item db.sqlite3 -ErrorAction SilentlyContinue
```

### 2. Delete Old Migration Files
```powershell
# Delete migration files from all apps
Get-ChildItem -Path users\migrations -Filter "0*.py" | Remove-Item
Get-ChildItem -Path hostels\migrations -Filter "0*.py" | Remove-Item
Get-ChildItem -Path allocations\migrations -Filter "0*.py" | Remove-Item
Get-ChildItem -Path payments\migrations -Filter "0*.py" | Remove-Item
Get-ChildItem -Path reports\migrations -Filter "0*.py" | Remove-Item
```

### 3. Create Fresh Migrations
```powershell
python manage.py makemigrations users
python manage.py makemigrations hostels
python manage.py makemigrations allocations
python manage.py makemigrations payments
python manage.py makemigrations
```

### 4. Apply Migrations
```powershell
python manage.py migrate
```

### 5. Create Superuser (Admin Account)
```powershell
python manage.py createsuperuser
```

**Important**: When creating the superuser:
- Enter username, email, and password
- After creation, you'll need to set `is_manager=True` via Django admin or shell

### 6. Set Manager Role (Option A - Django Shell)
```powershell
python manage.py shell
```

Then in the Python shell:
```python
from users.models import CustomUser
user = CustomUser.objects.get(username='your_username')
user.is_manager = True
user.save()
exit()
```

### 6. Set Manager Role (Option B - After First Login)
1. Run server: `python manage.py runserver`
2. Login to admin: http://127.0.0.1:8000/admin/
3. Go to Users → Your user
4. Check "is_manager" checkbox
5. Save

### 7. Run the Server
```powershell
python manage.py runserver
```

Visit: http://127.0.0.1:8000/

## Initial Data Setup

### Create Sample Data via Django Admin

1. **Login to Admin Panel**: http://127.0.0.1:8000/admin/

2. **Create Hostels**:
   - Click "Hostels" → "Add Hostel"
   - Example: Name="Hall A", Location="North Campus", Gender="Male"

3. **Create Blocks**:
   - Click "Blocks" → "Add Block"
   - Example: Hostel="Hall A", Name="Block 1", Capacity=50

4. **Create Rooms**:
   - Click "Rooms" → "Add Room"
   - Example: Block="Block 1", Room Number="101", Capacity=4

5. **Create Test Student**:
   - Click "Users" → "Add User"
   - Fill in details and check "is_student" checkbox

## Testing the System

### Test as Student:
1. Go to: http://127.0.0.1:8000/register/
2. Register a new student account
3. Login and view student dashboard
4. Submit a test payment

### Test as Admin:
1. Login with your superuser account
2. Go to admin dashboard
3. Create an allocation for a student
4. Verify student payments
5. Generate reports

## Common Commands

```powershell
# Run development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Open Django shell
python manage.py shell

# Collect static files (for production)
python manage.py collectstatic
```

## Troubleshooting

### Issue: "No such table: users_customuser"
**Solution**: You forgot to run migrations. Run:
```powershell
python manage.py migrate
```

### Issue: "Table already exists"
**Solution**: Delete db.sqlite3 and all migration files, then recreate:
```powershell
Remove-Item db.sqlite3
Get-ChildItem -Path . -Include "0*.py" -Recurse | Remove-Item
python manage.py makemigrations
python manage.py migrate
```

### Issue: Can't access admin dashboard
**Solution**: Make sure your user has `is_manager=True` or `is_staff=True`:
```python
python manage.py shell
from users.models import CustomUser
user = CustomUser.objects.get(username='your_username')
user.is_manager = True
user.is_staff = True
user.save()
```

### Issue: Templates not found
**Solution**: Check that `TEMPLATES['DIRS']` in settings.py includes `BASE_DIR / 'templates'`

## Quick Test Data Script

You can create test data using Django shell:

```python
python manage.py shell
```

```python
from users.models import CustomUser
from hostels.models import Hostel, Block, Room

# Create a hostel
hostel = Hostel.objects.create(
    name="Test Hall",
    location="Main Campus",
    gender="Mixed",
    description="Test hostel for development"
)

# Create a block
block = Block.objects.create(
    hostel=hostel,
    name="Block A",
    capacity=100
)

# Create rooms
for i in range(1, 11):
    Room.objects.create(
        block=block,
        room_number=f"10{i}",
        capacity=4
    )

print("Test data created successfully!")
```

## Next Steps

1. ✅ Complete setup steps above
2. ✅ Create sample hostels, blocks, and rooms
3. ✅ Register test students
4. ✅ Create test allocations
5. ✅ Test payment workflow
6. ✅ Generate reports

## Production Deployment Notes

Before deploying to production:

1. Change `SECRET_KEY` in settings.py
2. Set `DEBUG = False`
3. Configure `ALLOWED_HOSTS`
4. Use PostgreSQL or MySQL instead of SQLite
5. Set up proper static file serving
6. Configure email backend for notifications
7. Enable HTTPS
8. Set up backup system

Good luck with your Hostel Management System! 🎉
