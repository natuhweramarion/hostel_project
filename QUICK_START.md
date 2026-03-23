# 🚀 Quick Start Guide - Hostel Management System

## ✅ System Status: READY TO USE!

All migrations have been applied successfully and sample data has been created.

## 🌐 Access the System

**Development Server**: http://127.0.0.1:8000/

### 🔑 Login Credentials

#### Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Access**: Full admin dashboard, manage all features

#### Student Accounts (Password: `student123` for all)
- `john_doe` - John Doe (Computer Science, Level 300, Male)
- `jane_smith` - Jane Smith (Engineering, Level 200, Female)
- `mike_johnson` - Mike Johnson (Business, Level 400, Male)
- `sarah_williams` - Sarah Williams (Medicine, Level 100, Female)
- `david_brown` - David Brown (Law, Level 300, Male)

## 📊 Sample Data Created

### Hostels (3)
1. **Unity Hall** (Male) - North Campus
   - Block A (50 capacity) - 10 rooms
   - Block B (50 capacity) - 10 rooms

2. **Queens Hall** (Female) - South Campus
   - Block A (40 capacity) - 8 rooms
   - Block B (40 capacity) - 8 rooms

3. **International Hall** (Mixed) - East Campus
   - Block A (60 capacity) - 15 rooms

**Total**: 51 rooms, 204 bed spaces

## 🎯 Quick Actions

### As Admin (username: admin)

1. **Login**: http://127.0.0.1:8000/login/
2. **Admin Dashboard**: http://127.0.0.1:8000/dashboard/admin/
3. **Django Admin Panel**: http://127.0.0.1:8000/admin/

#### Create Allocations
- Go to: http://127.0.0.1:8000/allocations/create/
- Select a student and available room
- Set status and academic year
- Submit

#### Verify Payments
- Go to: http://127.0.0.1:8000/payments/
- Click "Verify" on pending payments
- Approve or reject

#### Generate Reports
- Go to: http://127.0.0.1:8000/reports/
- Choose report type
- Export to CSV if needed

### As Student (e.g., john_doe)

1. **Login**: http://127.0.0.1:8000/login/
2. **Student Dashboard**: http://127.0.0.1:8000/dashboard/student/
3. **Submit Payment**: http://127.0.0.1:8000/payments/create/

## 📱 Main URLs

| Page | URL | Access |
|------|-----|--------|
| Home | http://127.0.0.1:8000/ | Public |
| Login | http://127.0.0.1:8000/login/ | Public |
| Register | http://127.0.0.1:8000/register/ | Public |
| Student Dashboard | http://127.0.0.1:8000/dashboard/student/ | Students |
| Admin Dashboard | http://127.0.0.1:8000/dashboard/admin/ | Admins |
| Allocations | http://127.0.0.1:8000/allocations/ | Admins |
| Create Allocation | http://127.0.0.1:8000/allocations/create/ | Admins |
| Available Rooms | http://127.0.0.1:8000/allocations/available-rooms/ | Admins |
| Payments | http://127.0.0.1:8000/payments/ | Admins |
| Submit Payment | http://127.0.0.1:8000/payments/create/ | Students |
| Reports | http://127.0.0.1:8000/reports/ | Admins |
| Django Admin | http://127.0.0.1:8000/admin/ | Admins |

## 🧪 Testing Workflow

### 1. Test Student Registration
- Go to: http://127.0.0.1:8000/register/
- Create a new student account
- Login with new credentials

### 2. Test Allocation (as Admin)
- Login as admin
- Go to "Create Allocation"
- Allocate a student to a room
- Verify room shows as occupied

### 3. Test Payment (as Student)
- Login as student
- Go to "Submit Payment"
- Enter amount and reference number
- Submit

### 4. Test Payment Verification (as Admin)
- Login as admin
- Go to "Payments"
- Verify the pending payment

### 5. Test Reports (as Admin)
- Go to "Reports"
- View allocation report
- Export to CSV
- Check occupancy statistics

## 🛠️ Server Commands

```powershell
# Start server
python manage.py runserver

# Stop server
# Press Ctrl+C in the terminal

# Create superuser
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Open Django shell
python manage.py shell
```

## 📝 Database Info

- **Database**: SQLite (db.sqlite3)
- **Location**: `c:\Users\Marion\Desktop\HOSTEL MANAGEMENT SYSTEM\hostel_system\`
- **Size**: ~200KB
- **Tables**: 22 (including Django default tables)

## ✅ Migration Status

All migrations applied successfully:
- ✅ users (CustomUser model)
- ✅ hostels (Hostel, Block, Room models)
- ✅ allocations (Allocation model)
- ✅ payments (Payment model)
- ✅ Django core apps (admin, auth, sessions, etc.)

## 🎨 Features Available

### Admin Features
- ✅ View statistics dashboard
- ✅ Manage hostels, blocks, rooms
- ✅ Create/view allocations
- ✅ Verify payments
- ✅ Generate reports (CSV export)
- ✅ View available rooms
- ✅ Full Django admin access

### Student Features
- ✅ Register account
- ✅ View allocation details
- ✅ Submit payment records
- ✅ Check payment status
- ✅ View profile information

### System Features
- ✅ Automatic capacity validation
- ✅ Prevents over-allocation
- ✅ Room full status auto-update
- ✅ Role-based access control
- ✅ Responsive Bootstrap UI
- ✅ CSV report exports

## 🚨 Troubleshooting

### Server won't start
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port
python manage.py runserver 8080
```

### Can't login
- Check username/password
- Ensure user exists in database
- Try admin credentials: admin/admin123

### Templates not loading
- Check server is running
- Clear browser cache
- Check for errors in terminal

## 📞 Next Steps

1. ✅ Login as admin and explore dashboard
2. ✅ Create test allocations
3. ✅ Test payment workflow
4. ✅ Generate reports
5. ✅ Customize as needed

## 🎉 System is Ready!

Your Hostel Management System is fully configured and ready to use!

**Server Status**: Running on http://127.0.0.1:8000/
**Admin Access**: admin / admin123
**Sample Data**: Loaded ✓

Enjoy your new system! 🚀
