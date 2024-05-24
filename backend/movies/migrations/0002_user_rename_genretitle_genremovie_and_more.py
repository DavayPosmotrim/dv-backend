# Generated by Django 4.2.7 on 2024-05-03 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(verbose_name='Имя')),
                ('device_id', models.CharField(verbose_name='ID устройства')),
            ],
        ),
        migrations.RenameModel(
            old_name='GenreTitle',
            new_name='GenreMovie',
        ),
        migrations.AlterModelOptions(
            name='genremovie',
            options={'default_related_name': 'genresmovies'},
        ),
        migrations.AlterField(
            model_name='movie',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False, verbose_name='Уникальный код фильма'),
        ),
        migrations.DeleteModel(
            name='Favorite',
        ),
    ]