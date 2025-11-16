from fastapi import FastAPI
from .database.core import create_tables
from .entities.todo import Todo  # Import models to register them
from .entities.user import User  # Import models to register them
from .api import register_routes
from .logging import configure_logging, LogLevels


configure_logging(LogLevels.info)

app = FastAPI()

""" Only uncomment below to create new tables, 
otherwise the tests will fail if not connected
"""
create_tables()

register_routes(app)