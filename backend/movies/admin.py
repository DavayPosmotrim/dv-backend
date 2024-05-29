from django.contrib import admin
from .models import Genre, Movie


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    """Интерфейс модели жанра."""
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    """Интерфейс модели фильма."""
    list_display = ('id', 'name', 'get_genres')
    search_fields = ('name',)
    list_filter = ('genre',)

    def get_genres(self, obj):
        """Возвращает жанры к фильму в виде строки ."""
        return ', '.join([genre.name for genre in obj.genre.all()])
    get_genres.short_description = 'Genres'
