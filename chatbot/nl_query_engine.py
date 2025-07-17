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
        "The main table is 'listings_property' which contains columns like: title, suburb, city, price, property_type, description. "
        "The user might say things like: 'show me houses in Avondale under $500' or 'I want a flat in Harare with garden and WiFi'. "
        "Use proper WHERE clauses and lowercase string values when filtering by suburb, city, or property_type. "
        "Do not fabricate table or column names."
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
                        new_select = select_cols + f", {field}"
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

# sql_database = SQLDatabase(engine)
# query_engine = NLSQLTableQueryEngine(llm=llm, sql_database=sql_database)

def run_nl_query(natural_query):
    result = query_engine.query(natural_query)
    print("SQL generated: ", result.metadata.get("sql_query", "[none]"))
    return result
