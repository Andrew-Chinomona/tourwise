# Complete User Questions Guide

This guide shows all the types of questions users can ask the Tourwise chatbot and how they're handled by the system.

## 🎯 **Question Categories & Examples**

### **1. Conversational Questions** (Priority: 10)
**Handled by:** `ConversationalCapability`

#### **Greetings:**
- "Hello"
- "Hi there"
- "Good morning"
- "How are you?"
- "What's up?"

#### **Farewells:**
- "Goodbye"
- "See you later"
- "Thanks, bye"
- "Take care"

#### **Gratitude:**
- "Thank you"
- "Thanks a lot"
- "Appreciate it"
- "Perfect, thanks"

#### **Help Requests:**
- "How does this work?"
- "What can you do?"
- "Help"
- "Who are you?"

---

### **2. Location Clarification Questions** (Priority: 30)
**Handled by:** `LocationClarificationCapability`

#### **CBD Searches:**
- "I am looking for houses near the CBD"
- "Show me apartments close to the CBD"
- "Properties near the central business district"
- "Houses in the CBD area"

#### **Location-Based Queries:**
- "Properties near Harare CBD"
- "Apartments close to Bulawayo CBD"
- "Houses in the CBD in Mutare"

#### **Follow-up Responses:**
- "Harare" (when asked for city)
- "Bulawayo CBD" (when multiple CBDs available)

---

### **3. Comprehensive Questions** (Priority: 40)
**Handled by:** `ComprehensiveHandlerCapability`

#### **📊 Statistics Questions:**
- "How many properties do you have?"
- "What's the average price of houses?"
- "Show me property statistics"
- "What's the total number of properties?"
- "What's the price range?"
- "What are the most expensive properties?"
- "Show me the cheapest properties"
- "What's the average number of bedrooms?"
- "What are the popular areas?"
- "Give me a property count"

#### **🔄 Comparison Questions:**
- "Compare houses vs apartments"
- "What's the difference between buying and renting?"
- "Which is better: house or apartment?"
- "Houses vs apartments"
- "Show me similar properties"
- "What are alternative properties?"

#### **⭐ Recommendation Questions:**
- "Recommend some properties"
- "Suggest good properties"
- "Show me the best properties"
- "What are the top properties?"
- "Show me featured properties"
- "What are trending properties?"
- "Show me popular properties"

#### **🏠 Amenity Questions:**
- "Properties with wifi"
- "Houses with parking"
- "Apartments with pool"
- "What amenities are available?"
- "What facilities do you have?"
- "Properties with gym"

#### **💰 Pricing Questions:**
- "What's the price per month?"
- "What are the rental rates?"
- "Buying vs renting comparison"
- "Investment properties"
- "Return on investment"
- "Property valuation"
- "Market prices"

#### **📍 Location Questions:**
- "What are the safe areas?"
- "Best neighborhoods"
- "Schools nearby"
- "Transportation options"
- "Shopping centers"
- "Hospitals nearby"
- "Crime rate information"

#### **🏘️ Property Type Questions:**
- "House vs apartment comparison"
- "Difference between house and apartment"
- "Which property type should I choose?"
- "Pros and cons of houses"
- "Pros and cons of apartments"

#### **⏰ Timing Questions:**
- "When is the best time to buy?"
- "Seasonal prices"
- "Market trends"
- "Price fluctuations"
- "Busy season for properties"

#### **📞 Contact Questions:**
- "How do I contact the owner?"
- "Agent information"
- "Viewing appointment"
- "Schedule a visit"
- "Contact details"

#### **⚖️ Legal Questions:**
- "Legal requirements"
- "Documents needed"
- "Rental agreement"
- "Tenant rights"
- "Landlord obligations"
- "Property tax"

#### **💳 Financial Questions:**
- "Mortgage options"
- "Financing available"
- "Down payment"
- "Interest rates"
- "Loan terms"
- "Payment plans"

#### **🔧 Maintenance Questions:**
- "Maintenance costs"
- "Utilities included"
- "Repair responsibilities"
- "Property condition"
- "Renovation costs"

---

### **4. Property Search Questions** (Priority: 50)
**Handled by:** `PropertySearchCapability`

#### **Basic Property Searches:**
- "Show me houses"
- "I need apartments"
- "Properties for rent"
- "Houses for sale"
- "Find me a home"

#### **Specific Searches:**
- "Houses in Harare"
- "Apartments in Bulawayo"
- "Properties under $500"
- "3 bedroom houses"
- "Houses with 2 bathrooms"
- "Cheap apartments"
- "Luxury properties"

#### **Detailed Searches:**
- "Modern houses in Harare"
- "Traditional apartments"
- "Affordable properties"
- "Expensive houses"
- "New properties"
- "Old houses"

---

### **5. Database Query Questions** (Priority: 100)
**Handled by:** `DatabaseQueryCapability` (Fallback)

#### **Complex Queries:**
- "Properties built after 2020"
- "Houses with garden and pool"
- "Apartments near shopping centers"
- "Properties with specific amenities"
- "Custom search queries"

---

## 🔄 **Question Processing Flow**

```
User Input → MCP Orchestrator
    ↓
Check Capabilities by Priority:
1. Conversational (10) - Greetings, farewells, help
2. Location Clarification (30) - CBD and location queries
3. Comprehensive Handler (40) - Statistics, comparisons, etc.
4. Property Search (50) - Basic property searches
5. Database Query (100) - Fallback for everything else
```

---

## 📝 **Example Conversations**

### **Example 1: CBD Search with Follow-up**
```
User: "I am looking for houses near the CBD"
Bot: "I'd be happy to help you find properties near the CBD! Which city are you looking in? (e.g., Harare, Bulawayo, Mutare, etc.)"

User: "Harare"
Bot: "I found 15 properties within 10km of Harare CBD. Here are the closest ones:"
[Shows property results with distance information]
```

### **Example 2: Statistics Query**
```
User: "How many properties do you have?"
Bot: "📊 Property Statistics:
• Total properties: 150
• Average price: $45,000
• Price range: $15,000 - $200,000
• Average bedrooms: 2.5

🏠 Property Types:
• House: 80
• Apartment: 45
• Airbnb: 25

🌍 Top Cities:
• Harare: 60
• Bulawayo: 35
• Mutare: 25"
```

### **Example 3: Comparison Query**
```
User: "Compare houses vs apartments"
Bot: "🏠 House vs Apartment Comparison:

Houses:
• Average price: $55,000
• Average bedrooms: 3.2
• Available: 80

Apartments:
• Average price: $35,000
• Average bedrooms: 2.1
• Available: 45

Key Differences:
• Houses typically offer more space and privacy
• Apartments often have lower maintenance costs
• Houses may have higher utility costs
• Apartments often include amenities like gyms/pools"
```

### **Example 4: Recommendation Query**
```
User: "Recommend some properties"
Bot: "⭐ Recommended Properties:

🏠 Modern House in Avondale
📍 Avondale, Harare
💰 $75,000
🛏️ 3 bed, 2 bath

🏠 Luxury Apartment in CBD
📍 Harare CBD, Harare
💰 $45,000
🛏️ 2 bed, 1 bath

These are some of our top picks! Would you like me to search for specific criteria?"
```

---

## 🛠️ **How to Add New Question Types**

### **1. Add New Patterns**
In `ComprehensiveHandlerCapability`, add new pattern lists:

```python
self.new_category_patterns = [
    r"pattern.*one",
    r"pattern.*two",
    r"pattern.*three"
]
```

### **2. Add Handler Method**
```python
def _handle_new_category_query(self, content: str) -> MCPResponse:
    """Handle new category queries"""
    response = [
        "Your response here",
        "More response content"
    ]
    
    return MCPResponse(
        content="\n".join(response),
        message_type=MessageType.CONVERSATIONAL,
        metadata={"query_type": "new_category"}
    )
```

### **3. Update Process Method**
Add the new handler to the `process` method:

```python
elif self._matches_patterns(content_lower, self.new_category_patterns):
    return self._handle_new_category_query(content_lower)
```

### **4. Update Can Handle Method**
Add the new patterns to the `can_handle` method.

---

## 🎯 **Best Practices**

### **1. Pattern Design**
- Use regex patterns that are specific but flexible
- Consider variations in user language
- Test patterns with different phrasings

### **2. Response Formatting**
- Use emojis and formatting for readability
- Structure responses with clear sections
- Provide actionable next steps

### **3. Error Handling**
- Always include try-catch blocks
- Provide helpful fallback responses
- Log errors for debugging

### **4. Performance**
- Keep database queries efficient
- Use appropriate indexes
- Limit result sets when possible

---

## 🔍 **Testing Questions**

Here are some test questions to verify all capabilities work:

### **Conversational:**
- "Hello"
- "How are you?"
- "What can you do?"
- "Thank you"
- "Goodbye"

### **Location Clarification:**
- "I want houses near the CBD"
- "Properties close to the CBD in Harare"
- "Apartments near Bulawayo CBD"

### **Comprehensive:**
- "How many properties do you have?"
- "Compare houses vs apartments"
- "Recommend some properties"
- "What amenities are available?"
- "What are the safe areas?"

### **Property Search:**
- "Show me houses"
- "Apartments in Harare"
- "Properties under $50,000"

### **Database Query (Fallback):**
- "Properties with specific features"
- "Complex search queries"

This comprehensive system ensures that virtually any question a user might ask about properties in Zimbabwe can be handled appropriately! 