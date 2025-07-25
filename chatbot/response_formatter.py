"""
Response Formatter for MCP
Converts MCP responses to the format expected by the existing frontend
"""

import json
from typing import Dict, Any, List
from decimal import Decimal
from .mcp_core import MCPResponse, MessageType

def convert_decimal_to_float(obj):
    """Recursively convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    else:
        return obj

def _force_convert_to_basic_types(obj):
    """Force convert any object to basic JSON-safe types"""
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {str(key): _force_convert_to_basic_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_force_convert_to_basic_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return [_force_convert_to_basic_types(item) for item in obj]
    else:
        # Convert any other object to string
        try:
            return str(obj)
        except:
            return "Unknown object"

class MCPResponseFormatter:
    """Formats MCP responses for the frontend"""

    @staticmethod
    def format_for_frontend(mcp_response: MCPResponse) -> Dict[str, Any]:
        """Convert MCP response to frontend format"""

        # Handle conversational responses
        if mcp_response.message_type in [MessageType.GREETING, MessageType.FAREWELL,
                                        MessageType.GRATITUDE, MessageType.HELP,
                                        MessageType.CONVERSATIONAL]:
            return {
                "friendly_message": mcp_response.content,
                "result": [],
                "is_conversational": True
            }

        # Handle property search responses
        elif mcp_response.message_type == MessageType.PROPERTY_SEARCH:
            properties = mcp_response.data.get("properties", []) if mcp_response.data else []

            # Debug: Log the properties to see what we're getting
            print(f"🔍 MCP Response Formatter - Properties received: {len(properties)}")
            if properties:
                print(f"🔍 First property keys: {list(properties[0].keys())}")
                print(f"🔍 First property title: {properties[0].get('title', 'NO TITLE')}")
                print(f"🔍 First property price: {properties[0].get('price', 'NO PRICE')}")
                print(f"🔍 First property city: {properties[0].get('city', 'NO CITY')}")

            # Convert properties to JSON-safe format
            safe_properties = _force_convert_to_basic_types(properties)

            return {
                "friendly_message": mcp_response.content,
                "result": safe_properties,
                "property_count": len(properties)
            }

        # Handle database query responses
        elif mcp_response.message_type == MessageType.DATABASE_QUERY:
            properties = mcp_response.data.get("properties", []) if mcp_response.data else []

            # Convert properties to JSON-safe format
            safe_properties = _force_convert_to_basic_types(properties)

            return {
                "friendly_message": mcp_response.content,
                "result": safe_properties,
                "property_count": len(properties)
            }

        # Handle error responses
        elif mcp_response.message_type == MessageType.ERROR:
            return {
                "error": mcp_response.error_message or "An error occurred",
                "friendly_message": mcp_response.content
            }

        # Default fallback
        else:
            return {
                "friendly_message": mcp_response.content,
                "result": [],
                "message_type": mcp_response.message_type.value
            }

    @staticmethod
    def format_for_database_save(mcp_response: MCPResponse) -> Dict[str, Any]:
        """Format response metadata for database storage"""
        metadata = {}

        if mcp_response.message_type == MessageType.PROPERTY_SEARCH:
            properties = mcp_response.data.get("properties", []) if mcp_response.data else []
            metadata = {
                'property_count': len(properties),
                'properties': _force_convert_to_basic_types(properties)
            }
        elif mcp_response.message_type == MessageType.DATABASE_QUERY:
            properties = mcp_response.data.get("properties", []) if mcp_response.data else []
            metadata = {
                'property_count': len(properties),
                'properties': _force_convert_to_basic_types(properties)
            }
        elif mcp_response.message_type == MessageType.ERROR:
            metadata = {
                'error': mcp_response.error_message,
                'error_type': 'processing_error'
            }
        else:
            metadata = mcp_response.metadata or {}

        # Ensure metadata is JSON serializable
        try:
            json.dumps(metadata)
        except (TypeError, ValueError):
            metadata = _force_convert_to_basic_types(metadata)

        return metadata 