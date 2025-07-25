"""
Backend Formatter for Chatbot Frontend
Ensures data is rendered in the exact format the frontend expects
"""


def format_properties_for_frontend(properties):
    """
    Format properties data in the exact structure the frontend expects
    """
    if not properties:
        return []

    formatted_properties = []

    for prop in properties:
        # Ensure each property has all required fields
        formatted_prop = {
            'id': prop.get('id'),
            'title': prop.get('title') or 'Property',
            'price': prop.get('price'),
            'city': prop.get('city') or '',
            'suburb': prop.get('suburb') or '',
            'main_image': prop.get('main_image') or '',
            'street_address': prop.get('street_address') or '',
            'description': prop.get('description') or '',
            'bedrooms': prop.get('bedrooms'),
            'bathrooms': prop.get('bathrooms'),
            'area': prop.get('area'),
            'property_type': prop.get('property_type') or '',
            'property_images': prop.get('property_images') or []
        }

        # Ensure main_image is properly formatted
        if formatted_prop['main_image'] and not formatted_prop['main_image'].startswith(('http', '/media/')):
            formatted_prop['main_image'] = f"/media/{formatted_prop['main_image']}"

        formatted_properties.append(formatted_prop)

    return formatted_properties


def format_response_for_frontend(mcp_response):
    """
    Format the complete response in the exact structure the frontend expects
    """
    response_data = {
        'friendly_message': mcp_response.content,
        'result': [],
        'property_count': 0
    }

    # Handle different message types
    if hasattr(mcp_response, 'message_type'):
        if str(mcp_response.message_type) in ['MessageType.GREETING', 'MessageType.FAREWELL',
                                              'MessageType.GRATITUDE', 'MessageType.HELP',
                                              'MessageType.CONVERSATIONAL']:
            response_data['is_conversational'] = True
            return response_data

        elif str(mcp_response.message_type) in ['MessageType.PROPERTY_SEARCH', 'MessageType.DATABASE_QUERY']:
            if mcp_response.data and 'properties' in mcp_response.data:
                properties = mcp_response.data['properties']
                formatted_properties = format_properties_for_frontend(properties)
                response_data['result'] = formatted_properties
                response_data['property_count'] = len(formatted_properties)

    # Handle error responses
    if hasattr(mcp_response, 'success') and not mcp_response.success:
        response_data['error'] = getattr(mcp_response, 'error_message', 'An error occurred')

    return response_data