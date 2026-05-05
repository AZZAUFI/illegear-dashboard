import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = "T6d9c84acd6b1bf2d4-138a57ae68df0b79ab964e01ad2147ba"
SUBDOMAIN = "your_subdomain"  # Replace with your RepairShopr subdomain
BASE_URL = f"https://{SUBDOMAIN}.repairshopr.com/api/v1"

st.set_page_config(page_title="RepairShopr Monitor", layout="wide")

def fetch_tickets():
    headers = {'Authorization': f'Bearer {API_KEY}'}
    try:
        response = requests.get(f"{BASE_URL}/tickets", headers=headers)
        if response.status_code == 200:
            return response.json().get('tickets', [])
        else:
            st.error(f"Failed to fetch data: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return []

def main():
    st.title("🛠️ RepairShopr Critical Monitor")
    
    if st.button('🔄 Refresh Data'):
        st.rerun()

    tickets = fetch_tickets()
    
    if not tickets:
        st.warning("No active tickets found or API connection failed.")
        return

    # Process Data into DataFrame
    df = pd.DataFrame(tickets)
    
    # --- 1. SAFE IDENTIFICATION OF CUSTOMER REPLIES ---
    # We check if the column exists before filtering to avoid KeyError
    if 'has_unread_ticket_comments' in df.columns:
        replied_tickets = df[df['has_unread_ticket_comments'] == True].copy()
    else:
        replied_tickets = pd.DataFrame()

    # --- 2. SAFE IDENTIFICATION OF DUE/OVERDUE TICKETS ---
    if 'due_date' in df.columns:
        # errors='coerce' turns unparseable dates into NaT (Not a Time) instead of crashing
        df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce').dt.tz_localize(None)
        
        # Remove tickets that have no due date set
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
        st.header("📩 Unread Customer Replies")
        if not replied_tickets.empty:
            for _, row in replied_tickets.iterrows():
                # .get() provides a fallback if a specific field is missing in a row
                t_num = row.get('number', 'N/A')
                t_subj = row.get('subject', 'No Subject')
                t_cust = row.get('customer_business_then_name', 'Unknown Customer')
                st.info(f"**Ticket #{t_num}**: {t_subj}\n\n*Customer: {t_cust}*")
        else:
            st.success("No unread replies!")

    with col2:
        st.header("⏰ Due Date Alerts")
        
        if not overdue_tickets.empty:
            st.subheader("🚨 Overdue")
            for _, row in overdue_tickets.iterrows():
                t_num = row.get('number', 'N/A')
                d_date = row['due_date'].strftime('%Y-%m-%d %H:%M')
                st.error(f"**Ticket #{t_num}** - Due: {d_date}")
        
        if not near_due_tickets.empty:
            st.subheader("⚠️ Due Soon (Next 24h)")
            for _, row in near_due_tickets.iterrows():
                t_num = row.get('number', 'N/A')
                d_date = row['due_date'].strftime('%Y-%m-%d %H:%M')
                st.warning(f"**Ticket #{t_num}** - Due: {d_date}")
        
        if overdue_tickets.empty and near_due_tickets.empty:
            st.success("No tickets are overdue or due in the next 24 hours.")

if __name__ == "__main__":
    main()
