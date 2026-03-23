from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('allocations', '0002_allocation_unique_active_allocation_per_student'),
        ('hostels', '0005_hostel_image_url'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('academic_year', models.CharField(help_text='e.g. 2024/2025', max_length=20)),
                ('message', models.TextField(blank=True, null=True, help_text='Any additional notes for the hostel office')),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')],
                    default='pending',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('admin_notes', models.TextField(blank=True, null=True)),
                ('preferred_hostel', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='booking_requests',
                    to='hostels.hostel',
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_booking_requests',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='booking_requests',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Booking Request',
                'verbose_name_plural': 'Booking Requests',
                'ordering': ['-created_at'],
            },
        ),
    ]
