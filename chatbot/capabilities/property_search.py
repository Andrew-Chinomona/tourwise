"""
Property Search Capability for MCP
Handles property-related queries using the existing SQL query engine
"""

import ast
import logging
from typing import Dict, Any
from rapidfuzz import fuzz
from listings.models import Property, PropertyImage
from ..mcp_core import MCPCapability, MCPMessage, MCPResponse, MessageType
from ..nl_query_engine import run_nl_query

logger = logging.getLogger(__name__)


class PropertySearchCapability(MCPCapability):
    """Handles property search queries using the existing SQL query engine"""

    def __init__(self):
        super().__init__(
            name="PropertySearch",
            description="Handles property search queries using SQL and fuzzy matching"
        )

        # Property-related keywords that indicate a search query
        self.property_keywords = [
            "house", "houses", "home", "homes", "apartment", "apartments", "flat", "flats",
            "property", "properties", "rent", "rental", "buy", "purchase", "price", "cost",
            "bedroom", "bedrooms", "bathroom", "bathrooms", "area", "location", "city",
            "suburb", "harare", "bulawayo", "mutare", "gweru", "kwekwe", "masvingo",
            "cheap", "expensive", "affordable", "luxury", "modern", "traditional"
        ]

    def can_handle(self, message: MCPMessage) -> bool:
        """Check if this capability can handle the message"""
        content_lower = message.content.lower().strip()

        # Check if the message contains property-related keywords
        return any(keyword in content_lower for keyword in self.property_keywords)

    def process(self, message: MCPMessage, context: Dict[str, Any]) -> MCPResponse:
        """Process the property search query"""
        try:
            # Use the existing query engine
            result = run_nl_query(message.content)

            # Handle conversational responses (already handled by conversational capability)
            if isinstance(result, dict) and result.get("is_conversational"):
                return MCPResponse(
                    content=result.get("chat_response", "Hello!"),
                    message_type=MessageType.CONVERSATIONAL,
                    metadata={"is_conversational": True}
                )

            # Process SQL results
            rows = self._process_sql_result(result, message.content)

            if not rows:
                return MCPResponse(
                    content="Sorry, I couldn't find any properties matching your request.",
                    message_type=MessageType.PROPERTY_SEARCH,
                    data={"properties": []},
                    metadata={"property_count": 0}
                )

            # Apply fuzzy scoring
            scored_properties = self._apply_fuzzy_scoring(rows, message.content)

            # Get friendly message
            friendly_message = result.metadata.get("chat_response", "Here is what I found.")

            return MCPResponse(
                content=friendly_message,
                message_type=MessageType.PROPERTY_SEARCH,
                data={"properties": scored_properties},
                metadata={
                    "property_count": len(scored_properties),
                    "sql_query": result.metadata.get("sql_query", ""),
                    "properties": scored_properties  # For backward compatibility
                }
            )

        except Exception as e:
            logger.error(f"Error in property search: {str(e)}", exc_info=True)
            return MCPResponse(
                content="Something went wrong while searching for properties. Please try again.",
                message_type=MessageType.ERROR,
                success=False,
                error_message=str(e)
            )

    def _process_sql_result(self, result, user_input: str) -> list:
        """Process SQL result and convert to property objects"""
        rows = []

        try:
            raw_result = result.response
            if isinstance(raw_result, str):
                parsed = ast.literal_eval(raw_result)
            else:
                parsed = raw_result

            col_keys = result.metadata.get("col_keys", [])

            for tup in parsed:
                row = {}
                if isinstance(tup, tuple):
                    row = dict(zip(col_keys, tup))
                elif isinstance(tup, dict):
                    row = tup

                # Enrich with full property data
                enriched_row = self._enrich_property_data(row)
                if enriched_row:
                    rows.append(enriched_row)

        except Exception as e:
            logger.error(f"Error parsing SQL result: {str(e)}")
            return []

        return rows

    def _enrich_property_data(self, row: dict) -> dict:
        """Enrich property data with full ORM data"""
        try:
            prop = None
            if "id" in row:
                prop = Property.objects.get(id=row["id"])
            elif "title" in row:
                prop = Property.objects.filter(title__icontains=row["title"]).first()

            if prop:
                # Get property images
                images = PropertyImage.objects.filter(property=prop).values_list("image", flat=True)

                return {
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
                    "property_images": [img.url for img in images],
                    "created_at": prop.created_at.isoformat() if prop.created_at else None
                }

            return row

        except Property.DoesNotExist:
            return row
        except Exception as e:
            logger.error(f"Error enriching property data: {str(e)}")
            return row

    def _apply_fuzzy_scoring(self, properties: list, user_input: str) -> list:
        """Apply fuzzy scoring to properties based on user input"""
        scored = []

        for prop in properties:
            description = prop.get("description", "")
            amenities_str = ""

            # Get amenities if property ID is available
            if "id" in prop:
                try:
                    property_obj = Property.objects.get(id=prop["id"])
                    amenities = property_obj.amenities.all()
                    amenities_str = ", ".join([a.name for a in amenities])
                except Property.DoesNotExist:
                    pass

            # Calculate scores
            desc_score = fuzz.token_set_ratio(user_input, description)
            amenity_score = fuzz.token_set_ratio(user_input, amenities_str)
            total_score = desc_score * 0.6 + amenity_score * 0.4

            scored.append((total_score, prop))

        # Sort by score descending
        scored.sort(reverse=True, key=lambda x: x[0])

        # Return properties without scores
        return [prop for score, prop in scored]

    def get_priority(self) -> int:
        """Medium priority for property search"""
        return 50