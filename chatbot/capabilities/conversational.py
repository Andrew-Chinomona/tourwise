"""
Conversational Capability for MCP
Handles greetings, farewells, gratitude, and help queries
"""

import random
from typing import Dict, Any
from ..mcp_core import MCPCapability, MCPMessage, MCPResponse, MessageType


class ConversationalCapability(MCPCapability):
    """Handles conversational queries like greetings, farewells, etc."""

    def __init__(self):
        super().__init__(
            name="Conversational",
            description="Handles greetings, farewells, gratitude, and help queries"
        )

        # Define conversational patterns
        self.greetings = [
            "hello", "hi", "hey", "hie", "good morning", "good afternoon", "good evening",
            "how are you", "how's it going", "what's up", "sup", "yo"
        ]

        self.farewells = [
            "bye", "goodbye", "see you", "take care", "have a good day", "thanks", "thank you"
        ]

        self.gratitude = [
            "thanks", "thank you", "appreciate it", "awesome", "great", "perfect", "excellent"
        ]

        self.help_queries = [
            "how does this work", "what can you do", "help", "what are you", "who are you"
        ]

        # Response templates
        self.greeting_responses = [
            "Hello! 👋 I'm here to help you find your perfect property in Zimbabwe. What are you looking for today?",
            "Hi there! 😊 Welcome to Tourwise! I can help you find houses, apartments, and other properties. What's on your mind?",
            "Hey! 🏡 Great to see you! I'm your property search assistant. What type of property are you interested in?",
            "Good day! ✨ I'm here to make your property search easy and fun. What can I help you find today?",
            "Hello! 🌟 Welcome to Tourwise! I'm excited to help you discover amazing properties. What are you searching for?"
        ]

        self.farewell_responses = [
            "Goodbye! 👋 It was great helping you today. Feel free to come back anytime!",
            "Take care! 😊 Happy house hunting! Don't hesitate to return if you need more help.",
            "See you later! 🏡 I hope you found what you were looking for. Come back soon!",
            "Have a wonderful day! ✨ Thanks for using Tourwise. I'll be here when you need me!",
            "Bye for now! 🌟 Good luck with your property search. I'm always here to help!"
        ]

        self.gratitude_responses = [
            "You're very welcome! 😊 I'm glad I could help. Is there anything else you'd like to know?",
            "My pleasure! ✨ I love helping people find their perfect home. What else can I assist you with?",
            "Anytime! 🏡 I'm here to make your property search as smooth as possible. Need anything else?",
            "Happy to help! 🌟 That's what I'm here for. Feel free to ask me anything about properties!",
            "You're welcome! 😄 I enjoy helping people discover great properties. What's next on your list?"
        ]

    def can_handle(self, message: MCPMessage) -> bool:
        """Check if this capability can handle the message"""
        content_lower = message.content.lower().strip()

        # Check for greetings
        if any(greeting in content_lower for greeting in self.greetings):
            return True

        # Check for farewells
        if any(farewell in content_lower for farewell in self.farewells):
            return True

        # Check for gratitude
        if any(grat in content_lower for grat in self.gratitude):
            return True

        # Check for help queries
        if any(phrase in content_lower for phrase in self.help_queries):
            return True

        return False

    def process(self, message: MCPMessage, context: Dict[str, Any]) -> MCPResponse:
        """Process the conversational message"""
        content_lower = message.content.lower().strip()

        # Determine message type and response
        if any(greeting in content_lower for greeting in self.greetings):
            return MCPResponse(
                content=random.choice(self.greeting_responses),
                message_type=MessageType.GREETING,
                metadata={"is_conversational": True}
            )

        elif any(farewell in content_lower for farewell in self.farewells):
            return MCPResponse(
                content=random.choice(self.farewell_responses),
                message_type=MessageType.FAREWELL,
                metadata={"is_conversational": True}
            )

        elif any(grat in content_lower for grat in self.gratitude):
            return MCPResponse(
                content=random.choice(self.gratitude_responses),
                message_type=MessageType.GRATITUDE,
                metadata={"is_conversational": True}
            )

        elif any(phrase in content_lower for phrase in self.help_queries):
            return MCPResponse(
                content="I'm your AI property assistant! 🏡 I can help you find houses, apartments, and other properties in Zimbabwe. Just tell me what you're looking for - like 'houses in Harare' or 'apartments under $500' - and I'll search our database for you. What type of property interests you?",
                message_type=MessageType.HELP,
                metadata={"is_conversational": True}
            )

        # Fallback
        return MCPResponse(
            content="I'm here to help you find properties! What are you looking for?",
            message_type=MessageType.CONVERSATIONAL,
            metadata={"is_conversational": True}
        )

    def get_priority(self) -> int:
        """High priority for conversational queries"""
        return 10