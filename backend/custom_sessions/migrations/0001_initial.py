# Generated by Django 4.2.7 on 2024-04-30 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CustomSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=125)),
            ],
            options={
                'verbose_name': 'CustomSession',
                'verbose_name_plural': 'CustomSessions',
            },
        ),
    ]