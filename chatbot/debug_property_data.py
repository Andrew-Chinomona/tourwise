"""
Debug script to test property data retrieval
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourwise_Website.settings')
django.setup()

from listings.models import Property, PropertyImage
from chatbot.mcp_core import MCPMessage, MCPResponse, MessageType, MCPContext, get_mcp_orchestrator
from chatbot.capabilities.property_search import PropertySearchCapability


def test_property_data():
    """Test property data retrieval"""

    print("🔍 Testing Property Data Retrieval...")
    print("=" * 50)

    # Test 1: Check if we have any properties in the database
    properties = Property.objects.all()
    print(f"📊 Total properties in database: {properties.count()}")

    if properties.exists():
        # Get first property
        first_prop = properties.first()
        print(f"🏠 First property:")
        print(f"   ID: {first_prop.id}")
        print(f"   Title: {first_prop.title}")
        print(f"   City: {first_prop.city}")
        print(f"   Suburb: {first_prop.suburb}")
        print(f"   Price: {first_prop.price}")
        print(f"   Main Image: {first_prop.main_image}")

        # Check images
        images = PropertyImage.objects.filter(property=first_prop)
        print(f"   Images: {images.count()}")
        for img in images:
            print(f"     - {img.image}")

    # Test 2: Test the property search capability
    print("\n🔍 Testing Property Search Capability...")

    capability = PropertySearchCapability()

    # Test message
    test_message = MCPMessage(
        content="Show me houses in Harare",
        message_type=MessageType.PROPERTY_SEARCH
    )

    print(f"📝 Test message: '{test_message.content}'")
    print(f"🎯 Can handle: {capability.can_handle(test_message)}")

    if capability.can_handle(test_message):
        # Mock context
        class MockRequest:
            def __init__(self):
                self.user = None
                self.session = {}

        context = MCPContext(MockRequest())

        try:
            response = capability.process(test_message, context)
            print(f"✅ Response type: {response.message_type.value}")
            print(f"✅ Response content: {response.content}")

            if response.data and response.data.get("properties"):
                properties = response.data["properties"]
                print(f"✅ Properties returned: {len(properties)}")

                if properties:
                    first_prop = properties[0]
                    print(f"🏠 First property data:")
                    print(f"   Keys: {list(first_prop.keys())}")
                    print(f"   Title: {first_prop.get('title', 'NO TITLE')}")
                    print(f"   City: {first_prop.get('city', 'NO CITY')}")
                    print(f"   Suburb: {first_prop.get('suburb', 'NO SUBURB')}")
                    print(f"   Price: {first_prop.get('price', 'NO PRICE')}")
                    print(f"   Main Image: {first_prop.get('main_image', 'NO IMAGE')}")
            else:
                print("❌ No properties in response data")

        except Exception as e:
            print(f"❌ Error processing message: {str(e)}")
            import traceback
            traceback.print_exc()

    # Test 3: Test the MCP orchestrator
    print("\n🔍 Testing MCP Orchestrator...")

    orchestrator = get_mcp_orchestrator()
    print(f"📋 Registered capabilities: {[cap.name for cap in orchestrator.capabilities]}")

    # Test with orchestrator
    try:
        response = orchestrator.process_message("Show me houses in Harare", context)
        print(f"✅ Orchestrator response type: {response.message_type.value}")
        print(f"✅ Orchestrator response content: {response.content}")

        if response.data and response.data.get("properties"):
            properties = response.data["properties"]
            print(f"✅ Orchestrator properties: {len(properties)}")

            if properties:
                first_prop = properties[0]
                print(f"🏠 Orchestrator first property:")
                print(f"   Title: {first_prop.get('title', 'NO TITLE')}")
                print(f"   City: {first_prop.get('city', 'NO CITY')}")
                print(f"   Price: {first_prop.get('price', 'NO PRICE')}")
        else:
            print("❌ No properties from orchestrator")

    except Exception as e:
        print(f"❌ Error with orchestrator: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_property_data()