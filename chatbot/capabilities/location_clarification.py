"""
Location Clarification Capability for MCP
Handles follow-up questions for location clarification, especially for CBD searches
"""

import logging
import math
from typing import Dict, Any, List, Optional
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from listings.models import Property
from ..models import CBDLocation, ConversationState
from ..mcp_core import MCPCapability, MCPMessage, MCPResponse, MessageType

logger = logging.getLogger(__name__)


class LocationClarificationCapability(MCPCapability):
    """Handles location clarification and follow-up questions for CBD searches"""

    def __init__(self):
        super().__init__(
            name="LocationClarification",
            description="Handles location clarification and CBD follow-up questions"
        )

        # CBD-related keywords that trigger location clarification
        self.cbd_keywords = [
            "cbd", "central business district", "downtown", "city center", "town center",
            "near cbd", "close to cbd", "cbd area", "central area", "downtown area"
        ]

        # Location-related keywords that might need clarification
        self.location_keywords = [
            "near", "close to", "around", "in the area of", "within", "nearby",
            "vicinity", "surrounding", "proximity", "radius", "distance"
        ]

        # Zimbabwean cities with CBDs
        self.zimbabwe_cities = [
            "harare", "bulawayo", "mutare", "gweru", "kwekwe", "masvingo",
            "chitungwiza", "epworth", "ruwa", "chegutu", "kadoma", "marondera"
        ]

    def can_handle(self, message: MCPMessage) -> bool:
        """Check if this capability can handle the message"""
        content_lower = message.content.lower().strip()

        # Check if the message contains CBD-related keywords
        has_cbd_keywords = any(keyword in content_lower for keyword in self.cbd_keywords)

        # Check if the message contains location keywords
        has_location_keywords = any(keyword in content_lower for keyword in self.location_keywords)

        # Check if it mentions Zimbabwean cities
        has_zimbabwe_cities = any(city in content_lower for city in self.zimbabwe_cities)

        return has_cbd_keywords or (has_location_keywords and has_zimbabwe_cities)

    def process(self, message: MCPMessage, context: Dict[str, Any]) -> MCPResponse:
        """Process the location clarification request"""
        print(f"🔍 LocationClarificationCapability processing: {message.content}")

        try:
            # Get or create conversation state
            session = context.get('session')
            if not session:
                return MCPResponse(
                    content="I'm sorry, I couldn't access your conversation session. Please try again.",
                    message_type=MessageType.ERROR,
                    success=False
                )

            conv_state, created = ConversationState.objects.get_or_create(session=session)

            # Check if we're waiting for a response to a previous question
            if conv_state.waiting_for_cbd_clarification:
                return self._handle_cbd_selection(message, conv_state, context)

            # Check if we're waiting for location clarification
            if conv_state.waiting_for_location:
                return self._handle_location_response(message, conv_state, context)

            # Analyze the message for CBD-related queries
            return self._handle_initial_cbd_query(message, conv_state, context)

        except Exception as e:
            logger.error(f"Error in location clarification: {str(e)}", exc_info=True)
            return MCPResponse(
                content="Something went wrong while processing your location request. Please try again.",
                message_type=MessageType.ERROR,
                success=False,
                error_message=str(e)
            )

    def _handle_initial_cbd_query(self, message: MCPMessage, conv_state: ConversationState,
                                  context: Dict[str, Any]) -> MCPResponse:
        """Handle initial CBD-related query"""
        content_lower = message.content.lower().strip()

        # Extract city information from the message
        mentioned_cities = [city for city in self.zimbabwe_cities if city in content_lower]

        if not mentioned_cities:
            # No specific city mentioned, ask for clarification
            conv_state.waiting_for_location = True
            conv_state.pending_search_query = message.content
            conv_state.save()

            return MCPResponse(
                content="I'd be happy to help you find properties near the CBD! Which city are you looking in? (e.g., Harare, Bulawayo, Mutare, etc.)",
                message_type=MessageType.CONVERSATIONAL,
                metadata={"waiting_for_location": True}
            )

        # City mentioned, check if we have CBD data for it
        city = mentioned_cities[0]
        cbds = CBDLocation.objects.filter(city__iexact=city, is_active=True)

        if cbds.count() == 1:
            # Only one CBD for this city, use it directly
            cbd = cbds.first()
            return self._search_properties_near_cbd(cbd, message.content, context)

        elif cbds.count() > 1:
            # Multiple CBDs, ask for clarification
            conv_state.waiting_for_cbd_clarification = True
            conv_state.pending_search_query = message.content
            conv_state.suggested_cbds = [{"id": cbd.id, "name": cbd.name, "city": cbd.city} for cbd in cbds]
            conv_state.save()

            cbd_list = "\n".join([f"• {cbd.name}" for cbd in cbds])
            return MCPResponse(
                content=f"I found multiple CBD areas in {city.title()}. Which one are you interested in?\n\n{cbd_list}",
                message_type=MessageType.CONVERSATIONAL,
                metadata={"waiting_for_cbd_clarification": True, "suggested_cbds": conv_state.suggested_cbds}
            )

        else:
            # No CBD data for this city, create a default one or search by city center
            return self._search_properties_by_city_center(city, message.content, context)

    def _handle_cbd_selection(self, message: MCPMessage, conv_state: ConversationState,
                              context: Dict[str, Any]) -> MCPResponse:
        """Handle user's CBD selection"""
        content_lower = message.content.lower().strip()

        # Find the selected CBD
        selected_cbd = None
        for cbd_info in conv_state.suggested_cbds:
            if cbd_info['name'].lower() in content_lower:
                try:
                    selected_cbd = CBDLocation.objects.get(id=cbd_info['id'])
                    break
                except CBDLocation.DoesNotExist:
                    continue

        if not selected_cbd:
            # Try to find by partial match
            for cbd_info in conv_state.suggested_cbds:
                if any(word in cbd_info['name'].lower() for word in content_lower.split()):
                    try:
                        selected_cbd = CBDLocation.objects.get(id=cbd_info['id'])
                        break
                    except CBDLocation.DoesNotExist:
                        continue

        if selected_cbd:
            conv_state.selected_cbd = selected_cbd
            conv_state.waiting_for_cbd_clarification = False
            conv_state.save()

            return self._search_properties_near_cbd(selected_cbd, conv_state.pending_search_query, context)
        else:
            # Invalid selection, ask again
            cbd_list = "\n".join([f"• {cbd['name']}" for cbd in conv_state.suggested_cbds])
            return MCPResponse(
                content=f"I didn't understand your selection. Please choose from the following CBD areas:\n\n{cbd_list}",
                message_type=MessageType.CONVERSATIONAL,
                metadata={"waiting_for_cbd_clarification": True, "suggested_cbds": conv_state.suggested_cbds}
            )

    def _handle_location_response(self, message: MCPMessage, conv_state: ConversationState,
                                  context: Dict[str, Any]) -> MCPResponse:
        """Handle user's location response"""
        content_lower = message.content.lower().strip()

        # Extract city from response
        mentioned_cities = [city for city in self.zimbabwe_cities if city in content_lower]

        if not mentioned_cities:
            conv_state.reset_state()
            return MCPResponse(
                content="I'm sorry, I didn't recognize that city. Please try again with a Zimbabwean city like Harare, Bulawayo, Mutare, etc.",
                message_type=MessageType.CONVERSATIONAL
            )

        city = mentioned_cities[0]
        conv_state.waiting_for_location = False
        conv_state.save()

        # Now process the original query with the specified city
        original_query = conv_state.pending_search_query
        if original_query:
            # Add the city to the original query
            enhanced_query = f"{original_query} in {city}"
            return self._handle_initial_cbd_query(
                MCPMessage(content=enhanced_query, message_type=MessageType.CONVERSATIONAL),
                conv_state,
                context
            )
        else:
            return MCPResponse(
                content=f"Great! Now I can help you find properties near the CBD in {city.title()}. What type of property are you looking for?",
                message_type=MessageType.CONVERSATIONAL
            )

    def _search_properties_near_cbd(self, cbd: CBDLocation, original_query: str,
                                    context: Dict[str, Any]) -> MCPResponse:
        """Search for properties within 10km of the CBD"""
        try:
            # Create a Point for the CBD location
            cbd_point = Point(cbd.longitude, cbd.latitude)

            # Search for properties within 10km radius
            properties = Property.objects.filter(
                is_paid=True,
                location__isnull=False
            ).annotate(
                distance=Distance('location', cbd_point)
            ).filter(
                distance__lte=10000  # 10km in meters
            ).order_by('distance')[:20]  # Limit to 20 closest properties

            if not properties.exists():
                return MCPResponse(
                    content=f"I couldn't find any properties within 10km of {cbd.name} in {cbd.city}. Would you like me to search in a wider area or try a different location?",
                    message_type=MessageType.PROPERTY_SEARCH,
                    data={"properties": []},
                    metadata={"property_count": 0, "search_location": cbd.name}
                )

            # Convert to property data format
            property_data = []
            for prop in properties:
                property_data.append({
                    "id": prop.id,
                    "title": prop.title,
                    "description": prop.description,
                    "street_address": prop.street_address,
                    "suburb": prop.suburb,
                    "city": prop.city,
                    "state_or_region": prop.state_or_region,
                    "country": prop.country,
                    "property_type": prop.property_type,
                    "bedrooms": prop.bedrooms,
                    "bathrooms": prop.bathrooms,
                    "area": prop.area,
                    "price": float(prop.price) if prop.price else None,
                    "main_image": prop.main_image.url if prop.main_image else "",
                    "distance_from_cbd": round(prop.distance.km, 1) if hasattr(prop, 'distance') else None,
                    "created_at": prop.created_at.isoformat() if prop.created_at else None
                })

            # Reset conversation state
            session = context.get('session')
            if session:
                conv_state, _ = ConversationState.objects.get_or_create(session=session)
                conv_state.reset_state()

            return MCPResponse(
                content=f"I found {len(property_data)} properties within 10km of {cbd.name} in {cbd.city}. Here are the closest ones:",
                message_type=MessageType.PROPERTY_SEARCH,
                data={"properties": property_data},
                metadata={
                    "property_count": len(property_data),
                    "search_location": cbd.name,
                    "search_radius_km": 10,
                    "cbd_coordinates": {"lat": cbd.latitude, "lng": cbd.longitude}
                }
            )

        except Exception as e:
            logger.error(f"Error searching properties near CBD: {str(e)}")
            return MCPResponse(
                content="Sorry, I encountered an error while searching for properties. Please try again.",
                message_type=MessageType.ERROR,
                success=False,
                error_message=str(e)
            )

    def _search_properties_by_city_center(self, city: str, original_query: str, context: Dict[str, Any]) -> MCPResponse:
        """Search for properties in the city when no CBD data is available"""
        try:
            # Search for properties in the city
            properties = Property.objects.filter(
                is_paid=True,
                city__iexact=city
            ).order_by('-created_at')[:20]

            if not properties.exists():
                return MCPResponse(
                    content=f"I couldn't find any properties in {city.title()}. Would you like me to search in nearby areas?",
                    message_type=MessageType.PROPERTY_SEARCH,
                    data={"properties": []},
                    metadata={"property_count": 0, "search_location": city}
                )

            # Convert to property data format
            property_data = []
            for prop in properties:
                property_data.append({
                    "id": prop.id,
                    "title": prop.title,
                    "description": prop.description,
                    "street_address": prop.street_address,
                    "suburb": prop.suburb,
                    "city": prop.city,
                    "state_or_region": prop.state_or_region,
                    "country": prop.country,
                    "property_type": prop.property_type,
                    "bedrooms": prop.bedrooms,
                    "bathrooms": prop.bathrooms,
                    "area": prop.area,
                    "price": float(prop.price) if prop.price else None,
                    "main_image": prop.main_image.url if prop.main_image else "",
                    "created_at": prop.created_at.isoformat() if prop.created_at else None
                })

            return MCPResponse(
                content=f"I found {len(property_data)} properties in {city.title()}. Here are the most recent listings:",
                message_type=MessageType.PROPERTY_SEARCH,
                data={"properties": property_data},
                metadata={
                    "property_count": len(property_data),
                    "search_location": city,
                    "note": "No CBD data available, showing city-wide results"
                }
            )

        except Exception as e:
            logger.error(f"Error searching properties by city: {str(e)}")
            return MCPResponse(
                content="Sorry, I encountered an error while searching for properties. Please try again.",
                message_type=MessageType.ERROR,
                success=False,
                error_message=str(e)
            )

    def get_priority(self) -> int:
        """High priority for location clarification"""
        return 30