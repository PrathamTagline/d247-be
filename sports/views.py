import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from dotenv import load_dotenv

from backend.services import redis_service
from backend.services.scaper_service import get_highlight_home_private, get_odds, get_tree_record

from rest_framework.generics import ListAPIView
from .models import Sport, Competition, Event
from .serializers import EventOnlySerializer, SportSerializer,CompetitionOnlySerializer
from rest_framework.response import Response
from backend.permissions import HasTaglineSecretKey
from typing import List, Dict, Any, Optional
from backend.services.redis_service import redis_service
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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging
from typing import Dict, Any, List, Optional
from backend.services.redis_service import redis_service

logger = logging.getLogger(__name__)

class GetOddsByEventAndMarketView(APIView):
    """
    API to get odds data by event_id
    
    GET  /api/odds/{event_id}/                -> All markets for the event
    POST /api/odds/{event_id}/Bookmaker/      -> Filtered by market_ids (if provided in body)
    """
    permission_classes = [HasTaglineSecretKey]

    # ----------------- GET -----------------
    def get(self, request, event_id=None):
        validation_error = self._validate_url_params(event_id)
        if validation_error:
            return validation_error

        odds_data = self._get_event_odds_data(event_id)
        if not odds_data:
            return Response({
                'success': False,
                'error': f'No odds data found for event {event_id}',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        return Response(odds_data, status=status.HTTP_200_OK)

    # ----------------- POST -----------------
    def post(self, request, event_id=None, market_type=None):
        """
        POST with market_ids as either:
        - { "market_ids": ["id1","id2"] }
        - ["id1","id2"]
        """
        validation_error = self._validate_url_params(event_id)
        if validation_error:
            return validation_error

        odds_data = self._get_event_odds_data(event_id)
        if not odds_data:
            return Response({
                'success': False,
                'error': f'No odds data found for event {event_id}',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # ✅ handle both dict & list request bodies
        if isinstance(request.data, list):
            market_ids = request.data
        else:
            market_ids = request.data.get("market_ids", [])

        # filter by market_ids
        if isinstance(market_ids, list) and market_ids:
            filtered_markets = {}
            for key, markets_list in odds_data.get("markets", {}).items():
                filtered = [m for m in markets_list if m.get("marketId") in market_ids]
                if filtered:
                    filtered_markets[key] = filtered
            odds_data["markets"] = filtered_markets

        # filter by market_type from URL
        if market_type:
            filtered_by_type = {
                key: markets_list
                for key, markets_list in odds_data.get("markets", {}).items()
                if key.lower() == market_type.lower()
                or any(m.get("market") and m["market"].lower() == market_type.lower() for m in markets_list)
            }
            odds_data["markets"] = filtered_by_type

        return Response(odds_data, status=status.HTTP_200_OK)


    # ----------------- Helpers -----------------
    def _validate_url_params(self, event_id) -> Optional[Response]:
        if not event_id or not str(event_id).strip():
            return Response({
                'success': False,
                'error': 'event_id is required in URL path',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        return None

    def _get_event_odds_data(self, event_id: str) -> Dict:
        try:
            pattern = "odds:*:*"
            for redis_key in redis_service.get_keys_by_pattern(pattern):
                event_data = redis_service.get_data(redis_key)
                if not event_data or not isinstance(event_data, dict):
                    continue

                if str(event_data.get('eventid', '')) == str(event_id) or str(event_data.get('eventId', '')) == str(event_id):
                    return self._format_event_response(event_data)

            # fallback: direct event_id search
            alternative_pattern = f"odds:*:{event_id}"
            for redis_key in redis_service.get_keys_by_pattern(alternative_pattern):
                event_data = redis_service.get_data(redis_key)
                if event_data and isinstance(event_data, dict):
                    return self._format_event_response(event_data)

            return {}
        except Exception as e:
            logger.error(f"Error getting event odds: {e}")
            return {}

    def _format_event_response(self, event_data: Dict) -> Dict:
        return {
            "eventid": str(event_data.get('eventid', event_data.get('eventId', ''))),
            "eventName": event_data.get('eventName', ''),
            "updateTime": event_data.get('updateTime'),
            "status": event_data.get('status', 'OPEN'),
            "inplay": event_data.get('inplay', False),
            "sport": event_data.get('sport', {}),
            "sportId": event_data.get('sportId'),
            "eventId": str(event_data.get('eventid', event_data.get('eventId', ''))),
            "isLiveStream": event_data.get('isLiveStream'),
            "markets": event_data.get('markets', {})
        }
