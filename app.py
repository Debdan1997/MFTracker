from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="MF Tracker", page_icon="📈", layout="centered")
st.title("📈 Mutual Fund Tracker")

DEFAULT_FUNDS = {
    "122639": "Parag Parikh Flexi Cap Fund - Direct Growth",
}

@st.cache_data(ttl=3600)
def fetch_fund_data(code, name):
    try:
        url = f"https://api.mfapi.in/mf/{code}"
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            return None

        data = res.json().get("data", [])
        if not data or len(data) < 2:
            return None

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
        df["nav"] = df["nav"].astype(float)
        df = df.sort_values("date", ascending=False).reset_index(drop=True)

        latest_nav = df.iloc[0]["nav"]
        latest_date = df.iloc[0]["date"].strftime("%d %b %Y")

        # Helper function to compute percentage change against a target past date
        def get_pct_change_for_days(days):
            target_date = df.iloc[0]["date"] - timedelta(days=days)
            past_df = df[df["date"] <= target_date]
            if not past_df.empty:
                past_nav = past_df.iloc[0]["nav"]
                return round(((latest_nav - past_nav) / past_nav) * 100, 2)
            return 0.0

        # 1-Day Return
        prev_nav = df.iloc[1]["nav"]
        daily_change = round(((latest_nav - prev_nav) / prev_nav) * 100, 2)

        # 1-Month (30 Days) Return
        monthly_change = get_pct_change_for_days(30)

        # 3-Month (90 Days) Return
        three_month_change = get_pct_change_for_days(90)

        return {
            "name": name,
            "code": code,
            "latest_date": latest_date,
            "latest_nav": round(latest_nav, 2),
            "daily_pct": daily_change,
            "monthly_pct": monthly_change,
            "three_month_pct": three_month_change,
        }
    except Exception:
        return None


# Sidebar Watchlist
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

# Display Metrics
funds_data = []
with st.spinner("Fetching latest NAVs..."):
    for code, name in st.session_state.watchlist.items():
        info = fetch_fund_data(code, name)
        if info:
            funds_data.append(info)

if funds_data:
    for item in funds_data:
        st.subheader(item["name"])
        st.caption(
            f"NAV: ₹{item['latest_nav']} | Updated: {item['latest_date']}"
        )

        # Render 3 Columns for 1D, 1M, and 3M
        col1, col2, col3 = st.columns(3)
        col1.metric("1-Day", f"{item['daily_pct']}%", delta=item["daily_pct"])
        col2.metric(
            "1-Month", f"{item['monthly_pct']}%", delta=item["monthly_pct"]
        )
        col3.metric(
            "3-Month",
            f"{item['three_month_pct']}%",
            delta=item["three_month_pct"],
        )
        st.divider()
else:
    st.warning("No data retrieved.")
