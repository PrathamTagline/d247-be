import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from dotenv import load_dotenv

from backend.services import redis_service
from backend.services.scaper_service import get_highlight_home_private, get_odds, get_tree_record
from backend.services.store_treedata_service import save_tree_data

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
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class GetOddsByEventAndMarketView(APIView):
    """
    GET/POST API to get odds data by sport_id/event_id and market type
    
    URLs:
    - /api/odds/{sport_id}/{event_id}/
    - /api/odds/{sport_id}/{event_id}/{market_type}/
    
    Query Parameters (optional for backward compatibility):
    - market: Market type filter (e.g., "MATCH_ODDS", "BOOKMAKER", "FANCY")
    
    POST Body (optional):
    {
        "market_ids": ["7190840406478", "7190840406479", ...]
    }
    
    Examples:
    GET /api/odds/1/834441373/
    GET /api/odds/1/834441373/MATCH_ODDS/
    GET /api/odds/1/834441373/BOOKMAKER/
    POST /api/odds/1/834441373/BOOKMAKER/
    {
        "market_ids": ["6264639438562", "743748094417"]
    }
    
    Backward compatibility:
    GET /api/odds/1/834441373/?market=MATCH_ODDS (still supported)
    """
    
    def get(self, request, sport_id=None, event_id=None, market_type=None):
        """Handle GET requests"""
        return self._handle_request(request, sport_id, event_id, market_type)
    
    def post(self, request, sport_id=None, event_id=None, market_type=None):
        """Handle POST requests with market_ids in body"""
        return self._handle_request(request, sport_id, event_id, market_type)
    
    def _handle_request(self, request, sport_id=None, event_id=None, market_type=None):
        """Common handler for GET and POST requests"""
        try:
            # Validate URL parameters
            validation_error = self._validate_url_params(sport_id, event_id)
            if validation_error:
                return validation_error
            
            # Determine market type (URL parameter takes precedence over query parameter)
            final_market_type = self._get_market_type(request, market_type)
            
            # Get market_ids from POST body (optional)
            market_ids = []
            if request.method == 'POST':
                market_ids = request.data.get('market_ids', [])
                # Validate market_ids if provided
                if market_ids:
                    validation_error = self._validate_market_ids(market_ids)
                    if validation_error:
                        return validation_error
            
            # Get odds data
            odds_data, not_found_markets = self._get_odds_by_event_and_market(
                event_id, final_market_type, market_ids
            )
            
            # Prepare response
            response_data = {
                'success': True,
                'sport_id': sport_id,
                'event_id': event_id,
                'market_type': final_market_type if final_market_type else 'ALL',
                'data': odds_data,
                'total_found': len(odds_data),
                'message': f'Retrieved {len(odds_data)} odds for event {event_id}'
            }
            
            # Add market_ids specific info if applicable
            if market_ids:
                response_data.update({
                    'total_requested': len(market_ids),
                    'not_found_markets': not_found_markets,
                    'message': f'Retrieved {len(odds_data)} out of {len(market_ids)} requested markets'
                })
            
            logger.info(f"Successfully retrieved odds for event {event_id}, market: {final_market_type}")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in GetOddsByEventAndMarketView: {e}")
            return Response({
                'success': False,
                'error': f'Internal server error: {str(e)}',
                'data': [],
                'sport_id': sport_id,
                'event_id': event_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_market_type(self, request, url_market_type=None):
        """
        Get market type from URL parameter or query parameter (for backward compatibility)
        URL parameter takes precedence over query parameter
        """
        if url_market_type:
            return url_market_type.upper()
        
        # Fallback to query parameter for backward compatibility
        query_market_type = request.query_params.get('market', '')
        return query_market_type.upper() if query_market_type else ''
    
    def _validate_url_params(self, sport_id, event_id) -> Optional[Response]:
        """Validate URL parameters"""
        if not sport_id:
            return Response({
                'success': False,
                'error': 'sport_id is required in URL path',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not event_id:
            return Response({
                'success': False,
                'error': 'event_id is required in URL path',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            int(sport_id)
            int(event_id)
        except ValueError:
            return Response({
                'success': False,
                'error': 'sport_id and event_id must be valid integers',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return None
    
    def _validate_market_ids(self, market_ids: List) -> Optional[Response]:
        """Validate market_ids from POST body"""
        if not isinstance(market_ids, list):
            return Response({
                'success': False,
                'error': 'market_ids must be a list',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(market_ids) > 100:
            return Response({
                'success': False,
                'error': 'Maximum 100 market IDs allowed per request',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if all items are strings or can be converted to strings
        try:
            market_ids[:] = [str(mid).strip() for mid in market_ids if str(mid).strip()]
        except Exception:
            return Response({
                'success': False,
                'error': 'All market_ids must be valid strings/numbers',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return None
    
    def _get_odds_by_event_and_market(self, event_id: str, market_type: str, market_ids: List[str] = None) -> tuple:
        """
        Get odds data for the given event_id and market type
        
        Args:
            event_id: Event ID to search for
            market_type: Market type filter (MATCH_ODDS, BOOKMAKER, FANCY, etc.)
            market_ids: Optional specific market IDs to filter
            
        Returns:
            tuple: (odds_data, not_found_markets)
        """
        odds_data = []
        not_found_markets = []
        
        try:
            # Get Redis key for the specific event
            redis_key = f"odds:{event_id}"
            event_data = redis_service.get_data(redis_key)
            
            if not event_data:
                # Try pattern search if direct key doesn't exist
                all_odds_keys = redis_service.get_keys_by_pattern("odds:*")
                for key in all_odds_keys:
                    data = redis_service.get_data(key)
                    if data and isinstance(data, dict) and data.get('eventid') == event_id:
                        event_data = data
                        break
            
            if not event_data:
                return [], market_ids if market_ids else []
            
            # Extract markets based on criteria
            extracted_markets = self._extract_markets_by_criteria(
                event_data, market_type, market_ids
            )
            
            if market_ids:
                # Track which market IDs were found
                found_market_ids = {market['marketId'] for market in extracted_markets}
                not_found_markets = [mid for mid in market_ids if mid not in found_market_ids]
            
            odds_data.extend(extracted_markets)
            
        except Exception as e:
            logger.error(f"Error getting odds for event {event_id}: {e}")
            not_found_markets = market_ids if market_ids else []
        
        return odds_data, not_found_markets
    
    def _extract_markets_by_criteria(self, event_data: Dict, market_type: str, market_ids: List[str] = None) -> List[Dict]:
        """
        Extract markets from event data based on criteria
        
        Args:
            event_data: Event data with grouped markets
            market_type: Market type filter
            market_ids: Optional specific market IDs
            
        Returns:
            List of matching markets
        """
        matching_markets = []
        
        try:
            if not isinstance(event_data, dict) or 'markets' not in event_data:
                return []
            
            markets = event_data['markets']
            
            # Determine which market types to search
            market_types_to_search = []
            if market_type:
                # Map market type to internal keys
                type_mapping = {
                    'MATCH_ODDS': ['odds'],
                    'BOOKMAKER': ['bookmaker'],
                    'FANCY': ['fancy'],
                    'SESSION': ['session'],
                    'TOSS': ['toss']
                }
                market_types_to_search = type_mapping.get(market_type, [market_type.lower()])
            else:
                # Search all market types
                market_types_to_search = list(markets.keys())
            
            # Search through specified market types
            for market_key in market_types_to_search:
                if market_key in markets and isinstance(markets[market_key], list):
                    for market in markets[market_key]:
                        if isinstance(market, dict):
                            # Check if specific market IDs are requested
                            if market_ids:
                                if market.get('marketId') not in market_ids:
                                    continue
                            
                            # Create complete market object
                            complete_market = {
                                'eventid': event_data.get('eventid'),
                                'eventName': event_data.get('eventName'),
                                'marketId': market.get('marketId'),
                                'market': market.get('market'),
                                'updateTime': event_data.get('updateTime'),
                                'status': market.get('status'),
                                'inplay': market.get('inplay'),
                                'totalMatched': market.get('totalMatched'),
                                'active': market.get('active'),
                                'markettype': market.get('markettype'),
                                'min': market.get('min'),
                                'max': market.get('max'),
                                'runners': market.get('runners', []),
                                'sport': event_data.get('sport'),
                                'isLiveStream': event_data.get('isLiveStream')
                            }
                            matching_markets.append(complete_market)
            
        except Exception as e:
            logger.error(f"Error extracting markets by criteria: {e}")
        
        return matching_markets


# Keep the original view for backward compatibility
class GetOddsByMarketIdsView(APIView):
    """
    Original POST API to get odds data by market IDs (mids)
    Maintained for backward compatibility
    
    Payload:
    {
        "market_ids": ["7190840406478", "7190840406479", ...]
    }
    """
    
    def post(self, request):
        try:
            # Parse and validate request data
            market_ids = request.data.get('market_ids', [])
            
            # Input validation
            validation_error = self._validate_input(market_ids)
            if validation_error:
                return validation_error
            
            # Get odds data for each market ID
            odds_data, not_found_markets = self._get_odds_for_market_ids(market_ids)
            
            # Prepare response
            response_data = {
                'success': True,
                'data': odds_data,
                'total_requested': len(market_ids),
                'total_found': len(odds_data),
                'not_found_markets': not_found_markets,
                'message': f'Retrieved {len(odds_data)} out of {len(market_ids)} requested odds'
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Internal server error: {str(e)}',
                'data': [],
                'total_requested': 0,
                'total_found': 0,
                'not_found_markets': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _validate_input(self, market_ids: List) -> Optional[Response]:
        """Validate the input market_ids"""
        
        if not market_ids:
            return Response({
                'success': False,
                'error': 'market_ids is required and cannot be empty',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(market_ids, list):
            return Response({
                'success': False,
                'error': 'market_ids must be a list',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(market_ids) > 100:
            return Response({
                'success': False,
                'error': 'Maximum 100 market IDs allowed per request',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if all items are strings or can be converted to strings
        try:
            market_ids[:] = [str(mid).strip() for mid in market_ids if str(mid).strip()]
        except Exception:
            return Response({
                'success': False,
                'error': 'All market_ids must be valid strings/numbers',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not market_ids:  # If all were empty after stripping
            return Response({
                'success': False,
                'error': 'market_ids cannot contain only empty values',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return None
    
    def _get_odds_for_market_ids(self, market_ids: List[str]) -> tuple:
        """
        Get odds data for the given market IDs from grouped market format
        
        Returns:
            tuple: (odds_data, not_found_markets)
        """
        odds_data = []
        not_found_markets = []
        
        # Get all Redis keys with odds pattern
        all_odds_keys = redis_service.get_keys_by_pattern("odds:*")
        
        # Process each market ID by checking all Redis keys
        for market_id in market_ids:
            found = False
            
            for redis_key in all_odds_keys:
                try:
                    # Get data from Redis
                    event_data = redis_service.get_data(redis_key)
                    
                    if event_data:
                        # Extract matching markets from grouped format
                        matching_markets = self._extract_matching_markets_from_grouped(event_data, market_id)
                        
                        if matching_markets:
                            odds_data.extend(matching_markets)
                            found = True
                            break  # Found the market ID, move to next
                            
                except Exception as e:
                    continue
            
            if not found:
                not_found_markets.append(market_id)
        
        return odds_data, not_found_markets
    
    def _extract_matching_markets_from_grouped(self, event_data: Any, market_id: str) -> List[Dict]:
        """
        Extract markets matching the market_id from grouped event data
        """
        matching_markets = []
        
        try:
            # Handle grouped market format
            if isinstance(event_data, dict) and 'markets' in event_data:
                markets = event_data['markets']
                
                # Search through all market types (bookmaker, fancy, odds, etc.)
                for market_type, market_list in markets.items():
                    if isinstance(market_list, list):
                        for market in market_list:
                            if isinstance(market, dict) and market.get('marketId') == market_id:
                                # Create a complete market object with event info
                                complete_market = {
                                    'eventid': event_data.get('eventid'),
                                    'eventName': event_data.get('eventName'),
                                    'marketId': market.get('marketId'),
                                    'market': market.get('market'),
                                    'updateTime': event_data.get('updateTime'),
                                    'status': market.get('status'),
                                    'inplay': market.get('inplay'),
                                    'totalMatched': market.get('totalMatched'),
                                    'active': market.get('active'),
                                    'markettype': market.get('markettype'),
                                    'min': market.get('min'),
                                    'max': market.get('max'),
                                    'runners': market.get('runners', []),
                                    'sport': event_data.get('sport'),
                                    'isLiveStream': event_data.get('isLiveStream')
                                }
                                matching_markets.append(complete_market)
            
            return matching_markets
            
        except Exception as e:
            return []