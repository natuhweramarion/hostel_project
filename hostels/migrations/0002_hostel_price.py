from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hostels', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hostel',
            name='price_per_semester',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=12, null=True,
                help_text='Hostel fee per semester (UGX)'
            ),
        ),
    ]
