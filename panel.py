import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
# Based on your link: https://illegearticket.repairshopr.com
API_KEY = "T6d9c84acd6b1bf2d4-138a57ae68df0b79ab964e01ad2147ba"
SUBDOMAIN = "illegearticket" 
BASE_URL = f"https://{SUBDOMAIN}.repairshopr.com/api/v1"

st.set_page_config(page_title="Illegear Ticket Monitor", layout="wide")

def fetch_tickets():
    headers = {'Authorization': f'Bearer {API_KEY}'}
    try:
        # We use a timeout to prevent the app from hanging if the API is slow
        response = requests.get(f"{BASE_URL}/tickets", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get('tickets', [])
        else:
            st.error(f"API Error {response.status_code}: Please check if your API Key is valid.")
            return []
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return []

def main():
    st.title("🛠️ Illegear Critical Ticket Monitor")
    
    # Sidebar for quick stats
    st.sidebar.header("Dashboard Controls")
    if st.sidebar.button('🔄 Refresh Data'):
        st.rerun()

    tickets = fetch_tickets()
    
    if not tickets:
        st.info("No tickets currently match the criteria or the API returned an empty list.")
        return

    df = pd.DataFrame(tickets)
    
    # --- 1. FILTER CUSTOMER REPLIES ---
    # RepairShopr uses 'has_unread_ticket_comments' for new replies
    if 'has_unread_ticket_comments' in df.columns:
        replied_tickets = df[df['has_unread_ticket_comments'] == True].copy()
    else:
        replied_tickets = pd.DataFrame()

    # --- 2. FILTER DUE/OVERDUE ---
    if 'due_date' in df.columns:
        df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce').dt.tz_localize(None)
        df_dates = df.dropna(subset=['due_date'])
        
        now = datetime.now()
        overdue_tickets = df_dates[df_dates['due_date'] <= now].copy()
        near_due_tickets = df_dates[(df_dates['due_date'] > now) & 
                                    (df_dates['due_date'] <= now + pd.Timedelta(hours=24))].copy()
    else:
        overdue_tickets = pd.DataFrame()
        near_due_tickets = pd.DataFrame()

    # --- UI DISPLAY ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📩 Unread Replies")
        if not replied_tickets.empty:
            for _, row in replied_tickets.iterrows():
                with st.expander(f"Ticket #{row.get('number')} - {row.get('subject')[:30]}...", expanded=True):
                    st.write(f"**Customer:** {row.get('customer_business_then_name')}")
                    st.write(f"**Status:** {row.get('status')}")
        else:
            st.success("All customer messages have been read.")

    with col2:
        st.subheader("⏰ Deadline Watch")
        
        if not overdue_tickets.empty:
            st.error(f"**{len(overdue_tickets)} Tickets Overdue**")
            for _, row in overdue_tickets.iterrows():
                st.write(f"❌ **#{row.get('number')}** - Due: {row['due_date'].strftime('%d %b, %H:%M')}")
        
        if not near_due_tickets.empty:
            st.warning(f"**{len(near_due_tickets)} Tickets Due within 24h**")
            for _, row in near_due_tickets.iterrows():
                st.write(f"⚠️ **#{row.get('number')}** - Due: {row['due_date'].strftime('%d %b, %H:%M')}")
        
        if overdue_tickets.empty and near_due_tickets.empty:
            st.success("No immediate deadlines pending.")

if __name__ == "__main__":
    main()
