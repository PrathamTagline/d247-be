from django.urls import path
from . import views

urlpatterns = [
    path('tree-record/', views.TreeRecordView.as_view(), name='tree_record_api'),
    path("odds/", views.OddsView.as_view(), name="odds"),
    path("highlight-home/", views.HighlightHomePrivateView.as_view(), name="highlight-home"),
    path("sports-data/", views.SportListView.as_view(), name="sport-list"),
    path("<int:event_type_id>/competitions/", views.CompetitionListAPIView.as_view(), name="competition-list"),
    path("<int:event_type_id>/<int:competition_id>/events/", views.EventListAPIView.as_view(), name="event-list-by-sport-competition"),
]
