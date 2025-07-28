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
        "Always include the required fields: id, title, main_image, price, street_address, suburb, city in your SELECT statement. "
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
        required_fields = ["id", "title", "main_image", "price", "street_address", "suburb", "city"]
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
                    # if prop_id:
                    #     images = PropertyImage.objects.filter(property_id=prop_id).values_list("image", flat=True)
                    #     # Store as list of relative paths
                    #     row["property_images"] = list(images)
        except Exception as e:
            # If anything goes wrong, skip adding images (do not break main flow)
            pass
        # --- End property images logic ---

        return result


query_engine = CaseInsensitivePropertyTypeQueryEngine(llm=llm, sql_database=sql_database, tables=included_tables)


def run_nl_query(natural_query):
    """
    Pure SQL query engine - no conversational handling.
    Conversational queries are now handled by the MCP architecture.
    """
    print(f"🔍 Processing SQL query: '{natural_query}'")

    # Execute SQL query directly
    result = query_engine.query(natural_query)
    print("SQL generated: ", result.metadata.get("sql_query", "[none]"))
    return result

