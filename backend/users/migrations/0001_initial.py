# Generated by Django 4.2.7 on 2024-06-26 20:23

from django.db import migrations, models
import services.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('name', models.CharField(max_length=16, validators=[services.validators.validate_name], verbose_name='Имя')),
                ('device_id', models.UUIDField(editable=False, primary_key=True, serialize=False, verbose_name='ID устройства')),
            ],
        ),
    ]
