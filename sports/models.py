import uuid
from django.db import models
from backend.models import BaseModel


class Sport(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type_id = models.IntegerField(default=0, null=True, blank=True)
    name = models.CharField(max_length=255, default="", blank=True)
    oid = models.IntegerField(default=0, null=True, blank=True)
    tree = models.CharField(max_length=255, default="", blank=True)

    class Meta:
        db_table = "sport"

    def __str__(self):
        return self.name or str(self.id)


class Competition(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sport = models.ForeignKey(
        'Sport',
        on_delete=models.CASCADE,
        null=True,  # allow null for old rows
        blank=True,  # allow blank in forms/admin
        related_name="competitions",
    )
    competition_id = models.CharField(max_length=255, default="", blank=True, db_index=True)
    competition_name = models.CharField(max_length=255, default="", blank=True, db_index=True)
    competition_region = models.CharField(max_length=255, default="", blank=True)
    market_count = models.IntegerField(default=0)

    class Meta:
        db_table = "competition"

    def __str__(self):
        return self.competition_name or str(self.id)


class Event(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Foreign Keys
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name="events")
    competition = models.ForeignKey(
        Competition, on_delete=models.CASCADE, related_name="events", null=True, blank=True
    )

    # Event Info
    event_id = models.CharField(max_length=255, default="", blank=True, db_index=True)
    event_name = models.CharField(max_length=255, default="", blank=True, db_index=True)
    event_country_code = models.CharField(max_length=10, default="", blank=True)
    event_timezone = models.CharField(max_length=50, default="", blank=True)
    event_open_date = models.DateTimeField(null=True, blank=True)

    common_name = models.CharField(max_length=255, default="", blank=True)
    is_disabled = models.BooleanField(default=False)
    is_fancy = models.BooleanField(default=True)

    # Provider Info
    provider_id = models.CharField(max_length=255, default="", blank=True)
    provider_name = models.CharField(max_length=255, default="", blank=True)

    tv_url = models.URLField(max_length=500, default="", blank=True)
    score_iframe_url = models.URLField(max_length=500, default="", blank=True)

    # Market Info (JSON instead of sub-schema)
    market_ids = models.JSONField(default=list, blank=True)
    market_count = models.IntegerField(default=0)

    # Selections (JSON instead of sub-schema)
    selections = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "event"

    def __str__(self):
        return self.event_name or str(self.id)
