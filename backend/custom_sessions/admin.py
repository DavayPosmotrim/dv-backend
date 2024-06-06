from django.contrib import admin
from .models import CustomSession


@admin.register(CustomSession)
class CustomSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'status', 'get_formatted_date')
    readonly_fields = ('id', 'get_formatted_date')
    filter_horizontal = ('users', 'movies')

    def get_formatted_date(self, obj):
        return obj.get_formatted_date()
