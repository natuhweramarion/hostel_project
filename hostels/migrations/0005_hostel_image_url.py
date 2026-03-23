from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hostels', '0004_room_type_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='hostel',
            name='image_url',
            field=models.URLField(
                blank=True,
                max_length=500,
                null=True,
                help_text='URL of the hostel banner image',
            ),
        ),
    ]
