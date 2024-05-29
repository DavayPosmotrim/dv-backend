from django.contrib import admin
from .models import CustomSession, UserMovieVote


@admin.register(CustomSession)
class CustomSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'status', 'get_formatted_date')
    readonly_fields = ('id', 'get_formatted_date')
    filter_horizontal = ('users', 'movies')

    def get_formatted_date(self, obj):
        return obj.get_formatted_date()


@admin.register(UserMovieVote)
class UserMovieVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'session')
    list_filter = ('user', 'movie', 'session')
    search_fields = ('user__username', 'movie__title', 'session__id')
