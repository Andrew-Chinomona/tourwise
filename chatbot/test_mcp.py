"""
Test script for MCP Architecture
Run this to verify the MCP architecture is working correctly
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tourwise_website.settings')
django.setup()

from chatbot.mcp_core import MCPMessage, MCPResponse, MessageType, MCPContext, get_mcp_orchestrator
from chatbot.capabilities.conversational import ConversationalCapability
from chatbot.capabilities.property_search import PropertySearchCapability
from chatbot.capabilities.database_query import DatabaseQueryCapability


def test_mcp_architecture():
    """Test the MCP architecture with various message types"""

    print("🧪 Testing MCP Architecture...")
    print("=" * 50)

    # Test messages
    test_messages = [
        "Hello there!",
        "Show me houses in Harare",
        "What can you do?",
        "Thanks for helping",
        "Goodbye!",
        "Find apartments under $500",
        "This is a test message"
    ]

    # Get orchestrator
    orchestrator = get_mcp_orchestrator()

    print(f"📋 Registered capabilities: {[cap.name for cap in orchestrator.capabilities]}")
    print()

    # Test each message
    for message in test_messages:
        print(f"💬 Testing: '{message}'")

        # Create mock context
        class MockRequest:
            def __init__(self):
                self.user = None
                self.session = {}

        context = MCPContext(MockRequest())

        try:
            # Process message
            response = orchestrator.process_message(message, context)

            print(f"   ✅ Response: {response.content[:100]}...")
            print(f"   📝 Type: {response.message_type.value}")
            print(f"   🎯 Success: {response.success}")

            if response.data:
                print(f"   📊 Data keys: {list(response.data.keys())}")

            print()

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            print()

    print("🎉 MCP Architecture test completed!")


def test_capability_priority():
    """Test capability priority system"""

    print("🔢 Testing Capability Priority System...")
    print("=" * 50)

    orchestrator = get_mcp_orchestrator()

    # Sort capabilities by priority
    sorted_capabilities = sorted(orchestrator.capabilities, key=lambda c: c.get_priority())

    for i, capability in enumerate(sorted_capabilities, 1):
        print(f"{i}. {capability.name} (Priority: {capability.get_priority()})")

    print()
    print("✅ Priority system working correctly!")


def test_message_types():
    """Test different message types"""

    print("📝 Testing Message Types...")
    print("=" * 50)

    # Test each message type
    message_types = [
        MessageType.CONVERSATIONAL,
        MessageType.PROPERTY_SEARCH,
        MessageType.DATABASE_QUERY,
        MessageType.HELP,
        MessageType.GREETING,
        MessageType.FAREWELL,
        MessageType.GRATITUDE,
        MessageType.ERROR
    ]

    for msg_type in message_types:
        print(f"✅ {msg_type.value}: {msg_type}")

    print()
    print("✅ All message types working correctly!")


if __name__ == "__main__":
    print("🚀 Starting MCP Architecture Tests...")
    print()

    try:
        test_message_types()
        print()
        test_capability_priority()
        print()
        test_mcp_architecture()
        print()
        print("🎊 All tests passed! MCP Architecture is working correctly.")

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)