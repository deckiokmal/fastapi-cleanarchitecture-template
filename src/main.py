from fastapi import FastAPI
from .database.core import create_tables
from .entities.todo import Todo  # Import models to register them
from .entities.user import User  # Import models to register them
from .api import register_routes
from .logging import configure_logging, LogLevels
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()


configure_logging(LogLevels.info)

app = FastAPI()

# Get environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "development":
    allow_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
else:
    allow_origins = [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

""" Only uncomment below to create new tables, 
otherwise the tests will fail if not connected
"""
# create_tables()

register_routes(app)