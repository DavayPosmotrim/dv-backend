# Generated by Django 4.2.7 on 2024-06-21 22:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_password'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='id',
        ),
        migrations.RemoveField(
            model_name='user',
            name='password',
        ),
        migrations.AlterField(
            model_name='user',
            name='device_id',
            field=models.UUIDField(editable=False, primary_key=True, serialize=False, verbose_name='ID устройства'),
        ),
    ]
