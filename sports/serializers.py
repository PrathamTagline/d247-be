from rest_framework import serializers
from .models import Sport, Competition, Event


class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        exclude = ("id","created_at", "updated_at", "created_by", "updated_by")


class CompetitionOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        exclude = ("id","created_at", "updated_at", "created_by", "updated_by","sport")
        # fields = ["competition_id", "competition_name", "competition_region", "market_count"]

class CompetitionWithSportSerializer(serializers.Serializer):
    sport = SportSerializer()
    exclude = ("id","created_at", "updated_at", "created_by", "updated_by")
    competitions = CompetitionOnlySerializer(many=True)


class EventOnlySerializer(serializers.ModelSerializer):
    event_type_id = serializers.IntegerField(source="sport.event_type_id", read_only=True)
    competition_id = serializers.CharField(source="competition.competition_id", read_only=True)
    exclude = ("id","created_at", "updated_at", "created_by", "updated_by")
    class Meta:
        model = Event
        fields = [
            "event_id",
            "event_name",
            "event_country_code",
            "event_timezone",
            "event_open_date",
            "common_name",
            "is_disabled",
            "is_fancy",
            "provider_id",
            "provider_name",
            "tv_url",
            "score_iframe_url",
            "market_ids",
            "market_count",
            "selections",
            "event_type_id",   # from Sport
            "competition_id",  # from Competition
        ]
