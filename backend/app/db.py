import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://citypvp:citypvp@localhost:5432/citypvp"
)

engine = create_engine(DATABASE_URL)
Base = declarative_base()
