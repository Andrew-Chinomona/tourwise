"""
Database Query Capability for MCP
Handles general database queries as a fallback capability
"""

import logging
from typing import Dict, Any
from ..mcp_core import MCPCapability, MCPMessage, MCPResponse, MessageType
from ..nl_query_engine import run_nl_query

logger = logging.getLogger(__name__)


class DatabaseQueryCapability(MCPCapability):
    """Handles general database queries as a fallback"""

    def __init__(self):
        super().__init__(
            name="DatabaseQuery",
            description="Handles general database queries using the existing query engine"
        )

    def can_handle(self, message: MCPMessage) -> bool:
        """This capability handles all messages that haven't been handled by others"""
        # This is a fallback capability, so it should handle everything
        # The priority system ensures it only gets called if no other capability handles it
        return True

    def process(self, message: MCPMessage, context: Dict[str, Any]) -> MCPResponse:
        """Process the database query"""
        try:
            # Use the existing query engine
            result = run_nl_query(message.content)

            # Handle conversational responses
            if isinstance(result, dict) and result.get("is_conversational"):
                return MCPResponse(
                    content=result.get("chat_response", "Hello!"),
                    message_type=MessageType.CONVERSATIONAL,
                    metadata={"is_conversational": True}
                )

            # Handle SQL results
            if hasattr(result, 'response') and result.response:
                # Convert to standard format
                properties = []
                if isinstance(result.response, list):
                    properties = result.response

                friendly_message = result.metadata.get("chat_response", "Here is what I found.")

                return MCPResponse(
                    content=friendly_message,
                    message_type=MessageType.DATABASE_QUERY,
                    data={"properties": properties},
                    metadata={
                        "property_count": len(properties),
                        "sql_query": result.metadata.get("sql_query", ""),
                        "properties": properties  # For backward compatibility
                    }
                )

            # Fallback response
            return MCPResponse(
                content="I found some information, but it might not be exactly what you're looking for. Could you try rephrasing your question?",
                message_type=MessageType.DATABASE_QUERY,
                data={"properties": []},
                metadata={"property_count": 0}
            )

        except Exception as e:
            logger.error(f"Error in database query: {str(e)}", exc_info=True)
            return MCPResponse(
                content="I encountered an error while processing your request. Please try again.",
                message_type=MessageType.ERROR,
                success=False,
                error_message=str(e)
            )

    def get_priority(self) -> int:
        """Low priority - this is a fallback capability"""
        return 100