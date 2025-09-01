import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from dotenv import load_dotenv

from backend.services.scaper_service import get_highlight_home_private, get_odds, get_tree_record
from backend.services.store_treedata_service import save_tree_data

from rest_framework.generics import ListAPIView
from .models import Sport, Competition, Event
from .serializers import EventOnlySerializer, SportSerializer,CompetitionOnlySerializer
from rest_framework.response import Response
from backend.permissions import HasTaglineSecretKey

load_dotenv()


class TreeRecordView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            data = get_tree_record(os.getenv("DECRYPTION_KEY"))
            if "error" in data:
                return Response(data, status=status.HTTP_401_UNAUTHORIZED)

            return Response({"message": "Tree data saved successfully","data": data},status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OddsView(APIView):
    """
    API to fetch odds using sport_id and event_id.
    """

    def get(self, request, *args, **kwargs):
        try:
            sport_id = request.query_params.get("sport_id")
            event_id = request.query_params.get("event_id")

            if not sport_id or not event_id:
                return Response(
                    {"error": "sport_id and event_id are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            password = os.getenv("DECRYPTION_KEY")
            if not password:
                return Response(
                    {"error": "DECRYPTION_KEY not configured"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            data = get_odds(int(sport_id), int(event_id), password)
            return Response({"odds": data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HighlightHomePrivateView(APIView):
    """
    API to fetch highlight home private data using etid.
    """
    def get(self, request, *args, **kwargs):
        try:
            etid = request.query_params.get("etid")

            if not etid:
                return Response(
                    {"error": "etid is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            password = os.getenv("DECRYPTION_KEY")
            if not password:
                return Response(
                    {"error": "DECRYPTION_KEY not configured"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            data = get_highlight_home_private(int(etid), password)
            return Response({"highlight": data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SportListView(ListAPIView):
    queryset = Sport.objects.all()
    serializer_class = SportSerializer
    permission_classes = [HasTaglineSecretKey]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": True,
            "message": "Sports fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class CompetitionListAPIView(APIView):
    permission_classes = [HasTaglineSecretKey]

    def get(self, request, event_type_id=None):
        try:
            # filter Sport by event_type_id instead of id
            sport = Sport.objects.get(event_type_id=event_type_id)
            competitions = Competition.objects.filter(sport=sport)

            data = {
                "sport": SportSerializer(sport).data,
                "competitions": CompetitionOnlySerializer(competitions, many=True).data
            }

            return Response({
                "status": True,
                "message": "Competition data fetched successfully",
                **data
            }, status=status.HTTP_200_OK)
        except Sport.DoesNotExist:
            return Response({
                "status": False,
                "message": "Sport not found"
            }, status=status.HTTP_404_NOT_FOUND)


class EventListAPIView(APIView):
    permission_classes = [HasTaglineSecretKey]
    def get(self, request, event_type_id=None, competition_id=None):
        try:
            # Find sport by event_type_id
            sport = Sport.objects.get(event_type_id=event_type_id)

            # Find competition by competition_id + sport
            competition = Competition.objects.get(competition_id=competition_id, sport=sport)

            # Fetch events
            events = Event.objects.filter(sport=sport, competition=competition)

            if not events.exists():
                return Response({
                    "status": False,
                    "message": "No events found"
                }, status=status.HTTP_404_NOT_FOUND)

            return Response({
                "status": True,
                "message": "Events fetched successfully",
                "sport": SportSerializer(sport).data,
                "competition": CompetitionOnlySerializer(competition).data,
                "events": EventOnlySerializer(events, many=True).data
            }, status=status.HTTP_200_OK)

        except Sport.DoesNotExist:
            return Response({
                "status": False,
                "message": "Sport not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Competition.DoesNotExist:
            return Response({
                "status": False,
                "message": "Competition not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
