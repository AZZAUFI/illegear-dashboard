import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# --- CONFIGURATION ---
API_KEY = "T6d9c84acd6b1bf2d4-138a57ae68df0b79ab964e01ad2147ba"
SUBDOMAIN = "illegearticket" 
BASE_URL = f"https://{SUBDOMAIN}.repairshopr.com/api/v1"

st.set_page_config(page_title="Illegear Real-Time Monitor", layout="wide", initial_sidebar_state="collapsed")

# --- AUTO-REFRESH & STYLING ---
# The meta tag below refreshes the browser every 30 seconds
st.markdown("""
    <head><meta http-equiv="refresh" content="30"></head>
    <style>
    .stApp { background-color: #05070a; color: #e0e0e0; }
    header {visibility: hidden;}
    .main-header {
        font-family: 'Courier New', monospace;
        color: #00ffcc; text-align: center; font-size: 1.5rem;
        padding: 10px; border: 1px solid #00ffcc; margin-bottom: 20px;
    }
    .ticket-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 15px; padding: 10px;
    }
    .ticket-box {
        background: #11141b; border: 1px solid #2d3139;
        border-radius: 4px; padding: 15px; position: relative;
    }
    .indicator { height: 5px; width: 100%; position: absolute; top: 0; left: 0; }
    .status-unread { background: #00d4ff; box-shadow: 0 0 10px #00d4ff; }
    .status-overdue { background: #ff3e3e; box-shadow: 0 0 10px #ff3e3e; }
    .status-normal { background: #444; }
    
    .reply-tag {
        background: #00d4ff; color: black; font-size: 0.7rem;
        font-weight: bold; padding: 2px 6px; border-radius: 3px;
        display: inline-block; margin-bottom: 5px;
    }
    .due-tag { color: #ff3e3e; font-weight: bold; font-size: 0.85rem; }
    .cust-name { font-size: 1.1rem; font-weight: bold; color: #fff; }
    .ticket-subject { font-size: 0.85rem; color: #bbb; margin: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

def fetch_tickets():
    headers = {'Authorization': f'Bearer {API_KEY}'}
    try:
        response = requests.get(f"{BASE_URL}/tickets", headers=headers, timeout=10)
        return response.json().get('tickets', []) if response.status_code == 200 else []
    except: return []

def main():
    st.markdown('<div class="main-header">ILLEGEAR COMMAND CENTER | AUTO-SYNC ACTIVE</div>', unsafe_allow_html=True)
    
    tickets = fetch_tickets()
    if not tickets:
        st.info("🛰️ Syncing signals... Please wait.")
        return

    df = pd.DataFrame(tickets)
    now = datetime.now()
    
    # Ensure columns exist
    if 'has_unread_ticket_comments' not in df.columns: df['has_unread_ticket_comments'] = False
    if 'due_date' not in df.columns: df['due_date'] = None
    
    df['due_date_dt'] = pd.to_datetime(df['due_date'], errors='coerce').dt.tz_localize(None)

    grid_items = ""
    for _, row in df.iterrows():
        is_unread = row['has_unread_ticket_comments']
        due_dt = row['due_date_dt']
        is_overdue = pd.notnull(due_dt) and due_dt <= now
        
        # UI Logic for Tags
        reply_html = '<div class="reply-tag">📩 CUSTOMER REPLIED</div>' if is_unread else ""
        
        due_str = due_dt.strftime('%d %b, %H:%M') if pd.notnull(due_dt) else "No Deadline"
        due_html = f'<div class="due-tag">DUE: {due_str}</div>' if is_overdue else f'<div style="color:#888; font-size:0.8rem;">DUE: {due_str}</div>'
        
        # Color indicator priority: Overdue (Red) > Unread (Blue)
        indicator_class = "status-normal"
        if is_overdue: indicator_class = "status-overdue"
        elif is_unread: indicator_class = "status-unread"

        grid_items += f"""
        <div class="ticket-box">
            <div class="indicator {indicator_class}"></div>
            {reply_html}
            <div style="font-size: 0.7rem; color: #666;">REF: #{row.get('number')}</div>
            <div class="cust-name">{row.get('customer_business_then_name', 'N/A')}</div>
            <div class="ticket-subject">{str(row.get('subject', ''))[:50]}</div>
            {due_html}
        </div>"""
    
    st.markdown(f'<div class="ticket-grid">{grid_items}</div>', unsafe_allow_html=True)
    
    # Optional: Display countdown to next sync
    st.sidebar.write(f"Last Sync: {now.strftime('%H:%M:%S')}")
    st.sidebar.write("Auto-refreshing every 30s...")

if __name__ == "__main__":
    main()
