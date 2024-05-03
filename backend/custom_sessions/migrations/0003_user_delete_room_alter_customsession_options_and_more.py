# Generated by Django 4.2.7 on 2024-05-03 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0002_user_rename_genretitle_genremovie_and_more'),
        ('custom_sessions', '0002_room'),
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
        migrations.DeleteModel(
            name='Room',
        ),
        migrations.AlterModelOptions(
            name='customsession',
            options={'ordering': ('date',), 'verbose_name': 'Сеанс', 'verbose_name_plural': 'Сеансы'},
        ),
        migrations.RemoveField(
            model_name='customsession',
            name='name',
        ),
        migrations.AddField(
            model_name='customsession',
            name='date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата'),
        ),
        migrations.AddField(
            model_name='customsession',
            name='movies',
            field=models.ManyToManyField(to='movies.movie', verbose_name='Фильм'),
        ),
        migrations.AddField(
            model_name='customsession',
            name='status',
            field=models.CharField(choices=[('waiting', 'Ожидание'), ('voting', 'Голосование'), ('closed', 'Закрыто')], default='draft', max_length=10),
        ),
        migrations.AlterField(
            model_name='customsession',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AddField(
            model_name='customsession',
            name='users',
            field=models.ManyToManyField(to='custom_sessions.user', verbose_name='Пользователь'),
        ),
    ]