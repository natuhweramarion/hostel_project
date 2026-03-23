# Hostel Management System - MVP

A comprehensive Django-based system for managing hostel allocations, payments, and generating reports.

## Features

### Core Functionality
- **User Management**: Student and admin/manager roles with custom user model
- **Hostel Management**: Manage hostels, blocks, and rooms
- **Room Allocation**: Manual allocation with automatic capacity validation
- **Payment Tracking**: Record and verify student payments
- **Reports**: Generate allocation, payment, and occupancy reports (CSV export)

### User Roles
- **Students**: View allocation, submit payments, check payment status
- **Managers/Admins**: Manage allocations, verify payments, generate reports

## Project Structure

```
hostel_system/
├── manage.py
├── hostel_system/          # Main project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/                  # User authentication & profiles
│   ├── models.py          # CustomUser model
│   ├── views.py           # Login, register, dashboards
│   ├── forms.py           # Registration form
│   ├── admin.py
│   └── urls.py
├── hostels/               # Hostel, Block, Room models
│   ├── models.py
│   └── admin.py
├── allocations/           # Room allocation logic
│   ├── models.py          # Allocation model with validation
│   ├── views.py
│   ├── forms.py
│   ├── admin.py
│   └── urls.py
├── payments/              # Payment tracking
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── admin.py
│   └── urls.py
├── reports/               # Report generation
│   ├── views.py           # CSV exports
│   └── urls.py
├── templates/             # Bootstrap 5 templates
│   ├── base.html
│   ├── navbar.html
│   ├── users/
│   ├── allocations/
│   ├── payments/
│   └── reports/
└── static/                # Static files (CSS, JS, images)
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- pip (Python package manager)

### 2. Install Dependencies
```bash
pip install django
```

### 3. Database Setup

**IMPORTANT**: Since we're using a custom user model, you need to delete the existing database and migrations:

```bash
# Delete the database
Remove-Item db.sqlite3

# Delete all migration files (except __init__.py)
Get-ChildItem -Path . -Include "0*.py" -Recurse | Remove-Item

# Create new migrations
python manage.py makemigrations users
python manage.py makemigrations hostels
python manage.py makemigrations allocations
python manage.py makemigrations payments

# Apply migrations
python manage.py migrate
```

### 4. Create Superuser
```bash
python manage.py createsuperuser
```
Follow the prompts to create an admin account. Make sure to set `is_manager=True` or `is_staff=True` for admin access.

### 5. Run the Development Server
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000/

## Usage Guide

### Admin Setup (First Time)

1. **Login to Django Admin**: http://127.0.0.1:8000/admin/
   - Use your superuser credentials

2. **Create Hostels**:
   - Go to Hostels → Add Hostel
   - Enter name, location, gender (Male/Female/Mixed)

3. **Create Blocks**:
   - Go to Blocks → Add Block
   - Select hostel, enter block name and capacity

4. **Create Rooms**:
   - Go to Rooms → Add Room
   - Select block, enter room number and bed capacity

### Student Registration

1. Visit: http://127.0.0.1:8000/register/
2. Fill in registration form
3. Login with credentials

### Admin Dashboard Features

- **View Statistics**: Total students, hostels, rooms, allocations
- **Create Allocations**: Assign students to available rooms
- **Verify Payments**: Approve or reject payment submissions
- **Generate Reports**: Export data to CSV

### Student Dashboard Features

- **View Allocation**: See assigned hostel, block, and room
- **Submit Payment**: Record payment with reference number
- **Check Payment Status**: View verification status

## Key Features Explained

### Automatic Capacity Validation
- Prevents over-allocation of rooms
- Automatically marks rooms as full when capacity is reached
- Validates that students don't have multiple active allocations

### Payment Verification Workflow
1. Student submits payment with reference number
2. Payment status: "Pending"
3. Admin reviews and verifies/rejects
4. Status updates to "Verified" or "Rejected"

### Report Generation
- **Allocation Report**: All student allocations with details
- **Payment Report**: All payments with totals and status
- **Occupancy Report**: Room occupancy statistics by hostel
- **CSV Export**: Download reports for external analysis

## URL Patterns

### Public URLs
- `/` - Home page
- `/register/` - Student registration
- `/login/` - Login page
- `/logout/` - Logout

### Student URLs
- `/dashboard/` - Main dashboard (redirects based on role)
- `/dashboard/student/` - Student dashboard
- `/payments/create/` - Submit payment

### Admin URLs
- `/dashboard/admin/` - Admin dashboard
- `/allocations/` - View all allocations
- `/allocations/create/` - Create new allocation
- `/allocations/available-rooms/` - View available rooms
- `/payments/` - View all payments
- `/payments/verify/<id>/` - Verify payment
- `/reports/` - Reports dashboard
- `/reports/allocations/` - Allocation report
- `/reports/payments/` - Payment report
- `/reports/occupancy/` - Occupancy report
- `/admin/` - Django admin panel

## Models Overview

### CustomUser
- Extends Django's AbstractUser
- Fields: `is_student`, `is_manager`, `department`, `level`, `phone_number`, `student_id`, `gender`, `date_of_birth`

### Hostel
- Fields: `name`, `location`, `gender`, `description`
- Methods: `total_capacity()`, `available_spaces()`

### Block
- Fields: `hostel` (FK), `name`, `capacity`
- Methods: `available_rooms()`

### Room
- Fields: `block` (FK), `room_number`, `capacity`, `is_full`
- Methods: `occupied_beds()`, `available_beds()`, `check_and_update_full_status()`

### Allocation
- Fields: `user` (FK), `room` (FK), `status`, `date_allocated`, `academic_year`
- Validation: Prevents over-allocation and duplicate active allocations
- Auto-updates room full status

### Payment
- Fields: `user` (FK), `amount`, `reference_number`, `status`, `payment_method`, `verified_by` (FK)
- Status choices: Pending, Verified, Rejected

## Technologies Used

- **Backend**: Django 5.x
- **Frontend**: Bootstrap 5.3, Bootstrap Icons
- **Database**: SQLite (default, can be changed to PostgreSQL/MySQL)
- **Authentication**: Django built-in authentication system

## Security Notes

- Change `SECRET_KEY` in `settings.py` for production
- Set `DEBUG = False` in production
- Configure `ALLOWED_HOSTS` for production deployment
- Use environment variables for sensitive data
- Implement HTTPS in production

## Future Enhancements

- Automatic allocation algorithm
- Email notifications
- Payment gateway integration
- Mobile responsive improvements
- Advanced filtering and search
- Student profile editing
- Room maintenance tracking
- Hostel rules and regulations module

## Support

For issues or questions, refer to Django documentation: https://docs.djangoproject.com/

## License

This is an MVP project for educational/demonstration purposes.
