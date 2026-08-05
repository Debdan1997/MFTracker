from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st

# Set page config for mobile views
st.set_page_config(page_title="MF Tracker", page_icon="📈", layout="centered")

st.title("📈 Mutual Fund Tracker")

# Default Watchlist (Scheme Code : Display Name)
DEFAULT_FUNDS = {
    "125354": "Axis Small Cap Fund - Direct Growth",
    "122639": "Parag Parikh Flexi Cap Fund - Direct Growth",
    "119062": "HDFC Index S&P BSE Sensex - Direct Growth",
}


@st.cache_data(ttl=3600)  # Cache results for 1 hour to ensure quick reloads
def fetch_fund_data(code, name):
    try:
        url = f"https://api.mfapi.in/mf/{code}"
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            return None

        data = res.json().get("data", [])
        if not data or len(data) < 2:
            return None

        # Process NAV data into pandas DataFrame
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
        df["nav"] = df["nav"].astype(float)
        df = df.sort_values("date", ascending=False).reset_index(drop=True)

        latest_nav = df.iloc[0]["nav"]
        latest_date = df.iloc[0]["date"].strftime("%d %b %Y")

        # 1-Day Return
        prev_nav = df.iloc[1]["nav"]
        daily_change = ((latest_nav - prev_nav) / prev_nav) * 100

        # 30-Day Return (~30 calendar days ago)
        target_date = df.iloc[0]["date"] - timedelta(days=30)
        past_df = df[df["date"] <= target_date]
        if not past_df.empty:
            monthly_nav = past_df.iloc[0]["nav"]
            monthly_change = ((latest_nav - monthly_nav) / monthly_nav) * 100
        else:
            monthly_change = 0.0

        return {
            "name": name,
            "code": code,
            "latest_date": latest_date,
            "latest_nav": round(latest_nav, 2),
            "daily_pct": round(daily_change, 2),
            "monthly_pct": round(monthly_change, 2),
        }
    except Exception:
        return None


# Sidebar for managing watchlist
st.sidebar.header("Manage Watchlist")
if "watchlist" not in st.session_state:
    st.session_state.watchlist = DEFAULT_FUNDS.copy()

new_code = st.sidebar.text_input("Scheme Code (e.g., 125354)")
new_name = st.sidebar.text_input("Display Name")
if st.sidebar.button("Add Mutual Fund"):
    if new_code and new_name:
        st.session_state.watchlist[new_code.strip()] = new_name.strip()
        st.sidebar.success(f"Added {new_name}")
        st.rerun()

# Main Display Loop
funds_data = []
with st.spinner("Fetching latest NAVs..."):
    for code, name in st.session_state.watchlist.items():
        info = fetch_fund_data(code, name)
        if info:
            funds_data.append(info)

# Render Mobile-Friendly Metric Cards
if funds_data:
    for item in funds_data:
        st.subheader(item["name"])
        st.caption(
            f"NAV: ₹{item['latest_nav']} | Updated: {item['latest_date']}"
        )

        col1, col2 = st.columns(2)
        col1.metric("Daily Change", f"{item['daily_pct']}%", delta=item["daily_pct"])
        col2.metric(
            "30-Day Change", f"{item['monthly_pct']}%", delta=item["monthly_pct"]
        )
        st.divider()
else:
    st.warning("No data retrieved. Please check scheme codes or connection.")
