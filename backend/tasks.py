from django.utils import timezone
from django_q.models import Schedule
from django_q.tasks import schedule
from movies.models import Collection, Genre
from services.kinopoisk.kinopoisk_service import (KinopoiskCollections,
                                                  KinopoiskGenres)


def update_genres_and_collections():
    kinopoisk_service_genres = KinopoiskGenres()
    genres_data = kinopoisk_service_genres.get_genres()
    if genres_data:
        for genre_data in genres_data:
            Genre.objects.update_or_create(name=genre_data['name'])

    kinopoisk_service_collections = KinopoiskCollections()
    collections_data = kinopoisk_service_collections.get_collections()
    if collections_data:
        for collection_data in collections_data['docs']:
            Collection.objects.update_or_create(
                slug=collection_data['slug'],
                defaults={
                    'name': collection_data['name'],
                    'cover': collection_data.get('cover')
                }
            )


# Задача должна выполняться каждые 2 недели
schedule(
    'backend.tasks.update_genres_and_collections',
    schedule_type=Schedule.WEEKLY,
    repeats=-1,
    next_run=timezone.now() + timezone.timedelta(weeks=2)
)
