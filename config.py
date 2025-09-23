import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
DATA_DIR = "./data"
OUTPUT_DIR = "./output"

# rentcast
RENTCAST_API_KEY = os.getenv("RENTCAST_API_KEY")
RENTCAST_URL = "https://api.rentcast.io/v1"
MAX_RADIUS = 1.0

# argcgis
ARCGIS_USERNAME = os.getenv("ARCGIS_USERNAME")
ARCGIS_PASSWORD = os.getenv("ARCGIS_PASSWORD")
ARCGIS_URL = "https://www.arcgis.com"
ARCGIS_TOKEN_URL = f"{ARCGIS_URL}/sharing/rest/generateToken"
ARCGIS_ENRICH_URL = "https://geoenrich.arcgis.com/arcgis/rest/services/World/geoenrichmentserver/GeoEnrichment/enrich"

# openai
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-5"
MAX_RETRIES = 3

# pandasai
PANDASAI_MODEL = "o3"