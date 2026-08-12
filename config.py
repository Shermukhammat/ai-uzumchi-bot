import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DB_URL")
DEV_ID = int(os.getenv("DEV_ID"))
DEBUG = os.getenv("DEBUG") == '1'
MAX_CHANNELS = 10
