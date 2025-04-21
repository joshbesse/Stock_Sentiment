import sys
import os
import pandas as pd 
import datetime
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from database.db_utils import save_stock_prices, save_headlines, save_reddit_posts, save_sentiment
from app import fetch_price_data, fetch_headlines, fetch_reddit_posts, sentiment_over_time


sp500_df = pd.read_csv("./data_scraper/SP500.csv")
tickers = sp500_df["Symbol"].values
TICKER_ROTATION = [
    tickers[:100],
    tickers[100:200],
    tickers[200:300],
    tickers[300:400],
    tickers[400:]
]

def get_today_tickers():
    day_index = datetime.date.today().toordinal() % len(TICKER_ROTATION)
    return TICKER_ROTATION[day_index]

def main():
    tickers_today = get_today_tickers()
    print(f"Running daily scrape for tickers: {tickers_today}")

    for ticker in tickers_today:
        try:
            print(f"Fetching data for {ticker}...")

            days = 5
            price_data, company_name = fetch_price_data(ticker, days)
            headlines, _ = fetch_headlines(ticker, days, company_name)
            reddit_posts, _ = fetch_reddit_posts(ticker, days)
            sentiment = sentiment_over_time(headlines, reddit_posts, days)

            save_stock_prices(ticker, price_data)
            save_headlines(ticker, headlines)
            save_reddit_posts(ticker, reddit_posts)
            save_sentiment(ticker, sentiment)

            time.sleep(1)
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
    
    print("Daily scrape complete.")

if __name__ == "__main__":
    main()