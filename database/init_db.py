from models import Base
from sqlalchemy import create_engine

engine = create_engine("sqlite:///stock_sentiment.db")
Base.metadata.create_all(engine)

print("Database initialized.")