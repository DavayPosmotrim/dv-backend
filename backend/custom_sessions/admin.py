from django.contrib import admin

from .models import CustomSession


@admin.register(CustomSession)
class CustomSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "date",
        "status",
        "matched_movies_display",
        "get_formatted_date",
    )
    readonly_fields = ("id", "get_formatted_date")
    filter_horizontal = (
        "users",
        "movies",
        "matched_movies",
    )

    def get_formatted_date(self, obj):
        return obj.get_formatted_date()

    def matched_movies_display(self, obj):
        return ", ".join([movie.name for movie in obj.matched_movies.all()])

    matched_movies_display.short_description = "Избранные фильмы"
