import streamlit as st
import yfinance as yf
import datetime

@st.cache_data(ttl=600)
def fetch_price_data(ticker, days):
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)

    df = yf.download(ticker, start_date, end_date)

    if df.empty:
        return None
    
    return df['Close'].round(2)

# set page layout
st.set_page_config(
    layout='wide',
    page_title='Stock Sentiment',
    page_icon='📊',
)

# header
st.markdown("<h2>Stock Sentiment Dashboard</h2>", unsafe_allow_html=True)

# chart placeholder
chart_placeholder = st.empty()

# form
with st.form("ticker_input"):
    ticker = st.text_input("Enter stock ticker (e.g. AAPL, AMZN)", None, 5)
    days = st.slider("Select number of past days to look at", min_value=1, max_value=365, value=30)
    submitted = st.form_submit_button("Submit")

if submitted:
    with st.spinner(f"Fetching data for {ticker.upper()}..."):
        close_prices = fetch_price_data(ticker, days)

        if close_prices is None:
            st.error("Invalid ticker or no data found.")
        else:
            chart_placeholder.line_chart(close_prices)
            st.success(f"Showing closing prices for {ticker.upper()} over the past {days} days.")