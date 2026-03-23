from django.db import migrations


class Migration(migrations.Migration):
    """
    Removes the Car model that was accidentally added to the payments app.
    Car has no relation to hostel management domain.
    """

    dependencies = [
        ('payments', '0002_car'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Car',
        ),
    ]
