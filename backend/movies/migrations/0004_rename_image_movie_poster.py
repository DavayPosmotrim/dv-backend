# Generated by Django 4.2.7 on 2024-06-21 17:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0003_delete_genremovie'),
    ]

    operations = [
        migrations.RenameField(
            model_name='movie',
            old_name='image',
            new_name='poster',
        ),
    ]
