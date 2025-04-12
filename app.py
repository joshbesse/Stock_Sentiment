import os
from dotenv import load_dotenv
import datetime
import time
import streamlit as st
import yfinance as yf
import requests
import praw
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import altair as alt

@st.cache_data(ttl=600)
def fetch_price_data(ticker, days):
    try:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days)

        df = yf.download(ticker, start_date, end_date)

        if df.empty:
            return None
        
        return df['Close'].round(2)
    except Exception as e:
        return None

def get_sentiment(text, analyzer):
    if not text or not isinstance(text, str):
        return 0.0

    score = analyzer.polarity_scores(text)["compound"]
    return round(score, 2)

@st.cache_data(ttl=600)
def fetch_headlines(ticker, days):
    api_key = os.getenv("NEWSAPI_KEY") or st.secrets["newsapi"]["key"]
    url = "https://newsapi.org/v2/everything"
    days = min(days, 30)

    today = datetime.date.today()
    from_date = (today - datetime.timedelta(days)).strftime('%Y-%m-%d')

    params={
        "q": ticker,
        "from": from_date,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 100,
        "apiKey": api_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data["status"] != "ok":
        return []

    headlines = []
    for article in data["articles"]:
        headlines.append({
            "text": article["title"],
            "timestamp": pd.to_datetime(article["publishedAt"]).strftime('%Y-%m-%d'),
            "source": article["source"]["name"],
            "url": article["url"],
            "sentiment": get_sentiment(article["title"], analyzer)
        })
    
    return headlines, headlines[:20]

def init_reddit_client():
    client_id = os.getenv("REDDIT_CLIENT_ID") or st.secrets["praw"]["reddit_client_id"]
    client_secret = os.getenv("REDDIT_CLIENT_SECRET") or st.secrets["praw"]["reddit_client_secret"]
    user_agent = os.getenv("REDDIT_USER_AGENT") or st.secrets["praw"]["reddit_user_agent"]

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

@st.cache_data(ttl=600)
def fetch_reddit_posts(ticker, days, limit_per_sub=50):
    reddit = init_reddit_client()
    subreddits = ["stocks", "investing", "StockMarket"]
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days)

    posts = []
    for sub in subreddits:
        for post in reddit.subreddit(sub).search(ticker, sort="new", time_filter="month", limit=limit_per_sub):
            created_time = datetime.datetime.fromtimestamp(post.created_utc, tz=datetime.timezone.utc)
            if created_time < cutoff:
                continue

            posts.append({
                "title": post.title,
                "text": post.selftext,
                "score": post.score,
                "created": pd.to_datetime(post.created_utc, unit='s').strftime('%Y-%m-%d'),
                "url": post.url,
                "subreddit": sub,
                "sentiment": get_sentiment(post.title + " " + post.selftext, analyzer)
            })
        time.sleep(1)
    
    posts_sorted = sorted(posts, key=lambda x: x["created"], reverse=True)
    
    return posts, posts_sorted[:20]

def render_headlines(headlines):
    for headline in headlines:
        if headline['sentiment'] >= 0.3:
            sentiment = "Positive"
        elif headline['sentiment'] <= -0.3:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        st.markdown(f"**[{headline['text']}]({headline['url']})**")
        st.caption(f"Sentiment: {sentiment} ({headline['sentiment']}) | Source: {headline['source']} | Date: {headline['timestamp']}")

def render_reddit_posts(posts):
    for post in posts:
        if post['sentiment'] >= 0.3:
            sentiment = "Positive"
        elif post['sentiment'] <= 0.3:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        st.markdown(f"**[{post['title']}]({post['url']})**")
        st.write(f"> {post['text'][:200]}{'...' if len(post['text']) > 200 else ''}")
        st.caption(f"Sentiment: {sentiment} ({post['sentiment']}) | Subreddit: {post['subreddit']} | Upvotes: {post['score']} | Date: {post['created']}")

def sentiment_over_time(headlines, posts, days):
    def combine_sentiment_data(headlines, posts):
        headline_data = [{
            "date": item['timestamp'],
            "sentiment": item['sentiment']
        } for item in headlines]

        reddit_data = [{
            "date": item['created'],
            "sentiment": item['sentiment']
        } for item in posts]

        all_data = headline_data + reddit_data
        return pd.DataFrame(all_data)

    def group_sentiment_by_day(df, days):
        max_days = min(days, 14)

        grouped = df.groupby("date").mean().round(2).reset_index()
        grouped = grouped.sort_values("date").tail(max_days)

        grouped = grouped.rename(columns={"date": "Date"})
        grouped["Date"] = pd.to_datetime(grouped["Date"])

        return grouped

    combined = combine_sentiment_data(headlines, posts)
    grouped = group_sentiment_by_day(combined, days)

    return grouped

def make_price_chart(df, ticker):
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y(ticker, title="Price"),
        tooltip=["Date:T", alt.Tooltip(ticker, format=".2f")]
    ).properties(
        title=f"{ticker} Price Over Time"
    )

    return chart

def make_sentiment_chart(df, ticker):
    chart = alt.Chart(df).mark_line(point=True, color="orange").encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("sentiment", title="Average Sentiment"),
        tooltip=["Date:T", alt.Tooltip("sentiment", format=".2f")]
    ).properties(
        title=f"Average {ticker} Sentiment Over Time"
    )

    return chart

def make_overlay_chart(df_price, df_sentiment, ticker):
    df = pd.merge(df_price, df_sentiment, on="Date", how="outer")
    df = df.sort_values("Date")

    price_line = alt.Chart(df).mark_line(point=True, color="blue").encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y(ticker, title="Price"),
        tooltip=[alt.Tooltip("Date:T"), alt.Tooltip(ticker, format=".2f")]
    )

    sentiment_line = alt.Chart(df).mark_line(point=True, color="orange").encode(
        x="Date:T",
        y=alt.Y("sentiment", title="Average Sentiment"),
        tooltip=[alt.Tooltip("Date:T"), alt.Tooltip("sentiment", format=".2f")]
    )

    chart = alt.layer(price_line, sentiment_line).resolve_scale(y="independent").properties(
        title=f"{ticker} Price + Sentiment Over Time"
    )

    return chart

# set environment variables
load_dotenv()

# set page configs
st.set_page_config(
    layout='wide',
    page_title='Stock Sentiment',
    page_icon='📊',
)

# initialize newsapi headlines and reddit posts
top_headlines = None
top_posts = None

# initialize VADER model
analyzer = SentimentIntensityAnalyzer()

# set page layout
c1, c2 = st.columns([1, 1])

with c1:
    # header
    st.markdown("<h2>Stock Price + Sentiment Dashboard</h2>", unsafe_allow_html=True)

    with st.container():
        # graph placeholder
        graph = st.empty()

        # form
        with st.form("ticker_input"):
            ticker = st.text_input("Enter stock ticker (e.g. AAPL, AMZN)", None, 5)
            days = st.slider("Select number of past days to look at", min_value=1, max_value=365, value=30)
            submitted = st.form_submit_button("Submit")

        if submitted:
            if ticker is None:
                st.error("Invalid ticker or no data found.")
            else: 
                with st.spinner(f"Fetching data for {ticker.upper()}..."):
                    close_prices = fetch_price_data(ticker, days)
                    if close_prices is None:
                        st.error("Invalid ticker or no data found.")
                    else:
                        all_headlines, top_headlines = fetch_headlines(ticker, days)
                        all_posts, top_posts = fetch_reddit_posts(ticker, days)
                        sentiment = sentiment_over_time(all_headlines, all_posts, days)

                        with graph:
                            gt1, gt2, gt3 = st.tabs(["Price", "Sentiment", "Price + Sentiment"])
                            with gt1:
                                st.altair_chart(make_price_chart(close_prices.reset_index(), ticker), use_container_width=True)
                            
                            with gt2:
                                st.altair_chart(make_sentiment_chart(sentiment, ticker), use_container_width=True)

                            with gt3:
                                st.altair_chart(make_overlay_chart(close_prices.reset_index(), sentiment, ticker), use_container_width=True)

                        st.success(f"Showing closing prices for {ticker.upper()} over the past {days} days.")

with c2:
    t1, t2 = st.tabs(["Recent Headlines", "Recent Reddit Posts"])
    with t1:
        if top_headlines:
            render_headlines(top_headlines)
    with t2:
        if top_posts:
            render_reddit_posts(top_posts)