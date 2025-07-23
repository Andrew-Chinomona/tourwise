import os, urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings, SQLDatabase
from llama_index.llms.groq import Groq
from llama_index.core.query_engine import NLSQLTableQueryEngine
import re

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = urllib.parse.quote_plus(os.getenv("DB_PASSWORD"))
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
llm = Groq(
    model="llama3-8b-8192",
    api_key=os.getenv("GROQ_API_KEY"),
    system_message=(
        "You are an expert SQL assistant for a property search app in Zimbabwe. "
        "Your job is to convert natural language into SQL queries that work with the database schema. "
        "The main table is 'listings_property' which contains these columns: "
        "id, title, description, street_address, suburb, city, state_or_region, country, "
        "property_type, bedrooms, bathrooms, area, price, main_image, created_at. "
        "The property_type field has these values: 'house', 'apartment', 'airbnb', 'room', 'guesthouse'. "
        "When users mention 'houses', 'homes', or 'house', use property_type = 'house'. "
        "When users mention 'apartments', 'flats', or 'apartment', use property_type = 'apartment'. "
        "Use proper WHERE clauses and lowercase string values when filtering by suburb, city, or property_type. "
        "Always include the required fields: id, main_image, price, street_address, suburb, city in your SELECT statement. "
        "Do not use table aliases unless necessary. "
        "Do not fabricate table or column names."
    )
)

# Separate LLM for chat responses
chat_llm = Groq(
    model="llama3-8b-8192",
    api_key=os.getenv("GROQ_API_KEY"),
    system_message=(
        "You are a friendly, knowledgeable, and conversational AI assistant helping users find properties in Zimbabwe through Tourwise, a property listing platform. "
        "Your job is to understand natural language input and provide helpful, varied, and natural responses. "
        "Always vary the tone slightly to make the interaction feel natural and human-like. "
        "You are not a rule-based assistant. Respond in a fluid and intelligent manner like ChatGPT. "
        "Prioritize clarity, warmth, and context awareness."
    )
)

embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
Settings.embed_model = embed_model

included_tables = ["listings_property",
                   "listings_amenity",
                   "listings_currency",
                   "listings_property_amenities",
                   "listings_propertyimage"

                   ]
sql_database = SQLDatabase(engine, include_tables=included_tables)


class CaseInsensitivePropertyTypeQueryEngine(NLSQLTableQueryEngine):
    def __init__(self, llm, sql_database, tables=None):
        super().__init__(llm=llm, sql_database=sql_database, tables=tables)
        self.sql_database = sql_database

    def query(self, natural_query, *args, **kwargs):
        # Call the parent to get the result object (which includes the SQL)
        result = super().query(natural_query, *args, **kwargs)
        sql = result.metadata.get("sql_query", "")

        # --- Post-process SQL to ensure all required fields are always selected ---
        required_fields = ["id", "main_image", "price", "street_address", "suburb", "city"]
        for field in required_fields:
            if field not in sql.lower():
                import re
                select_match = re.match(r"(select\s+)(.+?)(\s+from\s+listings_property)", sql, re.IGNORECASE)
                if select_match:
                    select_cols = select_match.group(2)
                    if "*" in select_cols:
                        # If SELECT * is used, replace it with specific columns
                        new_select = ", ".join(required_fields)
                    else:
                        new_select = select_cols + f", {field}"
                    sql = select_match.group(1) + new_select + select_match.group(3) + sql[select_match.end(3):]
                    result.metadata["sql_query"] = sql
        # --- End post-process ---

        # Rewrite property_type comparisons to be case-insensitive (improved logic for table aliases)
        new_sql = re.sub(
            r"(?:\b(\w+)\.)?property_type\s*=\s*'([^']+)'",
            lambda m: f"LOWER({m.group(1) + '.' if m.group(1) else ''}property_type) = '{m.group(2).lower()}'",
            sql
        )
        if new_sql != sql:
            result.metadata["sql_query"] = new_sql
            result.response = self.sql_database.run_sql(new_sql)

        # Auto-add property_type filter if user mentioned houses/apartments but SQL doesn't have it
        if "property_type" not in sql.lower():
            natural_query_lower = natural_query.lower()
            if any(word in natural_query_lower for word in ["house", "houses", "home", "homes"]):
                # Add property_type = 'house' filter
                if "where" in sql.lower():
                    new_sql = re.sub(r"(\s+WHERE\s+)", r"\1property_type = 'house' AND ", sql, flags=re.IGNORECASE)
                else:
                    new_sql = re.sub(r"(\s+FROM\s+listings_property)", r"\1 WHERE property_type = 'house'", sql,
                                     flags=re.IGNORECASE)
                if new_sql != sql:
                    result.metadata["sql_query"] = new_sql
                    result.response = self.sql_database.run_sql(new_sql)
            elif any(word in natural_query_lower for word in ["apartment", "apartments", "flat", "flats"]):
                # Add property_type = 'apartment' filter
                if "where" in sql.lower():
                    new_sql = re.sub(r"(\s+WHERE\s+)", r"\1property_type = 'apartment' AND ", sql, flags=re.IGNORECASE)
                else:
                    new_sql = re.sub(r"(\s+FROM\s+listings_property)", r"\1 WHERE property_type = 'apartment'", sql,
                                     flags=re.IGNORECASE)
                if new_sql != sql:
                    result.metadata["sql_query"] = new_sql
                    result.response = self.sql_database.run_sql(new_sql)

        # Build conversational response with dynamic phrasing
        if isinstance(result.response, list) and result.response:
            property_count = len(result.response)
            first_result = result.response[0]
            city = first_result.get("city", "")
            suburb = first_result.get("suburb", "")
            location_string = ""
            if suburb:
                location_string = f"{suburb}, {city}" if city else suburb
            elif city:
                location_string = city
            else:
                location_string = "your selected area"

            print(f"🔍 Generating chat response for {property_count} properties in {location_string}")

            summary_prompt = (
                f"The user asked: '{natural_query}'. You found {property_count} matching properties in {location_string}. "
                f"Write a friendly, varied, and natural-sounding reply introducing these listings, "
                f"like a chatbot would. Include casual tone. Example phrases: 'Here's what I found', 'Take a look at these!', 'Looks like a good match!'. "
                f"Do NOT repeat the same phrasing every time. Add a touch of variety."
            )

            try:
                summary_response = chat_llm.complete(summary_prompt)
                result.metadata["chat_response"] = summary_response.text.strip()
                print(f"✅ Generated chat response: {result.metadata['chat_response']}")
            except Exception as e:
                print(f"❌ Error generating chat response: {str(e)}")
                # Fallback to a simple but varied message
                if property_count == 1:
                    result.metadata[
                        "chat_response"] = f"Perfect! I found {property_count} property that matches your search in {location_string}."
                else:
                    result.metadata[
                        "chat_response"] = f"Great! I found {property_count} properties that match your search in {location_string}."
        else:
            result.metadata["chat_response"] = "Here is what I found."

        # --- Fetch property images for each property in the result (for mobile views) ---
        # If result.response is a list of dicts, add property_images as a list of image paths
        try:
            from listings.models import PropertyImage
            if isinstance(result.response, list):
                for row in result.response:
                    # Try to get property id from row (id or pk)
                    prop_id = row.get("id")
                    if prop_id:
                        images = PropertyImage.objects.filter(property_id=prop_id).values_list("image", flat=True)
                        # Store as list of relative paths
                        row["property_images"] = list(images)
        except Exception as e:
            # If anything goes wrong, skip adding images (do not break main flow)
            pass
        # --- End property images logic ---

        return result


query_engine = CaseInsensitivePropertyTypeQueryEngine(llm=llm, sql_database=sql_database, tables=included_tables)


def run_nl_query(natural_query):
    # Handle conversational queries first
    natural_query_lower = natural_query.lower().strip()

    print(f"🔍 Processing query: '{natural_query}' (lowercase: '{natural_query_lower}')")

    # Greetings and salutations
    greetings = [
        "hello", "hi", "hey", "hie", "good morning", "good afternoon", "good evening",
        "how are you", "how's it going", "what's up", "sup", "yo"
    ]

    # Farewells
    farewells = [
        "bye", "goodbye", "see you", "take care", "have a good day", "thanks", "thank you"
    ]

    # Gratitude
    gratitude = [
        "thanks", "thank you", "appreciate it", "awesome", "great", "perfect", "excellent"
    ]

    # Check if it's a conversational query
    if any(greeting in natural_query_lower for greeting in greetings):
        print(f"✅ Detected greeting: '{natural_query}'")
        import random
        responses = [
            "Hello! 👋 I'm here to help you find your perfect property in Zimbabwe. What are you looking for today?",
            "Hi there! 😊 Welcome to Tourwise! I can help you find houses, apartments, and other properties. What's on your mind?",
            "Hey! 🏡 Great to see you! I'm your property search assistant. What type of property are you interested in?",
            "Good day! ✨ I'm here to make your property search easy and fun. What can I help you find today?",
            "Hello! 🌟 Welcome to Tourwise! I'm excited to help you discover amazing properties. What are you searching for?"
        ]
        return {
            "chat_response": random.choice(responses),
            "results": [],
            "is_conversational": True
        }

    elif any(farewell in natural_query_lower for farewell in farewells):
        print(f"✅ Detected farewell: '{natural_query}'")
        import random
        responses = [
            "Goodbye! 👋 It was great helping you today. Feel free to come back anytime!",
            "Take care! 😊 Happy house hunting! Don't hesitate to return if you need more help.",
            "See you later! 🏡 I hope you found what you were looking for. Come back soon!",
            "Have a wonderful day! ✨ Thanks for using Tourwise. I'll be here when you need me!",
            "Bye for now! 🌟 Good luck with your property search. I'm always here to help!"
        ]
        return {
            "chat_response": random.choice(responses),
            "results": [],
            "is_conversational": True
        }

    elif any(grat in natural_query_lower for grat in gratitude):
        print(f"✅ Detected gratitude: '{natural_query}'")
        import random
        responses = [
            "You're very welcome! 😊 I'm glad I could help. Is there anything else you'd like to know?",
            "My pleasure! ✨ I love helping people find their perfect home. What else can I assist you with?",
            "Anytime! 🏡 I'm here to make your property search as smooth as possible. Need anything else?",
            "Happy to help! 🌟 That's what I'm here for. Feel free to ask me anything about properties!",
            "You're welcome! 😄 I enjoy helping people discover great properties. What's next on your list?"
        ]
        return {
            "chat_response": random.choice(responses),
            "results": [],
            "is_conversational": True
        }

    # Handle other conversational queries
    elif any(phrase in natural_query_lower for phrase in [
        "how does this work", "what can you do", "help", "what are you", "who are you"
    ]):
        print(f"✅ Detected help query: '{natural_query}'")
        return {
            "chat_response": "I'm your AI property assistant! 🏡 I can help you find houses, apartments, and other properties in Zimbabwe. Just tell me what you're looking for - like 'houses in Harare' or 'apartments under $500' - and I'll search our database for you. What type of property interests you?",
            "results": [],
            "is_conversational": True
        }

    print(f"🔍 No conversational match found, proceeding with SQL query for: '{natural_query}'")
    # If not conversational, proceed with normal SQL query
    result = query_engine.query(natural_query)
    print("SQL generated: ", result.metadata.get("sql_query", "[none]"))
    return result

