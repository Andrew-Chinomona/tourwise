# Follow-Up Questions Feature

This document describes the new follow-up questions functionality implemented in the Tourwise chatbot.

## Overview

The chatbot now supports intelligent follow-up questions to clarify location information, especially for CBD (Central Business District) searches. When a user asks for properties "near the CBD" without specifying a city, the chatbot will ask for clarification and then search for properties within a 10km radius of the specified CBD.

## Features

### 1. Location Clarification
- **Trigger**: When users mention "CBD", "near CBD", "close to CBD", etc. without specifying a city
- **Response**: Asks user to specify which city they're interested in
- **Example**: 
  - User: "I am looking for houses near the CBD"
  - Bot: "I'd be happy to help you find properties near the CBD! Which city are you looking in? (e.g., Harare, Bulawayo, Mutare, etc.)"

### 2. CBD-Specific Searches
- **Functionality**: Searches for properties within 10km radius of the CBD
- **Distance Calculation**: Uses PostGIS geospatial functions for accurate distance calculation
- **Results**: Returns properties sorted by distance from CBD

### 3. Multiple CBD Support
- **Handling**: If a city has multiple CBD areas, the bot asks for clarification
- **Example**:
  - User: "I want apartments near the CBD in Harare"
  - Bot: "I found multiple CBD areas in Harare. Which one are you interested in?
    • Harare CBD
    • Avondale CBD"

### 4. Conversation State Management
- **Persistence**: Maintains conversation state across multiple messages
- **Context**: Remembers the original query while waiting for clarification
- **Reset**: Automatically resets state after completing a search

## Database Models

### CBDLocation
Stores CBD coordinates and information for Zimbabwean cities:
```python
class CBDLocation(models.Model):
    name = models.CharField(max_length=100, unique=True)
    city = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
```

### ConversationState
Tracks conversation state for follow-up questions:
```python
class ConversationState(models.Model):
    session = models.OneToOneField(ChatSession, on_delete=models.CASCADE)
    waiting_for_location = models.BooleanField(default=False)
    waiting_for_cbd_clarification = models.BooleanField(default=False)
    pending_search_query = models.TextField(blank=True)
    suggested_cbds = models.JSONField(default=list)
    selected_cbd = models.ForeignKey(CBDLocation, on_delete=models.SET_NULL, null=True)
```

## Setup Instructions

### 1. Run Migrations
```bash
python manage.py migrate chatbot
```

### 2. Populate CBD Data
```bash
python manage.py populate_cbd_data
```

This command creates CBD locations for major Zimbabwean cities:
- Harare CBD
- Bulawayo CBD
- Mutare CBD
- Gweru CBD
- Kwekwe CBD
- Masvingo CBD
- Chitungwiza CBD
- Epworth CBD
- Ruwa CBD
- Chegutu CBD
- Kadoma CBD
- Marondera CBD

### 3. Verify Installation
Check the Django admin interface to see the new CBD locations and conversation states.

## Usage Examples

### Example 1: Basic CBD Search
```
User: "I am looking for houses near the CBD"
Bot: "I'd be happy to help you find properties near the CBD! Which city are you looking in? (e.g., Harare, Bulawayo, Mutare, etc.)"

User: "Harare"
Bot: "I found 15 properties within 10km of Harare CBD. Here are the closest ones:"
[Shows property results with distance information]
```

### Example 2: Direct City Specification
```
User: "I want apartments near the CBD in Bulawayo"
Bot: "I found 8 properties within 10km of Bulawayo CBD. Here are the closest ones:"
[Shows property results with distance information]
```

### Example 3: Multiple CBD Areas
```
User: "I need a house near the CBD in Harare"
Bot: "I found multiple CBD areas in Harare. Which one are you interested in?
• Harare CBD
• Avondale CBD"

User: "Harare CBD"
Bot: "I found 12 properties within 10km of Harare CBD. Here are the closest ones:"
[Shows property results with distance information]
```

## Technical Implementation

### LocationClarificationCapability
The main capability that handles location clarification:

- **Priority**: 30 (higher than PropertySearchCapability)
- **Keywords**: Detects CBD-related and location-related keywords
- **Context**: Maintains conversation state across messages
- **Geospatial**: Uses PostGIS for accurate distance calculations

### Key Methods
- `can_handle()`: Detects if message needs location clarification
- `process()`: Main processing logic
- `_handle_initial_cbd_query()`: Processes initial CBD queries
- `_handle_cbd_selection()`: Handles user's CBD selection
- `_handle_location_response()`: Processes city responses
- `_search_properties_near_cbd()`: Searches properties within 10km radius

## Configuration

### Adding New CBD Locations
1. Use the Django admin interface to add new CBD locations
2. Or create a new management command for specific cities
3. Ensure coordinates are accurate (latitude, longitude)

### Modifying Search Radius
To change the 10km radius, modify the `_search_properties_near_cbd()` method:
```python
distance__lte=10000  # Change 10000 to desired radius in meters
```

### Adding New Cities
To support new cities, add them to the `zimbabwe_cities` list in `LocationClarificationCapability`:
```python
self.zimbabwe_cities = [
    "harare", "bulawayo", "mutare", "gweru", "kwekwe", "masvingo",
    "chitungwiza", "epworth", "ruwa", "chegutu", "kadoma", "marondera",
    "new_city"  # Add new cities here
]
```

## Testing

Run the test suite to verify functionality:
```bash
python manage.py test chatbot.test_location_clarification
```

The tests cover:
- CBD keyword detection
- Location clarification flow
- Property search with distance calculation
- Conversation state management

## Troubleshooting

### Common Issues

1. **No properties found**: Ensure properties have valid location coordinates
2. **Distance calculation errors**: Verify PostGIS is properly configured
3. **State not persisting**: Check that ConversationState is being created/updated correctly

### Debug Information
The capability includes extensive logging. Check the console output for:
- `🔍 LocationClarificationCapability processing: [message]`
- Distance calculation results
- Property search results

## Future Enhancements

Potential improvements:
1. **Dynamic radius**: Allow users to specify search radius
2. **Multiple CBDs per city**: Support for secondary CBD areas
3. **Transportation options**: Search based on walking/driving distance
4. **Amenity-based search**: Combine CBD proximity with amenity requirements
5. **Historical data**: Track popular CBD areas and search patterns 