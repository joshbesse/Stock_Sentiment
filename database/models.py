from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class StockPrice(Base):
    __tablename__ = "stock_prices"
    id = Column(Integer, primary_key=True)
    ticker = Column(String)
    date = Column(Date)
    close_price = Column(Float)

class Headline(Base):
    __tablename__ = "headlines"
    id = Column(Integer, primary_key=True)
    ticker = Column(String)
    date = Column(Date)
    title = Column(String)
    source = Column(String)
    url = Column(String)
    sentiment = Column(Float)

class RedditPost(Base):
    __tablename__ = "reddit_posts"
    id = Column(Integer, primary_key=True)
    ticker = Column(String)
    date = Column(Date)
    title = Column(String)
    text = Column(String)
    score = Column(Integer)
    url = Column(String)
    subreddit = Column(String)
    sentiment = Column(Float)

class Sentiment(Base):
    __tablename__ = "sentiment"
    id = Column(Integer, primary_key=True)
    ticker = Column(String)
    date = Column(Date)
    average_sentiment = Column(Float)