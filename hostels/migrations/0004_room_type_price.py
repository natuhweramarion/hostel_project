from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hostels', '0003_merge_20260307_1848'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='room_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('Single', 'Single'),
                    ('Double', 'Double'),
                    ('Self-Contained', 'Self-Contained'),
                    ('Shared', 'Shared'),
                ],
                max_length=20,
                null=True,
                help_text='Type of room',
            ),
        ),
        migrations.AddField(
            model_name='room',
            name='price_per_semester',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Room fee per semester (UGX)',
                max_digits=12,
                null=True,
            ),
        ),
    ]
