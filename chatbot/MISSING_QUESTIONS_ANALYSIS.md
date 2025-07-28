# Missing Questions Analysis

This document analyzes what types of questions users might ask that are NOT currently handled by the chatbot and provides solutions for adding them.

## 🔍 **Current Coverage Analysis**

### **✅ What's Already Handled:**

1. **Conversational** - Greetings, farewells, help requests
2. **Location Clarification** - CBD searches with follow-up questions
3. **Property Search** - Basic property queries
4. **Statistics** - Property counts, averages, ranges
5. **Comparisons** - House vs apartment, buy vs rent
6. **Recommendations** - Featured/top properties
7. **Amenities** - Available facilities
8. **Pricing** - General pricing information
9. **Location Info** - Safe areas, neighborhoods
10. **Property Types** - Different property categories
11. **Timing** - Best times to buy/rent
12. **Contact** - How to contact owners
13. **Legal** - Basic legal information
14. **Financial** - Mortgage and financing info
15. **Maintenance** - Maintenance and utility costs

## ❌ **Potentially Missing Question Types**

### **1. Multi-Language Support**
**Questions not handled:**
- "Ndoda dzimba muHarare" (Shona)
- "I need houses in Harare" (English variations)
- "Je veux des maisons à Harare" (French)

**Solution:** Add language detection capability
```python
class MultiLanguageCapability(MCPCapability):
    def __init__(self):
        self.languages = {
            'shona': ['ndoda', 'dzimba', 'mumba'],
            'french': ['maison', 'appartement', 'propriété'],
            'english': ['house', 'apartment', 'property']
        }
```

### **2. Advanced Filtering**
**Questions not handled:**
- "Show me properties with 3+ bedrooms AND 2+ bathrooms AND under $50k"
- "Houses with garden AND pool AND parking"
- "Apartments built after 2020 with modern amenities"

**Solution:** Enhance PropertySearchCapability with advanced filtering
```python
def _parse_advanced_filters(self, content: str) -> Dict[str, Any]:
    """Parse complex filter combinations"""
    filters = {}
    # Parse AND/OR logic
    # Handle multiple conditions
    return filters
```

### **3. Market Analysis**
**Questions not handled:**
- "Show me price trends over the last year"
- "Which areas are appreciating fastest?"
- "What's the market forecast for Harare?"
- "Compare prices between different suburbs"

**Solution:** Add MarketAnalysisCapability
```python
class MarketAnalysisCapability(MCPCapability):
    def _analyze_price_trends(self):
        """Analyze historical price data"""
        
    def _compare_market_performance(self):
        """Compare different areas"""
```

### **4. Investment Analysis**
**Questions not handled:**
- "Calculate ROI for this property"
- "What's the rental yield?"
- "Show me properties with highest rental income"
- "Investment properties with good returns"

**Solution:** Add InvestmentAnalysisCapability
```python
class InvestmentAnalysisCapability(MCPCapability):
    def _calculate_roi(self, property_data):
        """Calculate return on investment"""
        
    def _analyze_rental_yield(self, property_data):
        """Analyze rental yield potential"""
```

### **5. Virtual Tours & Media**
**Questions not handled:**
- "Show me virtual tours"
- "More photos of this property"
- "Video walkthrough"
- "360-degree view"

**Solution:** Add MediaCapability
```python
class MediaCapability(MCPCapability):
    def _handle_virtual_tour_request(self):
        """Handle virtual tour requests"""
        
    def _handle_photo_gallery_request(self):
        """Handle photo gallery requests"""
```

### **6. Neighborhood Information**
**Questions not handled:**
- "What's the crime rate in this area?"
- "School ratings nearby"
- "Public transport routes"
- "Shopping centers within 1km"

**Solution:** Add NeighborhoodInfoCapability
```python
class NeighborhoodInfoCapability(MCPCapability):
    def _get_crime_data(self, location):
        """Get crime statistics"""
        
    def _get_school_ratings(self, location):
        """Get nearby school information"""
```

### **7. Property History**
**Questions not handled:**
- "How long has this property been on the market?"
- "Previous sale prices"
- "Property history and renovations"
- "Days on market statistics"

**Solution:** Add PropertyHistoryCapability
```python
class PropertyHistoryCapability(MCPCapability):
    def _get_property_history(self, property_id):
        """Get property listing history"""
        
    def _get_market_duration(self, property_id):
        """Get days on market"""
```

### **8. User Preferences & Personalization**
**Questions not handled:**
- "Remember my preferences"
- "Show me properties like the ones I viewed"
- "Recommendations based on my search history"
- "Save my favorite properties"

**Solution:** Add PersonalizationCapability
```python
class PersonalizationCapability(MCPCapability):
    def _save_user_preferences(self, user_id, preferences):
        """Save user preferences"""
        
    def _get_personalized_recommendations(self, user_id):
        """Get personalized recommendations"""
```

### **9. Advanced Search Operators**
**Questions not handled:**
- "Properties within 5km of CBD"
- "Houses with price between $30k and $60k"
- "Apartments available from next month"
- "Properties with specific floor plans"

**Solution:** Enhance search with advanced operators
```python
def _parse_advanced_operators(self, content: str):
    """Parse advanced search operators"""
    # Handle distance operators
    # Handle price ranges
    # Handle date ranges
    # Handle specific criteria
```

### **10. Real-time Information**
**Questions not handled:**
- "Is this property still available?"
- "When was this last updated?"
- "Show me new listings from today"
- "Recently sold properties"

**Solution:** Add RealTimeCapability
```python
class RealTimeCapability(MCPCapability):
    def _check_availability(self, property_id):
        """Check if property is still available"""
        
    def _get_recent_listings(self, hours=24):
        """Get recently added listings"""
```

## 🛠️ **Implementation Priority**

### **High Priority (Implement First):**
1. **Advanced Filtering** - Most requested feature
2. **Multi-Language Support** - Important for Zimbabwe market
3. **Real-time Information** - Critical for user trust

### **Medium Priority:**
4. **Investment Analysis** - Valuable for serious buyers
5. **Neighborhood Information** - Helps with decision making
6. **Property History** - Useful for market understanding

### **Low Priority:**
7. **Market Analysis** - Complex to implement
8. **Virtual Tours** - Requires additional infrastructure
9. **Personalization** - Nice to have feature
10. **Advanced Search Operators** - Can be added incrementally

## 📋 **Quick Implementation Guide**

### **Step 1: Add New Capability**
```python
# Create new capability file
class NewCapability(MCPCapability):
    def __init__(self):
        super().__init__(
            name="NewCapability",
            description="Handles new type of queries"
        )
        
    def can_handle(self, message: MCPMessage) -> bool:
        # Add pattern matching logic
        return True
        
    def process(self, message: MCPMessage, context: Dict[str, Any]) -> MCPResponse:
        # Add processing logic
        return MCPResponse(...)
```

### **Step 2: Register in MCP Core**
```python
# In mcp_core.py
from .capabilities.new_capability import NewCapability

def _register_default_capabilities(self):
    # Add to the list
    self.register_capability(NewCapability())
```

### **Step 3: Add Database Models (if needed)**
```python
# In models.py
class NewModel(models.Model):
    # Add required fields
    pass
```

### **Step 4: Create Migrations**
```bash
python manage.py makemigrations chatbot
python manage.py migrate
```

### **Step 5: Test**
```python
# Add tests to test_new_capability.py
def test_new_capability():
    # Test the new functionality
    pass
```

## 🎯 **Recommendation**

Start with **Advanced Filtering** as it's the most commonly requested feature and will significantly improve user experience. Then add **Multi-Language Support** to better serve the Zimbabwean market.

The current system is already quite comprehensive, but these additions will make it even more powerful and user-friendly! 