import streamlit as st
import yfinance as yf
import datetime
from dotenv import load_dotenv
import os
import requests

@st.cache_data(ttl=600)
def fetch_price_data(ticker, days):
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days)

    df = yf.download(ticker, start_date, end_date)

    if df.empty:
        return None
    
    return df['Close'].round(2)

@st.cache_data(ttl=600)
def fetch_headlines(ticker, days):
    api_key = os.getenv("NEWSAPI_KEY") or st.secrets["api_keys"]["newsapi"]
    url = "https://newsapi.org/v2/everything"
    days = min(days, 30)

    today = datetime.date.today()
    from_date = (today - datetime.timedelta(days)).strftime('%Y-%m-%d')

    params={
        "q": ticker,
        "from": from_date,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 10,
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
            "timestamp": article["publishedAt"],
            "source": article["source"]["name"],
            "url": article["url"]
        })
    
    return headlines

def render_headlines(headlines):
    for headline in headlines:
        st.markdown(f"**[{headline['text']}]({headline['url']})**")
        st.caption(f"{headline['source']} | {headline['timestamp']}")

load_dotenv()

# set page configs
st.set_page_config(
    layout='wide',
    page_title='Stock Sentiment',
    page_icon='📊',
)

headlines = None

# set page layout
c1, c2 = st.columns([1, 1])

with c1:
    # header
    st.markdown("<h2>Stock Sentiment Dashboard</h2>", unsafe_allow_html=True)

    # chart placeholder
    chart = st.line_chart()

    with st.container():
        # form
        with st.form("ticker_input"):
            ticker = st.text_input("Enter stock ticker (e.g. AAPL, AMZN)", None, 5)
            days = st.slider("Select number of past days to look at", min_value=1, max_value=365, value=30)
            submitted = st.form_submit_button("Submit")

        if submitted:
            with st.spinner(f"Fetching data for {ticker.upper()}..."):
                close_prices = fetch_price_data(ticker, days)
                headlines = fetch_headlines(ticker, days)

                if close_prices is None:
                    st.error("Invalid ticker or no data found.")
                else:
                    chart.line_chart(close_prices)
                    st.success(f"Showing closing prices for {ticker.upper()} over the past {days} days.")

with c2:
    t1, t2 = st.tabs(["Recent Headlines", "Recent Tweets"])
    with t1:
        if headlines:
            render_headlines(headlines)
