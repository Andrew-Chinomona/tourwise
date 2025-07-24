"""
Example Capability for MCP
Demonstrates how to create a new capability for the MCP architecture
"""

import logging
from typing import Dict, Any
from ..mcp_core import MCPCapability, MCPMessage, MCPResponse, MessageType

logger = logging.getLogger(__name__)


class ExampleCapability(MCPCapability):
    """Example capability that demonstrates the MCP architecture"""

    def __init__(self):
        super().__init__(
            name="Example",
            description="Example capability for demonstration purposes"
        )

        # Define patterns this capability can handle
        self.example_patterns = [
            "example", "demo", "test", "show me how", "demonstrate"
        ]

    def can_handle(self, message: MCPMessage) -> bool:
        """Check if this capability can handle the message"""
        content_lower = message.content.lower().strip()
        return any(pattern in content_lower for pattern in self.example_patterns)

    def process(self, message: MCPMessage, context: Dict[str, Any]) -> MCPResponse:
        """Process the example message"""
        content_lower = message.content.lower().strip()

        if "example" in content_lower or "demo" in content_lower:
            return MCPResponse(
                content="This is an example of how easy it is to add new capabilities to the MCP architecture! 🚀\n\nYou can create new capabilities by:\n1. Creating a new class that inherits from MCPCapability\n2. Implementing can_handle() and process() methods\n3. Registering the capability with the registry\n\nThis makes the chatbot highly extensible and modular!",
                message_type=MessageType.CONVERSATIONAL,
                metadata={"is_example": True, "capability_name": self.name}
            )

        elif "test" in content_lower:
            return MCPResponse(
                content="Testing the MCP architecture! ✅\n\nThis response shows that the capability system is working correctly. You can add more sophisticated capabilities for:\n- Image analysis\n- External API calls\n- Complex data processing\n- Multi-step workflows\n\nThe possibilities are endless!",
                message_type=MessageType.CONVERSATIONAL,
                metadata={"is_test": True, "capability_name": self.name}
            )

        else:
            return MCPResponse(
                content="This is a demonstration of the MCP capability system. Try asking for an 'example' or 'demo' to see more!",
                message_type=MessageType.CONVERSATIONAL,
                metadata={"is_demo": True, "capability_name": self.name}
            )

    def get_priority(self) -> int:
        """Medium priority for example capability"""
        return 30

# Example of how to register this capability
# from chatbot.capability_registry import register_capability
# register_capability(ExampleCapability()) 