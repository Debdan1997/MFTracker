from datetime import datetime, timedelta
import requests
import streamlit as st

st.set_page_config(page_title="MF Tracker", page_icon="📈", layout="centered")
st.title("📈 Mutual Fund Tracker")

DEFAULT_FUNDS = {
    "125354": "Axis Small Cap Fund - Direct Growth",
    "122639": "Parag Parikh Flexi Cap Fund - Direct Growth",
    "119062": "HDFC Index S&P BSE Sensex - Direct Growth",
}


@st.cache_data(ttl=3600)
def fetch_fund_data(code, name):
    try:
        url = f"https://api.mfapi.in/mf/{code}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            st.error(
                f"Failed to fetch data for {name} (HTTP {res.status_code})"
            )
            return None

        data = res.json().get("data", [])
        if not data or len(data) < 2:
            st.warning(f"Insufficient historical data for {name}")
            return None

        # Parse JSON array into a clean list of dicts with parsed dates & floats
        parsed_data = []
        for item in data:
            try:
                dt = datetime.strptime(item["date"], "%d-%m-%Y")
                nav = float(item["nav"])
                parsed_data.append({"date": dt, "nav": nav})
            except (ValueError, TypeError):
                continue

        # Ensure sorted descending by date (latest first)
        parsed_data.sort(key=lambda x: x["date"], reverse=True)

        if len(parsed_data) < 2:
            return None

        latest_entry = parsed_data[0]
        latest_nav = latest_entry["nav"]
        latest_date_str = latest_entry["date"].strftime("%d %b %Y")

        # Helper: Find the closest NAV on or before target past date
        def get_past_nav(target_date):
            for entry in parsed_data:
                if entry["date"] <= target_date:
                    return entry["nav"]
            return None

        # 1-Day Change
        prev_nav = parsed_data[1]["nav"]
        daily_pct = (
            round(((latest_nav - prev_nav) / prev_nav) * 100, 2)
            if prev_nav > 0
            else 0.0
        )

        # 1-Month (30 Days) Change
        target_30d = latest_entry["date"] - timedelta(days=30)
        nav_30d = get_past_nav(target_30d)
        monthly_pct = (
            round(((latest_nav - nav_30d) / nav_30d) * 100, 2)
            if nav_30d
            else 0.0
        )

        # 3-Month (90 Days) Change
        target_90d = latest_entry["date"] - timedelta(days=90)
        nav_90d = get_past_nav(target_90d)
        three_month_pct = (
            round(((latest_nav - nav_90d) / nav_90d) * 100, 2)
            if nav_90d
            else 0.0
        )

        return {
            "name": name,
            "code": code,
            "latest_date": latest_date_str,
            "latest_nav": round(latest_nav, 2),
            "daily_pct": daily_pct,
            "monthly_pct": monthly_pct,
            "three_month_pct": three_month_pct,
        }
    except Exception as e:
        st.error(f"Error processing {name}: {str(e)}")
        return None


# Sidebar
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

# Display
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
    st.info("No fund data to display.")
