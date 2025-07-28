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
        print(f"🔍 PropertySearchCapability processing: {message.content}")
        try:
            # Use the existing query engine (now pure SQL)
            result = run_nl_query(message.content)
            print(f"🔍 SQL query result type: {type(result)}")
            print(f"🔍 SQL query has response: {hasattr(result, 'response')}")

            # Process SQL results
            rows = self._process_sql_result(result, message.content)

            # Debug: Log what we got from SQL
            print(f"🔍 PropertySearch - SQL rows received: {len(rows)}")
            if rows:
                print(f"🔍 First row keys: {list(rows[0].keys())}")
                print(f"🔍 First row data: {rows[0]}")

            if not rows:
                # Fallback: Get some actual properties from the database
                print("🔍 No enriched rows found, trying fallback to get actual properties...")
                fallback_properties = Property.objects.filter(property_type='house')[:5]

                if fallback_properties.exists():
                    print(f"🔍 Found {fallback_properties.count()} fallback properties")
                    fallback_rows = []
                    for prop in fallback_properties:
                        images = PropertyImage.objects.filter(property=prop).values_list("image", flat=True)

                        # Ensure main_image is properly formatted
                        main_image_url = ""
                        if prop.main_image:
                            if hasattr(prop.main_image, 'url'):
                                main_image_url = prop.main_image.url
                            else:
                                main_image_url = str(prop.main_image)

                        fallback_rows.append({
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
                            "main_image": main_image_url,
                            # "property_images": [img.url for img in images] if images else [],
                            "created_at": prop.created_at.isoformat() if prop.created_at else None
                        })
                    rows = fallback_rows
                else:
                    return MCPResponse(
                        content="Sorry, I couldn't find any properties matching your request.",
                        message_type=MessageType.PROPERTY_SEARCH,
                        data={"properties": []},
                        metadata={"property_count": 0}
                    )

            # Apply fuzzy scoring
            scored_properties = self._apply_fuzzy_scoring(rows, message.content)

            # Debug: Log final properties
            print(f"🔍 PropertySearch - Final properties: {len(scored_properties)}")
            if scored_properties:
                print(f"🔍 First final property: {scored_properties[0]}")

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

            # Handle the complex response format from LlamaIndex
            if isinstance(raw_result, tuple) and len(raw_result) == 2:
                # Format: (string_result, metadata_dict)
                str_result, metadata_dict = raw_result
                if isinstance(metadata_dict, dict) and 'result' in metadata_dict:
                    # Use the result from metadata_dict
                    parsed = metadata_dict['result']
                    col_keys = metadata_dict.get('col_keys', [])
                else:
                    # Fallback to parsing string
                    parsed = ast.literal_eval(str_result) if isinstance(str_result, str) else str_result
                    col_keys = result.metadata.get("col_keys", [])
            elif isinstance(raw_result, str):
                parsed = ast.literal_eval(raw_result)
                col_keys = result.metadata.get("col_keys", [])
            else:
                parsed = raw_result
                col_keys = result.metadata.get("col_keys", [])

            print(f"🔍 Raw SQL result type: {type(raw_result)}")
            print(f"🔍 Column keys: {col_keys}")
            print(f"🔍 Parsed result type: {type(parsed)}")
            print(f"🔍 Parsed result length: {len(parsed) if isinstance(parsed, list) else 'N/A'}")

            # Use the column keys from the actual data if available, otherwise use correct order
            if not col_keys:
                col_keys = ['title', 'street_address', 'suburb', 'city', 'id', 'main_image', 'price']
                print(f"🔍 Using fallback column keys: {col_keys}")

            for tup in parsed:
                row = {}
                if isinstance(tup, tuple):
                    # Create row dictionary from tuple and column keys
                    row = dict(zip(col_keys, tup))
                elif isinstance(tup, dict):
                    row = tup

                print(f"🔍 Processing row: {row}")
                print(f"🔍 Row main_image: {row.get('main_image', 'NOT FOUND')}")

                # Enrich with full property data
                enriched_row = self._enrich_property_data(row)
                if enriched_row:
                    print(f"🔍 Enriched row main_image: {enriched_row.get('main_image', 'NOT FOUND')}")
                    rows.append(enriched_row)

        except Exception as e:
            logger.error(f"Error parsing SQL result: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

        return rows

    def _enrich_property_data(self, row: dict) -> dict:
        """Enrich property data with full ORM data"""
        try:
            prop = None
            if "id" in row and row["id"]:
                try:
                    prop = Property.objects.get(id=row["id"])
                except (ValueError, Property.DoesNotExist):
                    pass

            # If we couldn't find by ID, try by title
            if not prop and "title" in row and row["title"]:
                prop = Property.objects.filter(title__icontains=row["title"]).first()

            # If we still don't have a property, try to find any property that matches the data
            if not prop:
                # Try to find by city/suburb if available
                if "city" in row and row["city"]:
                    prop = Property.objects.filter(city__icontains=row["city"]).first()
                elif "suburb" in row and row["suburb"]:
                    prop = Property.objects.filter(suburb__icontains=row["suburb"]).first()

            if prop:
                # Get property images as fallback, but prioritize main_image
                images = PropertyImage.objects.filter(property=prop).values_list("image", flat=True)

                # Ensure main_image is properly formatted
                main_image_url = ""
                if prop.main_image:
                    if hasattr(prop.main_image, 'url'):
                        main_image_url = prop.main_image.url
                    else:
                        main_image_url = str(prop.main_image)

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
                    "main_image": main_image_url,
                    # "property_images": [img.url for img in images] if images else [],
                    "created_at": prop.created_at.isoformat() if prop.created_at else None
                }

            # If we still don't have a property, ensure we have the required fields for frontend
            # This ensures the frontend doesn't show "Untitled Property" and "$N/A"
            # Prioritize main_image from SQL result
            main_image_from_sql = row.get("main_image", "")
            if main_image_from_sql and not main_image_from_sql.startswith('/'):
                # If it's a relative path, make it absolute
                main_image_from_sql = f"/media/{main_image_from_sql}"

            enriched_row = {
                "id": row.get("id"),
                "title": row.get("title", "Property"),
                "description": row.get("description", ""),
                "street_address": row.get("street_address", ""),
                "suburb": row.get("suburb", ""),
                "city": row.get("city", ""),
                "state_or_region": row.get("state_or_region", ""),
                "country": row.get("country", ""),
                "property_type": row.get("property_type", ""),
                "bedrooms": row.get("bedrooms"),
                "bathrooms": row.get("bathrooms"),
                "area": row.get("area"),
                "price": row.get("price"),
                "main_image": main_image_from_sql,
                # "property_images": row.get("property_images", []),
                "created_at": row.get("created_at")
            }

            # If we have some data from SQL but not a full property object, try to find a matching property
            if not prop and (row.get("title") or row.get("city") or row.get("suburb")):
                # Try to find a property that matches any of the available data
                query = Property.objects.all()

                if row.get("title") and row.get("title") != "Property":
                    query = query.filter(title__icontains=row.get("title"))
                elif row.get("city"):
                    query = query.filter(city__icontains=row.get("city"))
                elif row.get("suburb"):
                    query = query.filter(suburb__icontains=row.get("suburb"))

                # Get the first matching property
                prop = query.first()

                if prop:
                    print(f"🔍 Found matching property by partial data: {prop.title}")
                    # Get property images as fallback, but prioritize main_image
                    images = PropertyImage.objects.filter(property=prop).values_list("image", flat=True)

                    # Ensure main_image is properly formatted
                    main_image_url = ""
                    if prop.main_image:
                        if hasattr(prop.main_image, 'url'):
                            main_image_url = prop.main_image.url
                        else:
                            main_image_url = str(prop.main_image)

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
                        "main_image": main_image_url,
                        # "property_images": [img.url for img in images] if images else [],
                        "created_at": prop.created_at.isoformat() if prop.created_at else None
                    }

            return enriched_row

        except Exception as e:
            logger.error(f"Error enriching property data: {str(e)}")
            # Return a minimal valid structure with prioritized main_image
            main_image_from_sql = row.get("main_image", "")
            if main_image_from_sql and not main_image_from_sql.startswith('/'):
                # If it's a relative path, make it absolute
                main_image_from_sql = f"/media/{main_image_from_sql}"

            return {
                "id": row.get("id"),
                "title": row.get("title", "Property"),
                "suburb": row.get("suburb", ""),
                "city": row.get("city", ""),
                "price": row.get("price"),
                "main_image": main_image_from_sql,
                "description": row.get("description", "")
            }

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