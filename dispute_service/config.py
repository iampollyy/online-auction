import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

SERVICE_BUS_LISTEN_CONNECTION_STRING = os.getenv("SERVICE_BUS_RECEIVE_CONNECTION_STRING", "")

QUEUE_NAME = "polinatrybialustava"
