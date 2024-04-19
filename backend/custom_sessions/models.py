from django.db import models


class CustomSession(models.Model):
    """CustomSession model."""
    name = models.CharField(
        max_length=125,
    )

    class Meta:
        verbose_name = "CustomSession"
        verbose_name_plural = "CustomSessions"

    def __str__(self):
        return self.name
