import random
import string

from django.db import models
from services.constants import STATUS_CHOICES
from services.utils import format_date
from users.models import User


def generate_id():
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))


class CustomSession(models.Model):
    """Модель комнаты/сеанса."""

    id = models.CharField(
        primary_key=True,
        default=generate_id,
        max_length=8,
        editable=False,
        verbose_name="Уникальный идентификатор сессии",
    )
    date = models.DateField(
        verbose_name="Дата",
        auto_now_add=True,
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="draft",
    )

    class Meta:

        verbose_name = "Сеанс"
        verbose_name_plural = "Сеансы"

    def __str__(self):
        return f"CustomSession {self.id or 'Unknown'}"

    def get_formatted_date(self):
        if self.date:
            return format_date(self.date)
        else:
            return "Дата не установлена"


class CustomSessionUser(models.Model):
    """Model describe users connected to the session."""

    session = models.ForeignKey(
        CustomSession, related_name="users", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name="sessions",
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "CustomSessionUser"
        verbose_name_plural = "CustomSessionUsers"
