# Hostel Management System - Automated Setup Script
# Run this script in PowerShell to set up the project

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Hostel Management System - Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Delete old database
Write-Host "[1/6] Deleting old database..." -ForegroundColor Yellow
if (Test-Path "db.sqlite3") {
    Remove-Item "db.sqlite3" -Force
    Write-Host "✓ Database deleted" -ForegroundColor Green
} else {
    Write-Host "✓ No existing database found" -ForegroundColor Green
}
Write-Host ""

# Step 2: Delete old migrations
Write-Host "[2/6] Cleaning old migrations..." -ForegroundColor Yellow
$apps = @("users", "hostels", "allocations", "payments", "reports")
foreach ($app in $apps) {
    $migrationPath = "$app\migrations"
    if (Test-Path $migrationPath) {
        Get-ChildItem -Path $migrationPath -Filter "0*.py" -ErrorAction SilentlyContinue | Remove-Item -Force
    }
}
Write-Host "✓ Old migrations cleaned" -ForegroundColor Green
Write-Host ""

# Step 3: Create new migrations
Write-Host "[3/6] Creating new migrations..." -ForegroundColor Yellow
python manage.py makemigrations users
python manage.py makemigrations hostels
python manage.py makemigrations allocations
python manage.py makemigrations payments
python manage.py makemigrations
Write-Host "✓ Migrations created" -ForegroundColor Green
Write-Host ""

# Step 4: Apply migrations
Write-Host "[4/6] Applying migrations to database..." -ForegroundColor Yellow
python manage.py migrate
Write-Host "✓ Migrations applied" -ForegroundColor Green
Write-Host ""

# Step 5: Create superuser
Write-Host "[5/6] Creating superuser account..." -ForegroundColor Yellow
Write-Host "Please enter superuser details:" -ForegroundColor Cyan
python manage.py createsuperuser
Write-Host ""

# Step 6: Set manager role
Write-Host "[6/6] Setting manager role..." -ForegroundColor Yellow
Write-Host "Enter the username you just created:" -ForegroundColor Cyan
$username = Read-Host
python manage.py shell -c "from users.models import CustomUser; user = CustomUser.objects.get(username='$username'); user.is_manager = True; user.save(); print('✓ Manager role set for $username')"
Write-Host ""

# Setup complete
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Run: python manage.py runserver" -ForegroundColor White
Write-Host "2. Visit: http://127.0.0.1:8000/" -ForegroundColor White
Write-Host "3. Login to admin: http://127.0.0.1:8000/admin/" -ForegroundColor White
Write-Host "4. Create hostels, blocks, and rooms" -ForegroundColor White
Write-Host ""
Write-Host "Would you like to start the development server now? (Y/N)" -ForegroundColor Yellow
$response = Read-Host
if ($response -eq "Y" -or $response -eq "y") {
    Write-Host ""
    Write-Host "Starting development server..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    python manage.py runserver
}
