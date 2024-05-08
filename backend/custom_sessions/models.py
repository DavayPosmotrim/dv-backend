import base64
import os
import time

from django.db import models

from movies.models import Movie
from services.constants import STATUS_CHOICES
from services.utils import format_date
from users.models import User


# вариант быстрого генератора id с проверкой уникальности
# и наличием букв в идентификаторе
def generate_session_id():
    # Получает текущее время в миллисекундах
    current_time = int(time.time() * 1000)
    # генерирует случайные байты
    random_bytes = os.urandom(1)
    id_bytes = current_time.to_bytes(4, byteorder='big') + random_bytes
    id_str = base64.b64encode(
        id_bytes,
        altchars=b'-_').decode('ascii')
    if len(id_str) == 8 and not CustomSession.objects.filter(
        id=id_str
    ).exists():
        return id_str
    else:
        return generate_session_id()


class CustomSession(models.Model):
    """Модель комнаты/сеанса. """

    # id = models.CharField(   # вариант для использ. со служебной функцией
    #     primary_key=True,
    #     max_length=8,
    #     default=generate_session_id,
    #     editable=False
    # )

    # уникальность поля id обеспечена типом поля
    # тогда импорт служебной функции не нужен
    id = models.AutoField(primary_key=True)
    users = models.ManyToManyField(
        User,
        verbose_name='Пользователь',
    )
    movies = models.ManyToManyField(
        Movie,
        verbose_name='Фильм',
    )
    date = models.DateField(
        verbose_name='Дата',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
    )

    class Meta:
        ordering = ("date",)
        verbose_name = "Сеанс"
        verbose_name_plural = "Сеансы"

    def save(self, *args, **kwargs):
        # присваивает полю id восьмизначный строковый идентификатор
        # если принципиально наличие букв, то этот способ не подходит
        if not self.id:
            self.id = f"{self.pk:08d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.id

    def get_formatted_date(self):
        if self.date:
            return format_date(self.date)
        else:
            return 'Дата не установлена'
