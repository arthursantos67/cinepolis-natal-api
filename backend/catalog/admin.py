from django.contrib import admin

from catalog.models import Genre, Movie, Room, Session


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "duration_minutes", "release_date", "created_at")
    search_fields = ("title",)
    filter_horizontal = ("genres",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity", "created_at")
    search_fields = ("name",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("movie", "room", "start_time", "end_time", "created_at")
    list_filter = ("room", "start_time")
    search_fields = ("movie__title", "room__name")