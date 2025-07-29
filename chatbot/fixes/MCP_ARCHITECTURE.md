# MCP (Model Context Protocol) Architecture

## Overview

The Tourwise chatbot has been refactored to use a flexible MCP (Model Context Protocol) architecture that provides:

- **Modular Design**: Separate capabilities for different functionalities
- **Easy Extensibility**: Simple way to add new capabilities
- **Backward Compatibility**: Existing frontend and UI remain unchanged
- **Clean Separation of Concerns**: Each capability handles specific types of queries
- **Priority-based Routing**: Messages are routed to the most appropriate capability

## Architecture Components

### 1. MCP Core (`mcp_core.py`)

The core of the MCP architecture containing:

- **MCPMessage**: Standardized message format
- **MCPResponse**: Standardized response format
- **MCPCapability**: Base class for all capabilities
- **MCPContext**: Manages conversation context and session state
- **MCPOrchestrator**: Routes messages to appropriate capabilities

### 2. Capabilities

Individual modules that handle specific types of queries:

- **ConversationalCapability**: Handles greetings, farewells, gratitude, and help queries
- **PropertySearchCapability**: Handles property-related queries using SQL
- **DatabaseQueryCapability**: Fallback for general database queries

### 3. Response Formatter (`response_formatter.py`)

Converts MCP responses to the format expected by the existing frontend.

### 4. Capability Registry (`capability_registry.py`)

Provides a clean interface for registering and managing capabilities.

## How It Works

1. **Message Reception**: User message is received by the view
2. **Context Creation**: MCPContext is created with session and user information
3. **Capability Routing**: Orchestrator finds the first capability that can handle the message
4. **Message Processing**: Selected capability processes the message
5. **Response Formatting**: Response is formatted for the frontend
6. **Database Storage**: Message and response are saved to the database

## Adding New Capabilities

### Step 1: Create a New Capability

Create a new file in `capabilities/` directory:

```python
from ..mcp_core import MCPCapability, MCPMessage, MCPResponse, MessageType

class MyNewCapability(MCPCapability):
    def __init__(self):
        super().__init__(
            name="MyNewCapability",
            description="Handles specific type of queries"
        )
        
        # Define patterns this capability can handle
        self.patterns = ["keyword1", "keyword2"]
    
    def can_handle(self, message: MCPMessage) -> bool:
        """Check if this capability can handle the message"""
        content_lower = message.content.lower().strip()
        return any(pattern in content_lower for pattern in self.patterns)
    
    def process(self, message: MCPMessage, context: Dict[str, Any]) -> MCPResponse:
        """Process the message and return a response"""
        # Your processing logic here
        return MCPResponse(
            content="Your response here",
            message_type=MessageType.CONVERSATIONAL,
            metadata={"custom_data": "value"}
        )
    
    def get_priority(self) -> int:
        """Set processing priority (lower = higher priority)"""
        return 50
```

### Step 2: Register the Capability

Add the capability to the orchestrator in `mcp_core.py`:

```python
def _register_default_capabilities(self):
    """Register default capabilities"""
    from .capabilities.conversational import ConversationalCapability
    from .capabilities.property_search import PropertySearchCapability
    from .capabilities.database_query import DatabaseQueryCapability
    from .capabilities.my_new_capability import MyNewCapability  # Add this
    
    self.register_capability(ConversationalCapability())
    self.register_capability(PropertySearchCapability())
    self.register_capability(DatabaseQueryCapability())
    self.register_capability(MyNewCapability())  # Add this
```

### Step 3: Update Response Formatter (if needed)

If your capability returns a new message type, update `response_formatter.py`:

```python
def format_for_frontend(mcp_response: MCPResponse) -> Dict[str, Any]:
    # ... existing code ...
    
    elif mcp_response.message_type == MessageType.MY_NEW_TYPE:
        return {
            "friendly_message": mcp_response.content,
            "result": mcp_response.data,
            "custom_field": mcp_response.metadata.get("custom_data")
        }
```

## Message Types

The system supports these message types:

- `CONVERSATIONAL`: General conversational responses
- `PROPERTY_SEARCH`: Property search results
- `DATABASE_QUERY`: General database queries
- `HELP`: Help and information responses
- `GREETING`: Greeting responses
- `FAREWELL`: Farewell responses
- `GRATITUDE`: Gratitude responses
- `ERROR`: Error responses

## Priority System

Capabilities are processed in priority order (lower number = higher priority):

- **10**: ConversationalCapability (highest priority)
- **30**: ExampleCapability
- **50**: PropertySearchCapability
- **100**: DatabaseQueryCapability (fallback)

## Context Management

The `MCPContext` class provides:

- Session management
- User information
- Context data storage
- Database operations

## Backward Compatibility

The new architecture maintains full backward compatibility:

- Existing frontend code works unchanged
- Same API endpoints
- Same response format
- Same database schema
- Same UI/UX

## Benefits of MCP Architecture

1. **Modularity**: Each capability is self-contained
2. **Extensibility**: Easy to add new capabilities
3. **Maintainability**: Clear separation of concerns
4. **Testability**: Each capability can be tested independently
5. **Scalability**: New features can be added without modifying existing code
6. **Flexibility**: Capabilities can be enabled/disabled easily

## Example Use Cases

### Adding Image Analysis
```python
class ImageAnalysisCapability(MCPCapability):
    def can_handle(self, message: MCPMessage) -> bool:
        return "analyze image" in message.content.lower()
    
    def process(self, message: MCPMessage, context: Dict[str, Any]) -> MCPResponse:
        # Use computer vision APIs
        return MCPResponse(...)
```

### Adding External API Integration
```python
class WeatherCapability(MCPCapability):
    def can_handle(self, message: MCPMessage) -> bool:
        return "weather" in message.content.lower()
    
    def process(self, message: MCPMessage, context: Dict[str, Any]) -> MCPResponse:
        # Call weather API
        return MCPResponse(...)
```

### Adding Multi-step Workflows
```python
class WorkflowCapability(MCPCapability):
    def process(self, message: MCPMessage, context: Dict[str, Any]) -> MCPResponse:
        # Store workflow state in context
        context["workflow_step"] = "step1"
        return MCPResponse(...)
```

## Testing

Each capability can be tested independently:

```python
def test_conversational_capability():
    capability = ConversationalCapability()
    message = MCPMessage(content="hello", message_type=MessageType.CONVERSATIONAL)
    context = {}
    
    assert capability.can_handle(message)
    response = capability.process(message, context)
    assert response.message_type == MessageType.GREETING
```

## Migration Guide

The migration from the old architecture was seamless:

1. **No frontend changes required**
2. **No database changes required**
3. **Same API endpoints**
4. **Enhanced functionality**

## Future Enhancements

Potential areas for expansion:

1. **Plugin System**: Dynamic capability loading
2. **Configuration Management**: Runtime capability configuration
3. **Analytics**: Capability usage tracking
4. **A/B Testing**: Different capability versions
5. **Machine Learning**: Dynamic capability selection

## Support

For questions or issues with the MCP architecture:

1. Check the example capability in `capabilities/example_capability.py`
2. Review the existing capabilities for patterns
3. Test your capability thoroughly before deployment
4. Follow the priority system guidelines 