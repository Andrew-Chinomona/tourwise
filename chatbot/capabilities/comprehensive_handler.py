"""
Comprehensive Handler Capability for MCP
Handles all types of user questions that might not be covered by other capabilities
"""

import logging
import re
from typing import Dict, Any, List, Optional
from django.db.models import Q, Avg, Min, Max, Count
from listings.models import Property, Amenity, Currency
from ..mcp_core import MCPCapability, MCPMessage, MCPResponse, MessageType

logger = logging.getLogger(__name__)


class ComprehensiveHandlerCapability(MCPCapability):
    """Handles comprehensive queries including statistics, comparisons, recommendations, etc."""

    def __init__(self):
        super().__init__(
            name="ComprehensiveHandler",
            description="Handles statistics, comparisons, recommendations, and other complex queries"
        )

        # Question patterns that this capability can handle
        self.statistics_patterns = [
            r"how many.*properties",
            r"what.*average.*price",
            r"statistics.*properties",
            r"total.*properties",
            r"price.*range",
            r"most.*expensive",
            r"cheapest.*properties",
            r"average.*bedrooms",
            r"popular.*areas",
            r"property.*count"
        ]

        self.comparison_patterns = [
            r"compare.*properties",
            r"difference.*between",
            r"which.*better",
            r"vs\.",
            r"versus",
            r"similar.*properties",
            r"alternative.*properties"
        ]

        self.recommendation_patterns = [
            r"recommend.*properties",
            r"suggest.*properties",
            r"best.*properties",
            r"top.*properties",
            r"featured.*properties",
            r"trending.*properties",
            r"popular.*properties"
        ]

        self.amenity_patterns = [
            r"properties.*with.*wifi",
            r"properties.*with.*parking",
            r"properties.*with.*pool",
            r"amenities.*available",
            r"what.*amenities",
            r"facilities.*available"
        ]

        self.pricing_patterns = [
            r"price.*per.*month",
            r"rental.*rates",
            r"buying.*vs.*renting",
            r"investment.*properties",
            r"return.*on.*investment",
            r"property.*valuation",
            r"market.*prices"
        ]

        self.location_patterns = [
            r"safe.*areas",
            r"best.*neighborhoods",
            r"schools.*nearby",
            r"transportation.*options",
            r"shopping.*centers",
            r"hospitals.*nearby",
            r"crime.*rate"
        ]

        self.property_type_patterns = [
            r"house.*vs.*apartment",
            r"difference.*house.*apartment",
            r"which.*property.*type",
            r"pros.*cons.*house",
            r"pros.*cons.*apartment"
        ]

        self.timing_patterns = [
            r"when.*best.*time",
            r"seasonal.*prices",
            r"market.*trends",
            r"price.*fluctuations",
            r"busy.*season"
        ]

        self.contact_patterns = [
            r"how.*contact.*owner",
            r"agent.*information",
            r"viewing.*appointment",
            r"schedule.*visit",
            r"contact.*details"
        ]

        self.legal_patterns = [
            r"legal.*requirements",
            r"documents.*needed",
            r"rental.*agreement",
            r"tenant.*rights",
            r"landlord.*obligations",
            r"property.*tax"
        ]

        self.financial_patterns = [
            r"mortgage.*options",
            r"financing.*available",
            r"down.*payment",
            r"interest.*rates",
            r"loan.*terms",
            r"payment.*plans"
        ]

        self.maintenance_patterns = [
            r"maintenance.*costs",
            r"utilities.*included",
            r"repair.*responsibilities",
            r"property.*condition",
            r"renovation.*costs"
        ]

    def can_handle(self, message: MCPMessage) -> bool:
        """Check if this capability can handle the message"""
        content_lower = message.content.lower().strip()

        # Check all patterns
        all_patterns = (
                self.statistics_patterns +
                self.comparison_patterns +
                self.recommendation_patterns +
                self.amenity_patterns +
                self.pricing_patterns +
                self.location_patterns +
                self.property_type_patterns +
                self.timing_patterns +
                self.contact_patterns +
                self.legal_patterns +
                self.financial_patterns +
                self.maintenance_patterns
        )

        for pattern in all_patterns:
            if re.search(pattern, content_lower):
                return True

        return False

    def process(self, message: MCPMessage, context: Dict[str, Any]) -> MCPResponse:
        """Process the comprehensive query"""
        content_lower = message.content.lower().strip()

        try:
            # Determine query type and handle accordingly
            if self._matches_patterns(content_lower, self.statistics_patterns):
                return self._handle_statistics_query(content_lower)

            elif self._matches_patterns(content_lower, self.comparison_patterns):
                return self._handle_comparison_query(content_lower)

            elif self._matches_patterns(content_lower, self.recommendation_patterns):
                return self._handle_recommendation_query(content_lower)

            elif self._matches_patterns(content_lower, self.amenity_patterns):
                return self._handle_amenity_query(content_lower)

            elif self._matches_patterns(content_lower, self.pricing_patterns):
                return self._handle_pricing_query(content_lower)

            elif self._matches_patterns(content_lower, self.location_patterns):
                return self._handle_location_query(content_lower)

            elif self._matches_patterns(content_lower, self.property_type_patterns):
                return self._handle_property_type_query(content_lower)

            elif self._matches_patterns(content_lower, self.timing_patterns):
                return self._handle_timing_query(content_lower)

            elif self._matches_patterns(content_lower, self.contact_patterns):
                return self._handle_contact_query(content_lower)

            elif self._matches_patterns(content_lower, self.legal_patterns):
                return self._handle_legal_query(content_lower)

            elif self._matches_patterns(content_lower, self.financial_patterns):
                return self._handle_financial_query(content_lower)

            elif self._matches_patterns(content_lower, self.maintenance_patterns):
                return self._handle_maintenance_query(content_lower)

            else:
                return self._handle_general_query(content_lower)

        except Exception as e:
            logger.error(f"Error in comprehensive handler: {str(e)}", exc_info=True)
            return MCPResponse(
                content="I encountered an error while processing your request. Please try rephrasing your question.",
                message_type=MessageType.ERROR,
                success=False,
                error_message=str(e)
            )

    def _matches_patterns(self, content: str, patterns: List[str]) -> bool:
        """Check if content matches any of the given patterns"""
        return any(re.search(pattern, content) for pattern in patterns)

    def _handle_statistics_query(self, content: str) -> MCPResponse:
        """Handle statistics-related queries"""
        try:
            # Get basic statistics
            total_properties = Property.objects.filter(is_paid=True).count()

            if total_properties == 0:
                return MCPResponse(
                    content="Currently, there are no properties available in our database.",
                    message_type=MessageType.CONVERSATIONAL
                )

            # Price statistics
            price_stats = Property.objects.filter(
                is_paid=True,
                price__isnull=False
            ).aggregate(
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price')
            )

            # Property type distribution
            type_distribution = Property.objects.filter(
                is_paid=True
            ).values('property_type').annotate(
                count=Count('id')
            ).order_by('-count')

            # City distribution
            city_distribution = Property.objects.filter(
                is_paid=True
            ).values('city').annotate(
                count=Count('id')
            ).order_by('-count')[:5]

            # Bedroom statistics
            bedroom_stats = Property.objects.filter(
                is_paid=True,
                bedrooms__isnull=False
            ).aggregate(
                avg_bedrooms=Avg('bedrooms')
            )

            # Format response
            response_parts = [
                f"📊 **Property Statistics:**",
                f"• Total properties: {total_properties}",
                f"• Average price: ${price_stats['avg_price']:,.2f}" if price_stats[
                    'avg_price'] else "• Average price: Not available",
                f"• Price range: ${price_stats['min_price']:,.2f} - ${price_stats['max_price']:,.2f}" if price_stats[
                                                                                                             'min_price'] and
                                                                                                         price_stats[
                                                                                                             'max_price'] else "• Price range: Not available",
                f"• Average bedrooms: {bedroom_stats['avg_bedrooms']:.1f}" if bedroom_stats[
                    'avg_bedrooms'] else "• Average bedrooms: Not available"
            ]

            if type_distribution:
                response_parts.append("\n🏠 **Property Types:**")
                for prop_type in type_distribution[:3]:
                    response_parts.append(f"• {prop_type['property_type'].title()}: {prop_type['count']}")

            if city_distribution:
                response_parts.append("\n🌍 **Top Cities:**")
                for city in city_distribution:
                    response_parts.append(f"• {city['city'].title()}: {city['count']}")

            return MCPResponse(
                content="\n".join(response_parts),
                message_type=MessageType.CONVERSATIONAL,
                metadata={"query_type": "statistics"}
            )

        except Exception as e:
            logger.error(f"Error in statistics query: {str(e)}")
            return MCPResponse(
                content="I'm having trouble retrieving statistics right now. Please try again later.",
                message_type=MessageType.ERROR,
                success=False
            )

    def _handle_comparison_query(self, content: str) -> MCPResponse:
        """Handle comparison-related queries"""
        # Extract comparison terms
        if "house" in content and "apartment" in content:
            return self._compare_house_vs_apartment()
        elif "buy" in content and "rent" in content:
            return self._compare_buy_vs_rent()
        else:
            return MCPResponse(
                content="I can help you compare different property types, buying vs renting, or specific properties. What would you like to compare?",
                message_type=MessageType.CONVERSATIONAL
            )

    def _compare_house_vs_apartment(self) -> MCPResponse:
        """Compare houses vs apartments"""
        try:
            house_stats = Property.objects.filter(
                is_paid=True,
                property_type='house',
                price__isnull=False
            ).aggregate(
                avg_price=Avg('price'),
                avg_bedrooms=Avg('bedrooms'),
                count=Count('id')
            )

            apartment_stats = Property.objects.filter(
                is_paid=True,
                property_type='apartment',
                price__isnull=False
            ).aggregate(
                avg_price=Avg('price'),
                avg_bedrooms=Avg('bedrooms'),
                count=Count('id')
            )

            response = [
                "🏠 **House vs Apartment Comparison:**",
                "",
                "**Houses:**",
                f"• Average price: ${house_stats['avg_price']:,.2f}" if house_stats[
                    'avg_price'] else "• Average price: Not available",
                f"• Average bedrooms: {house_stats['avg_bedrooms']:.1f}" if house_stats[
                    'avg_bedrooms'] else "• Average bedrooms: Not available",
                f"• Available: {house_stats['count']}",
                "",
                "**Apartments:**",
                f"• Average price: ${apartment_stats['avg_price']:,.2f}" if apartment_stats[
                    'avg_price'] else "• Average price: Not available",
                f"• Average bedrooms: {apartment_stats['avg_bedrooms']:.1f}" if apartment_stats[
                    'avg_bedrooms'] else "• Average bedrooms: Not available",
                f"• Available: {apartment_stats['count']}",
                "",
                "**Key Differences:**",
                "• Houses typically offer more space and privacy",
                "• Apartments often have lower maintenance costs",
                "• Houses may have higher utility costs",
                "• Apartments often include amenities like gyms/pools"
            ]

            return MCPResponse(
                content="\n".join(response),
                message_type=MessageType.CONVERSATIONAL,
                metadata={"query_type": "comparison"}
            )

        except Exception as e:
            logger.error(f"Error in house vs apartment comparison: {str(e)}")
            return MCPResponse(
                content="I'm having trouble comparing properties right now. Please try again later.",
                message_type=MessageType.ERROR,
                success=False
            )

    def _compare_buy_vs_rent(self) -> MCPResponse:
        """Compare buying vs renting"""
        response = [
            "💰 **Buying vs Renting Comparison:**",
            "",
            "**Buying:**",
            "✅ Pros:",
            "• Build equity over time",
            "• Freedom to customize",
            "• Potential investment returns",
            "• Stable monthly payments",
            "",
            "❌ Cons:",
            "• High upfront costs (down payment, closing costs)",
            "• Maintenance responsibilities",
            "• Less flexibility to move",
            "• Market risk",
            "",
            "**Renting:**",
            "✅ Pros:",
            "• Lower upfront costs",
            "• Flexibility to move",
            "• No maintenance worries",
            "• Predictable monthly costs",
            "",
            "❌ Cons:",
            "• No equity building",
            "• Rent can increase",
            "• Limited customization",
            "• No tax benefits",
            "",
            "**Consider your financial situation, timeline, and lifestyle preferences when deciding!**"
        ]

        return MCPResponse(
            content="\n".join(response),
            message_type=MessageType.CONVERSATIONAL,
            metadata={"query_type": "comparison"}
        )

    def _handle_recommendation_query(self, content: str) -> MCPResponse:
        """Handle recommendation queries"""
        try:
            # Get featured/priority properties
            featured_properties = Property.objects.filter(
                is_paid=True,
                listing_type='priority'
            ).order_by('-created_at')[:5]

            if not featured_properties.exists():
                # Fallback to recent properties
                featured_properties = Property.objects.filter(
                    is_paid=True
                ).order_by('-created_at')[:5]

            if not featured_properties.exists():
                return MCPResponse(
                    content="I don't have any properties to recommend at the moment. Please check back later!",
                    message_type=MessageType.CONVERSATIONAL
                )

            response_parts = [
                "⭐ **Recommended Properties:**",
                ""
            ]

            for prop in featured_properties:
                response_parts.append(
                    f"🏠 **{prop.title}**\n"
                    f"📍 {prop.suburb}, {prop.city}\n"
                    f"💰 ${prop.price:,.2f}" if prop.price else "💰 Price on request"
                                                               f"🛏️ {prop.bedrooms} bed, {prop.bathrooms} bath\n"
                )

            response_parts.append(
                "\nThese are some of our top picks! Would you like me to search for specific criteria?")

            return MCPResponse(
                content="\n".join(response_parts),
                message_type=MessageType.CONVERSATIONAL,
                metadata={"query_type": "recommendation"}
            )

        except Exception as e:
            logger.error(f"Error in recommendation query: {str(e)}")
            return MCPResponse(
                content="I'm having trouble finding recommendations right now. Please try a specific search instead.",
                message_type=MessageType.ERROR,
                success=False
            )

    def _handle_amenity_query(self, content: str) -> MCPResponse:
        """Handle amenity-related queries"""
        try:
            # Get all available amenities
            amenities = Amenity.objects.all().order_by('name')

            if not amenities.exists():
                return MCPResponse(
                    content="I don't have information about specific amenities at the moment. You can ask about properties in general!",
                    message_type=MessageType.CONVERSATIONAL
                )

            response_parts = [
                "🏠 **Available Amenities:**",
                ""
            ]

            for amenity in amenities:
                response_parts.append(f"• {amenity.name}")

            response_parts.append(
                "\nYou can search for properties with specific amenities by saying something like 'properties with wifi' or 'houses with parking'.")

            return MCPResponse(
                content="\n".join(response_parts),
                message_type=MessageType.CONVERSATIONAL,
                metadata={"query_type": "amenities"}
            )

        except Exception as e:
            logger.error(f"Error in amenity query: {str(e)}")
            return MCPResponse(
                content="I'm having trouble retrieving amenity information. Please try a different question.",
                message_type=MessageType.ERROR,
                success=False
            )

    def _handle_pricing_query(self, content: str) -> MCPResponse:
        """Handle pricing-related queries"""
        response = [
            "💰 **Pricing Information:**",
            "",
            "**Rental Properties:**",
            "• Prices vary by location, size, and amenities",
            "• Utilities may or may not be included",
            "• Security deposits are typically required",
            "• Rent is usually paid monthly",
            "",
            "**Properties for Sale:**",
            "• Prices depend on market conditions",
            "• Down payments typically 10-20%",
            "• Closing costs include legal fees and taxes",
            "• Mortgage terms available from banks",
            "",
            "**Market Factors:**",
            "• Location (CBD vs suburbs)",
            "• Property condition and age",
            "• Available amenities",
            "• Market demand and supply",
            "",
            "For specific pricing, try searching for properties in your preferred area!"
        ]

        return MCPResponse(
            content="\n".join(response),
            message_type=MessageType.CONVERSATIONAL,
            metadata={"query_type": "pricing"}
        )

    def _handle_location_query(self, content: str) -> MCPResponse:
        """Handle location-related queries"""
        response = [
            "📍 **Location Information:**",
            "",
            "**Safe Areas:**",
            "• Research crime statistics for specific neighborhoods",
            "• Visit the area at different times",
            "• Talk to local residents",
            "• Check with local police stations",
            "",
            "**Schools & Education:**",
            "• Contact local school districts",
            "• Visit schools in the area",
            "• Check school ratings and performance",
            "• Consider proximity to universities",
            "",
            "**Transportation:**",
            "• Check public transport routes",
            "• Consider traffic patterns",
            "• Look for major highways and roads",
            "• Check parking availability",
            "",
            "**Shopping & Services:**",
            "• Look for nearby shopping centers",
            "• Check for hospitals and clinics",
            "• Find restaurants and entertainment",
            "• Consider proximity to banks and post offices",
            "",
            "For specific area information, try searching for properties in that location!"
        ]

        return MCPResponse(
            content="\n".join(response),
            message_type=MessageType.CONVERSATIONAL,
            metadata={"query_type": "location"}
        )

    def _handle_property_type_query(self, content: str) -> MCPResponse:
        """Handle property type queries"""
        response = [
            "🏠 **Property Types:**",
            "",
            "**Houses:**",
            "• Standalone properties with private yards",
            "• More space and privacy",
            "• Higher maintenance responsibility",
            "• Usually more expensive",
            "",
            "**Apartments:**",
            "• Units in multi-family buildings",
            "• Shared amenities and facilities",
            "• Lower maintenance responsibility",
            "• Often more affordable",
            "",
            "**Airbnb:**",
            "• Short-term rental properties",
            "• Fully furnished and equipped",
            "• Flexible booking options",
            "• Higher nightly rates",
            "",
            "**Rooms:**",
            "• Individual rooms for rent",
            "• Shared common areas",
            "• Most affordable option",
            "• Less privacy",
            "",
            "**Guesthouses:**",
            "• Small, independent accommodations",
            "• Often in residential areas",
            "• Good for longer stays",
            "• Home-like atmosphere"
        ]

        return MCPResponse(
            content="\n".join(response),
            message_type=MessageType.CONVERSATIONAL,
            metadata={"query_type": "property_types"}
        )

    def _handle_timing_query(self, content: str) -> MCPResponse:
        """Handle timing-related queries"""
        response = [
            "⏰ **Timing Information:**",
            "",
            "**Best Time to Buy/Rent:**",
            "• Market conditions vary throughout the year",
            "• End of year may have more motivated sellers",
            "• Spring/summer often has more inventory",
            "• Consider your personal timeline",
            "",
            "**Seasonal Factors:**",
            "• Prices may fluctuate with seasons",
            "• Weather affects property viewing",
            "• School year affects family moves",
            "• Holiday periods may have limited availability",
            "",
            "**Market Trends:**",
            "• Monitor local market conditions",
            "• Check historical price data",
            "• Consider economic factors",
            "• Consult with real estate professionals",
            "",
            "**Viewing Properties:**",
            "• Schedule viewings during daylight hours",
            "• Visit at different times of day",
            "• Check traffic patterns",
            "• Consider seasonal weather conditions"
        ]

        return MCPResponse(
            content="\n".join(response),
            message_type=MessageType.CONVERSATIONAL,
            metadata={"query_type": "timing"}
        )

    def _handle_contact_query(self, content: str) -> MCPResponse:
        """Handle contact-related queries"""
        response = [
            "📞 **Contact Information:**",
            "",
            "**Property Owners:**",
            "• Contact details are available on property listings",
            "• Use the contact form on each property page",
            "• Phone numbers and emails are provided",
            "• Response times vary by owner",
            "",
            "**Scheduling Viewings:**",
            "• Contact the property owner directly",
            "• Arrange convenient viewing times",
            "• Be punctual for appointments",
            "• Ask questions during viewings",
            "",
            "**Tourwise Support:**",
            "• We're here to help with your search",
            "• Use the chat for general questions",
            "• Contact us for technical issues",
            "• We can't arrange viewings directly",
            "",
            "**Tips for Contacting Owners:**",
            "• Be professional and polite",
            "• Have your questions ready",
            "• Mention your timeline and requirements",
            "• Follow up if needed"
        ]

        return MCPResponse(
            content="\n".join(response),
            message_type=MessageType.CONVERSATIONAL,
            metadata={"query_type": "contact"}
        )

    def _handle_legal_query(self, content: str) -> MCPResponse:
        """Handle legal-related queries"""
        response = [
            "⚖️ **Legal Information:**",
            "",
            "**Rental Agreements:**",
            "• Written contracts are recommended",
            "• Include rent amount and payment terms",
            "• Specify lease duration and renewal terms",
            "• Detail maintenance responsibilities",
            "",
            "**Required Documents:**",
            "• Proof of income/employment",
            "• References from previous landlords",
            "• Credit check authorization",
            "• Identification documents",
            "",
            "**Tenant Rights:**",
            "• Right to habitable living conditions",
            "• Right to privacy and quiet enjoyment",
            "• Right to request repairs",
            "• Protection from discrimination",
            "",
            "**Landlord Obligations:**",
            "• Maintain habitable conditions",
            "• Make necessary repairs",
            "• Provide proper notice for entry",
            "• Follow eviction procedures",
            "",
            "**Important:** This is general information. Consult with a legal professional for specific advice."
        ]

        return MCPResponse(
            content="\n".join(response),
            message_type=MessageType.CONVERSATIONAL,
            metadata={"query_type": "legal"}
        )

    def _handle_financial_query(self, content: str) -> MCPResponse:
        """Handle financial-related queries"""
        response = [
            "💳 **Financial Information:**",
            "",
            "**Mortgage Options:**",
            "• Conventional mortgages available",
            "• Government-backed loans may be available",
            "• Down payments typically 10-20%",
            "• Interest rates vary by lender and credit score",
            "",
            "**Financing Requirements:**",
            "• Good credit score (650+)",
            "• Stable income and employment",
            "• Debt-to-income ratio under 43%",
            "• Sufficient down payment",
            "",
            "**Payment Plans:**",
            "• Monthly mortgage payments",
            "• Property taxes and insurance",
            "• Maintenance and utility costs",
            "• Emergency fund recommended",
            "",
            "**Investment Considerations:**",
            "• Rental income potential",
            "• Property appreciation",
            "• Tax benefits for homeowners",
            "• Market risk and volatility",
            "",
            "**Consult with financial advisors and mortgage lenders for personalized advice.**"
        ]

        return MCPResponse(
            content="\n".join(response),
            message_type=MessageType.CONVERSATIONAL,
            metadata={"query_type": "financial"}
        )

    def _handle_maintenance_query(self, content: str) -> MCPResponse:
        """Handle maintenance-related queries"""
        response = [
            "🔧 **Maintenance Information:**",
            "",
            "**Rental Properties:**",
            "• Landlords typically handle major repairs",
            "• Tenants may be responsible for minor maintenance",
            "• Check lease agreement for specific terms",
            "• Report issues promptly",
            "",
            "**Owned Properties:**",
            "• Full responsibility for all maintenance",
            "• Regular inspections recommended",
            "• Budget for unexpected repairs",
            "• Consider home warranty options",
            "",
            "**Common Maintenance Costs:**",
            "• HVAC system maintenance",
            "• Plumbing and electrical repairs",
            "• Roof and exterior maintenance",
            "• Landscaping and yard care",
            "",
            "**Utilities:**",
            "• Check what's included in rent",
            "• Budget for electricity, water, gas",
            "• Internet and cable costs",
            "• Trash and recycling services",
            "",
            "**Prevention Tips:**",
            "• Regular inspections and maintenance",
            "• Address issues before they become major problems",
            "• Keep emergency fund for repairs",
            "• Maintain good relationships with contractors"
        ]

        return MCPResponse(
            content="\n".join(response),
            message_type=MessageType.CONVERSATIONAL,
            metadata={"query_type": "maintenance"}
        )

    def _handle_general_query(self, content: str) -> MCPResponse:
        """Handle general queries that don't fit other categories"""
        response = [
            "🤔 **I understand you're asking about something specific.**",
            "",
            "Here are some things I can help you with:",
            "",
            "🏠 **Property Search:**",
            "• Find houses, apartments, or other properties",
            "• Search by location, price, or features",
            "• Get property recommendations",
            "",
            "📊 **Market Information:**",
            "• Property statistics and trends",
            "• Price comparisons and analysis",
            "• Market insights and data",
            "",
            "💡 **General Advice:**",
            "• Property buying and renting tips",
            "• Location and neighborhood information",
            "• Financial and legal considerations",
            "",
            "Try asking me something like:",
            "• 'Show me houses in Harare'",
            "• 'What's the average price of apartments?'",
            "• 'Compare houses vs apartments'",
            "• 'What amenities are available?'"
        ]

        return MCPResponse(
            content="\n".join(response),
            message_type=MessageType.CONVERSATIONAL,
            metadata={"query_type": "general"}
        )

    def get_priority(self) -> int:
        """Medium priority - handles complex queries"""
        return 40