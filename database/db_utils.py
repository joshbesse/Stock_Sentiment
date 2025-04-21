from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from database.models import StockPrice, Headline, RedditPost, Sentiment

engine = create_engine("sqlite:///stock_sentiment.db")
Session = sessionmaker(bind=engine)

def save_stock_prices(ticker, price_df):
    session = Session()
    for date, price in price_df.iterrows():
        exists = session.query(StockPrice).filter_by(ticker=ticker, date=date).first()
        if not exists:
            record = StockPrice(
                ticker=ticker,
                date=date,
                close_price=price
            )
            session.add(record)
    session.commit()
    session.close()

def save_headlines(ticker, headlines):
    session = Session()
    for h in headlines:
        exists = session.query(Headline).filter_by(ticker=ticker, date=h["timestamp"], title=h["text"]).first()
        if not exists:
            record = Headline(
                ticker=ticker,
                date=h["timestamp"],
                title=h["text"],
                source=h["source"],
                url=h["url"],
                sentiment=h["sentiment"]
            )
            session.add(record)
    session.commit()
    session.close()

def save_reddit_posts(ticker, posts):
    session = Session()
    for p in posts:
        exists = session.query(RedditPost).filter_by(ticker=ticker, date=p["created"], title=p["title"]).first()
        if not exists:
            record = RedditPost(
                ticker=ticker,
                date=p["created"],
                title=p["title"],
                text=p["text"],
                score=p["score"],
                url=p["url"],
                subreddit=p["subreddit"],
                sentiment=p["sentiment"]
            )
            session.add(record)
    session.commit()
    session.close()

def save_sentiment(ticker, sentiment_df):
    session = Session()
    for date, sentiment in sentiment_df.iterrows():
        exists = session.query(Sentiment).filter_by(ticker=ticker, date=date).first()
        if not exists:
            record = Sentiment(
                ticker=ticker,
                date=date,
                average_sentiment=sentiment
            )
            session.add(record)
    session.commit()
    session.close()