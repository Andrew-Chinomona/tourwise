"""
Smart Location Search Capability for MCP
Handles intelligent location-based property searches with suburb/city disambiguation
"""

import logging
from typing import Dict, Any, List, Optional
from django.db.models import Q
from listings.models import Property
from ..mcp_core import MCPCapability, MCPMessage, MCPResponse, MessageType
from ..nl_query_engine import run_nl_query

logger = logging.getLogger(__name__)

class SmartLocationSearchCapability(MCPCapability):
    """Handles intelligent location-based property searches"""

    def __init__(self):
        super().__init__(
            name="SmartLocationSearch",
            description="Handles intelligent location-based property searches with proper suburb/city detection"
        )

        # Known Zimbabwean suburbs (commonly searched)
        self.known_suburbs = [
            'avondale', 'borrowdale', 'mount pleasant', 'westgate', 'greendale', 'warren park',
            'mambo', 'highlands', 'mbare', 'glen view', 'glen norah', 'hatfield', 'msasa',
            'waterfalls', 'chitungwiza', 'epworth', 'ruwa', 'norton', 'chegutu', 'kadoma',
            'alexanderpark', 'belvedere', 'braeside', 'eastlea', 'greystone park', 'hillside',
            'kambuzuma', 'lochinvar', 'marlborough', 'newlands', 'tynwald', 'waterfalls'
        ]

        # Known Zimbabwean cities
        self.known_cities = [
            'harare', 'bulawayo', 'mutare', 'gweru', 'kwekwe', 'masvingo', 'chitungwiza',
            'epworth', 'ruwa', 'norton', 'chegutu', 'kadoma', 'marondera', 'chinhoyi',
            'kariba', 'victoria falls', 'hwange', 'chiredzi', 'bindura', 'rusape'
        ]

        # Location-related keywords
        self.location_keywords = [
            'in', 'at', 'near', 'around', 'located', 'situated', 'area', 'suburb', 'city',
            'properties', 'houses', 'apartments', 'homes', 'listings'
        ]

    def can_handle(self, message: MCPMessage) -> bool:
        """Check if this capability can handle the message"""
        content_lower = message.content.lower().strip()

        # Check if message contains property search terms AND location terms
        has_property_terms = any(term in content_lower for term in ['house', 'houses', 'apartment', 'apartments', 'property', 'properties', 'home', 'homes'])
        has_location_terms = any(term in content_lower for term in self.location_keywords)

        # Check if message contains known Zimbabwe locations
        has_zim_locations = any(location in content_lower for location in self.known_suburbs + self.known_cities)

        return has_property_terms and (has_location_terms or has_zim_locations)

    def process(self, message: MCPMessage, context: Dict[str, Any]) -> MCPResponse:
        """Process the smart location search"""
        print(f"🔍 SmartLocationSearchCapability processing: {message.content}")

        try:
            # Extract location from the message
            location_info = self._extract_location_info(message.content)

            if location_info['needs_clarification']:
                return self._request_clarification(location_info, message.content)

            # If we have clear location info, search with proper filtering
            return self._search_with_smart_location(message.content, location_info)

        except Exception as e:
            logger.error(f"Error in smart location search: {str(e)}", exc_info=True)
            # Fallback to regular SQL query engine
            try:
                result = run_nl_query(message.content)
                return self._format_sql_response(result, message.content)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {str(fallback_error)}")
                return MCPResponse(
                    content="I'm having trouble searching for properties right now. Please try rephrasing your request.",
                    message_type=MessageType.ERROR,
                    success=False,
                    error_message=str(e)
                )

    def _extract_location_info(self, query: str) -> Dict[str, Any]:
        """Extract and classify location information from the query"""
        query_lower = query.lower()

        location_info = {
            'locations': [],
            'is_suburb': [],
            'is_city': [],
            'ambiguous': [],
            'needs_clarification': False
        }

        # Find mentioned locations
        for suburb in self.known_suburbs:
            if suburb in query_lower:
                location_info['locations'].append(suburb)
                location_info['is_suburb'].append(suburb)

        for city in self.known_cities:
            if city in query_lower:
                location_info['locations'].append(city)
                location_info['is_city'].append(city)

        # Check for ambiguous cases (locations that could be either)
        ambiguous_locations = ['chitungwiza', 'epworth', 'ruwa', 'norton', 'chegutu', 'kadoma']
        for location in ambiguous_locations:
            if location in query_lower and location not in location_info['is_city']:
                location_info['ambiguous'].append(location)

        # If no clear locations found, we might need clarification
        if not location_info['locations']:
            location_info['needs_clarification'] = True

        return location_info

    def _request_clarification(self, location_info: Dict[str, Any], original_query: str) -> MCPResponse:
        """Request clarification for ambiguous location queries"""
        return MCPResponse(
            content="I'd be happy to help you find properties! Could you please specify which area or city in Zimbabwe you're interested in? For example: 'houses in Avondale' or 'apartments in Harare'.",
            message_type=MessageType.CONVERSATIONAL,
            metadata={"needs_location_clarification": True}
        )

    def _search_with_smart_location(self, query: str, location_info: Dict[str, Any]) -> MCPResponse:
        """Search with intelligent location handling"""
        try:
            # Build search filters
            location_filter = Q()

            # Add suburb filters
            for suburb in location_info['is_suburb']:
                location_filter |= Q(suburb__icontains=suburb)

            # Add city filters
            for city in location_info['is_city']:
                location_filter |= Q(city__icontains=city)

            # Handle ambiguous locations (search both fields)
            for location in location_info['ambiguous']:
                location_filter |= Q(suburb__icontains=location) | Q(city__icontains=location)

            # Determine property type from query
            query_lower = query.lower()
            property_filter = Q()

            if any(term in query_lower for term in ['house', 'houses', 'home', 'homes']):
                property_filter = Q(property_type='house')
            elif any(term in query_lower for term in ['apartment', 'apartments', 'flat', 'flats']):
                property_filter = Q(property_type='apartment')
            elif any(term in query_lower for term in ['airbnb']):
                property_filter = Q(property_type='airbnb')
            elif any(term in query_lower for term in ['room', 'rooms']):
                property_filter = Q(property_type='room')
            elif any(term in query_lower for term in ['guesthouse', 'guest house']):
                property_filter = Q(property_type='guesthouse')

            # Extract price constraints from query
            price_filter = Q()
            import re

            # Look for price patterns like "below $1000", "under $500", "less than $2000"
            price_patterns = [
                r'below\s+\$?(\d+(?:,\d+)*)',  # below $1000
                r'under\s+\$?(\d+(?:,\d+)*)',  # under $500
                r'less\s+than\s+\$?(\d+(?:,\d+)*)',  # less than $2000
                r'up\s+to\s+\$?(\d+(?:,\d+)*)',  # up to $1500
                r'max\s+\$?(\d+(?:,\d+)*)',  # max $1000
                r'maximum\s+\$?(\d+(?:,\d+)*)',  # maximum $1000
                r'\$?(\d+(?:,\d+)*)\s+or\s+less',  # $1000 or less
                r'\$?(\d+(?:,\d+)*)\s+and\s+below',  # $1000 and below
                r'cheaper\s+than\s+\$?(\d+(?:,\d+)*)',  # cheaper than $1000
                r'no\s+more\s+than\s+\$?(\d+(?:,\d+)*)',  # no more than $1000
                r'within\s+\$?(\d+(?:,\d+)*)',  # within $1000
            ]

            max_price = None
            for pattern in price_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    price_str = match.group(1).replace(',', '')
                    try:
                        max_price = float(price_str)
                        print(f"🔍 Extracted max price: ${max_price}")
                        break
                    except ValueError:
                        continue

            if max_price:
                price_filter = Q(price__lte=max_price)
                print(f"🔍 Applied price filter: <= ${max_price}")

            # Combine filters
            final_filter = Q(is_paid=True)
            if location_filter:
                final_filter &= location_filter
            if property_filter:
                final_filter &= property_filter
            if price_filter:
                final_filter &= price_filter

            # Execute search
            print(f"🔍 SmartLocationSearch - Final filter: {final_filter}")
            properties = Property.objects.filter(final_filter).order_by('-created_at')[:50]
            print(f"🔍 SmartLocationSearch - Found {properties.count()} properties")

            if not properties.exists():
                # No results - try fallback with SQL query engine
                print(f"🔍 No direct results found, trying SQL fallback for: {query}")
                result = run_nl_query(query)
                return self._format_sql_response(result, query)

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

            # Generate friendly message
            location_names = location_info['is_suburb'] + location_info['is_city'] + location_info['ambiguous']
            location_str = ', '.join([loc.title() for loc in location_names])

            # Add price information to the message
            price_info = ""
            if max_price:
                price_info = f" under ${max_price:,.0f}"

            if len(property_data) == 1:
                friendly_message = f"Perfect! I found 1 property in {location_str}{price_info}."
            else:
                friendly_message = f"Great! I found {len(property_data)} properties in {location_str}{price_info}."

            return MCPResponse(
                content=friendly_message,
                message_type=MessageType.PROPERTY_SEARCH,
                data={"properties": property_data},
                metadata={
                    "property_count": len(property_data),
                    "search_location": location_str,
                    "search_method": "smart_location_search"
                }
            )

        except Exception as e:
            logger.error(f"Error in smart location search: {str(e)}")
            # Fallback to SQL query engine
            result = run_nl_query(query)
            return self._format_sql_response(result, query)

    def _format_sql_response(self, result, query: str) -> MCPResponse:
        """Format SQL query engine response to match our format"""
        try:
            # Process SQL results similar to PropertySearchCapability
            rows = self._process_sql_result(result)

            if not rows:
                return MCPResponse(
                    content="Sorry, I couldn't find any properties matching your request.",
                    message_type=MessageType.PROPERTY_SEARCH,
                    data={"properties": []},
                    metadata={"property_count": 0}
                )

            # Get friendly message from SQL result
            friendly_message = result.metadata.get("chat_response", "Here's what I found.")

            return MCPResponse(
                content=friendly_message,
                message_type=MessageType.PROPERTY_SEARCH,
                data={"properties": rows},
                metadata={
                    "property_count": len(rows),
                    "sql_query": result.metadata.get("sql_query", ""),
                    "search_method": "sql_fallback"
                }
            )

        except Exception as e:
            logger.error(f"Error formatting SQL response: {str(e)}")
            return MCPResponse(
                content="I found some results but had trouble formatting them. Please try again.",
                message_type=MessageType.ERROR,
                success=False,
                error_message=str(e)
            )

    def _process_sql_result(self, result) -> List[Dict]:
        """Process SQL result and convert to property objects"""
        rows = []

        try:
            raw_result = result.response

            # Handle the complex response format from LlamaIndex
            if isinstance(raw_result, tuple) and len(raw_result) == 2:
                str_result, metadata_dict = raw_result
                if isinstance(metadata_dict, dict) and 'result' in metadata_dict:
                    parsed = metadata_dict['result']
                    col_keys = metadata_dict.get('col_keys', [])
                else:
                    parsed = ast.literal_eval(str_result) if isinstance(str_result, str) else str_result
                    col_keys = result.metadata.get("col_keys", [])
            elif isinstance(raw_result, str):
                import ast
                parsed = ast.literal_eval(raw_result)
                col_keys = result.metadata.get("col_keys", [])
            else:
                parsed = raw_result
                col_keys = result.metadata.get("col_keys", [])

            # Use fallback column keys if not available
            if not col_keys:
                col_keys = ['id', 'title', 'main_image', 'price', 'street_address', 'suburb', 'city']

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

    def _enrich_property_data(self, row: dict) -> Optional[Dict]:
        """Enrich property data with full ORM data"""
        try:
            prop = None
            if "id" in row and row["id"]:
                try:
                    prop = Property.objects.get(id=row["id"])
                except (ValueError, Property.DoesNotExist):
                    pass

            if prop:
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
                    "created_at": prop.created_at.isoformat() if prop.created_at else None
                }

            # Return minimal valid structure if no property found
            return {
                "id": row.get("id"),
                "title": row.get("title", "Property"),
                "suburb": row.get("suburb", ""),
                "city": row.get("city", ""),
                "price": row.get("price"),
                "main_image": row.get("main_image", ""),
                "description": row.get("description", "")
            }

        except Exception as e:
            logger.error(f"Error enriching property data: {str(e)}")
            return None

    def get_priority(self) -> int:
        """High priority for smart location searches"""
        return 25