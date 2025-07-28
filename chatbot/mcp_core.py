"""
MCP (Model Context Protocol) Core Architecture
Handles message routing, capability management, and response orchestration
"""

import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from django.http import HttpRequest
from .models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of messages that can be processed"""
    CONVERSATIONAL = "conversational"
    PROPERTY_SEARCH = "property_search"
    DATABASE_QUERY = "database_query"
    HELP = "help"
    GREETING = "greeting"
    FAREWELL = "farewell"
    GRATITUDE = "gratitude"
    ERROR = "error"

@dataclass
class MCPMessage:
    """Standardized message format for MCP"""
    content: str
    message_type: MessageType
    metadata: Dict[str, Any] = None
    session_id: Optional[str] = None
    user_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'message_type': self.message_type.value,
            'metadata': self.metadata or {},
            'session_id': self.session_id,
            'user_id': self.user_id
        }

@dataclass
class MCPResponse:
    """Standardized response format for MCP"""
    content: str
    message_type: MessageType
    data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'message_type': self.message_type.value,
            'data': self.data,
            'metadata': self.metadata or {},
            'success': self.success,
            'error_message': self.error_message
        }

class MCPCapability:
    """Base class for MCP capabilities"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def can_handle(self, message: MCPMessage) -> bool:
        """Override to determine if this capability can handle the message"""
        raise NotImplementedError

    def process(self, message: MCPMessage, context: Dict[str, Any]) -> MCPResponse:
        """Override to process the message and return a response"""
        raise NotImplementedError

    def get_priority(self) -> int:
        """Override to set processing priority (lower = higher priority)"""
        return 100

class MCPContext:
    """Manages conversation context and session state"""

    def __init__(self, request: HttpRequest):
        self.request = request
        self.session = None
        self.user = request.user if hasattr(request, 'user') else None
        self.context_data = {}

    def get_or_create_session(self) -> ChatSession:
        """Get or create a chat session"""
        from .views import get_or_create_session
        self.session = get_or_create_session(self.request)
        return self.session

    def save_message(self, sender: str, content: str, message_type: str = 'text', metadata: Dict[str, Any] = None) -> ChatMessage:
        """Save a message to the database"""
        from .views import save_message
        return save_message(self.session, sender, content, message_type, metadata)

    def get_context_data(self, key: str, default: Any = None) -> Any:
        """Get context data"""
        return self.context_data.get(key, default)

    def set_context_data(self, key: str, value: Any):
        """Set context data"""
        self.context_data[key] = value

class MCPOrchestrator:
    """Main orchestrator for MCP message processing"""

    def __init__(self):
        self.capabilities: List[MCPCapability] = []
        self._register_default_capabilities()

    def register_capability(self, capability: MCPCapability):
        """Register a new capability"""
        self.capabilities.append(capability)
        # Sort by priority
        self.capabilities.sort(key=lambda c: c.get_priority())
        logger.info(f"Registered MCP capability: {capability.name}")

    def _register_default_capabilities(self):
        """Register default capabilities"""
        from .capabilities.conversational import ConversationalCapability
        from .capabilities.property_search import PropertySearchCapability
        from .capabilities.database_query import DatabaseQueryCapability
        from .capabilities.location_clarification import LocationClarificationCapability

        self.register_capability(ConversationalCapability())
        self.register_capability(LocationClarificationCapability())  # Higher priority for location clarification
        self.register_capability(PropertySearchCapability())
        self.register_capability(DatabaseQueryCapability())

    def process_message(self, content: str, context: MCPContext) -> MCPResponse:
        """Process a message through all registered capabilities"""
        try:
            # Create MCP message
            message = MCPMessage(
                content=content,
                message_type=MessageType.CONVERSATIONAL,  # Default, will be updated by capabilities
                session_id=context.session.session_id if context.session else None,
                user_id=context.user.id if context.user and context.user.is_authenticated else None
            )

            # Find the first capability that can handle this message
            print(f"🔍 MCP Orchestrator checking {len(self.capabilities)} capabilities for: '{content}'")
            for capability in self.capabilities:
                print(f"🔍 Checking capability: {capability.name}")
                can_handle = capability.can_handle(message)
                print(f"🔍 {capability.name} can handle: {can_handle}")
                if can_handle:
                    print(f"🔍 Processing with capability: {capability.name}")
                    logger.info(f"Processing message with capability: {capability.name}")

                    # Pass session in context data for capabilities that need it
                    context_data = context.context_data.copy()
                    context_data['session'] = context.session
                    response = capability.process(message, context_data)

                    # Save the message and response to database
                    if context.session:
                        context.save_message('user', content)
                        context.save_message('bot', response.content, response.message_type.value, response.metadata)

                    return response

            # No capability found, return error response
            logger.warning(f"No capability found to handle message: {content}")
            return MCPResponse(
                content="I'm not sure how to help with that. Could you try rephrasing your question?",
                message_type=MessageType.ERROR,
                success=False,
                error_message="No capability found"
            )

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return MCPResponse(
                content="Something went wrong. Please try again.",
                message_type=MessageType.ERROR,
                success=False,
                error_message=str(e)
            )

# Global orchestrator instance
mcp_orchestrator = MCPOrchestrator()

def get_mcp_orchestrator() -> MCPOrchestrator:
    """Get the global MCP orchestrator instance"""
    return mcp_orchestrator 