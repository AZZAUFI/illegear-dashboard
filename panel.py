import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone

# --- CONFIGURATION ---
API_KEY = "T6d9c84acd6b1bf2d4-138a57ae68df0b79ab964e01ad2147ba"
SUBDOMAIN = "illegearticket"  # Replace with your RepairShopr subdomain
BASE_URL = f"https://{SUBDOMAIN}.repairshopr.com/api/v1"

st.set_page_config(page_title="RepairShopr Monitor", layout="wide")

def fetch_tickets():
    headers = {'Authorization': f'Bearer {API_KEY}'}
    # Fetching the most recent 50 tickets
    response = requests.get(f"{BASE_URL}/tickets", headers=headers)
    if response.status_code == 200:
        return response.json()['tickets']
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return []

def main():
    st.title("🛠️ RepairShopr Critical Monitor")
    
    if st.button('🔄 Refresh Data'):
        st.rerun()

    tickets = fetch_tickets()
    
    if not tickets:
        st.warning("No tickets found or API connection failed.")
        return

    # Process Data
    df = pd.DataFrame(tickets)
    
    # 1. IDENTIFY CUSTOMER REPLIES
    # RepairShopr often flags tickets with 'has_unread_ticket_comments' 
    # or we check if the 'last_comment_type' is from a customer.
    replied_tickets = df[df['has_unread_ticket_comments'] == True]

    # 2. IDENTIFY DUE/OVERDUE TICKETS
    # Convert string dates to datetime objects
    df['due_date'] = pd.to_datetime(df['due_date']).dt.tz_localize(None)
    now = datetime.now()
    
    # Filter for tickets due within 24 hours or already overdue
    overdue_tickets = df[df['due_date'] <= now]
    near_due_tickets = df[(df['due_date'] > now) & 
                          (df['due_date'] <= now + pd.Timedelta(hours=24))]

    # --- UI DISPLAY ---
    col1, col2 = st.columns(2)

    with col1:
        st.header("📩 Unread Customer Replies")
        if not replied_tickets.empty:
            for _, row in replied_tickets.iterrows():
                st.info(f"**Ticket #{row['number']}**: {row['subject']}\n\n*Customer: {row['customer_business_then_name']}*")
        else:
            st.success("No unread replies!")

    with col2:
        st.header("⏰ Due Date Alerts")
        
        if not overdue_tickets.empty:
            st.subheader("🚨 Overdue")
            for _, row in overdue_tickets.iterrows():
                st.error(f"**Ticket #{row['number']}** - Due: {row['due_date'].strftime('%Y-%m-%d %H:%M')}")
        
        if not near_due_tickets.empty:
            st.subheader("⚠️ Due Soon (Next 24h)")
            for _, row in near_due_tickets.iterrows():
                st.warning(f"**Ticket #{row['number']}** - Due: {row['due_date'].strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()