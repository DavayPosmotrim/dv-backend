# Generated by Django 4.2.7 on 2024-07-18 16:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0002_remove_movie_persons_movie_actors_movie_directors_and_more"),
        ("users", "0001_initial"),
        ("custom_sessions", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomSessionMovieVote",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "movie_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="votes",
                        to="movies.movie",
                    ),
                ),
                (
                    "session_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="votes",
                        to="custom_sessions.customsession",
                    ),
                ),
                (
                    "user_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="votes",
                        to="users.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "CustomSessionMovieVote",
                "verbose_name_plural": "CustomSessionMovieVotes",
            },
        ),
        migrations.AddConstraint(
            model_name="customsessionmovievote",
            constraint=models.UniqueConstraint(
                fields=("session_id", "user_id", "movie_id"), name="unique_vote"
            ),
        ),
    ]
