from django.contrib import admin
from .models import Sport, Competition, Event


class CompetitionInline(admin.TabularInline):
    model = Competition
    extra = 1
    show_change_link = True
    fields = ("competition_name", "competition_id", "competition_region", "market_count")


class EventInline(admin.TabularInline):
    model = Event
    extra = 1
    show_change_link = True
    fields = ("event_name", "event_id", "event_open_date", "is_disabled", "is_fancy")


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ("name", "event_type_id", "oid", "tree")
    search_fields = ("name", "event_type_id", "oid")
    list_filter = ("tree",)
    inlines = [CompetitionInline, EventInline]


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ("competition_name", "competition_id", "sport", "competition_region", "market_count")
    search_fields = ("competition_name", "competition_id")
    list_filter = ("competition_region", "sport")
    inlines = [EventInline]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "event_name",
        "event_id",
        "sport",
        "competition",
        "event_open_date",
        "is_disabled",
        "is_fancy",
    )
    search_fields = ("event_name", "event_id", "sport__name", "competition__competition_name")
    list_filter = ("sport", "competition", "is_disabled", "is_fancy")
    autocomplete_fields = ("sport", "competition")  # for easier selection when many exist
