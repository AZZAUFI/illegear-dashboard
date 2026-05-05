import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = "T6d9c84acd6b1bf2d4-138a57ae68df0b79ab964e01ad2147ba"
SUBDOMAIN = "illegearticket" 
BASE_URL = f"https://{SUBDOMAIN}.repairshopr.com/api/v1"

st.set_page_config(page_title="Illegear Real-Time Monitor", layout="wide", initial_sidebar_state="collapsed")

# --- CSS & AUTO-REFRESH ---
# We use a single markdown block to handle styles and the 30s refresh meta-tag
st.markdown("""
    <meta http-equiv="refresh" content="30">
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
        min-height: 160px;
    }
    .indicator { height: 5px; width: 100%; position: absolute; top: 0; left: 0; border-radius: 4px 4px 0 0; }
    .status-unread { background: #00d4ff; box-shadow: 0 0 10px #00d4ff; }
    .status-overdue { background: #ff3e3e; box-shadow: 0 0 10px #ff3e3e; }
    .status-normal { background: #444; }
    
    .reply-tag {
        background: #00d4ff; color: black; font-size: 0.7rem;
        font-weight: bold; padding: 2px 6px; border-radius: 3px;
        display: inline-block; margin-bottom: 8px;
    }
    .due-tag { color: #ff3e3e; font-weight: bold; font-size: 0.85rem; margin-top: 10px; }
    .cust-name { font-size: 1.1rem; font-weight: bold; color: #fff; margin-bottom: 4px; }
    .ticket-subject { font-size: 0.85rem; color: #bbb; margin: 5px 0; line-height: 1.4; }
    .ref-no { font-size: 0.7rem; color: #666; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

def fetch_tickets():
    headers = {'Authorization': f'Bearer {API_KEY}'}
    try:
        response = requests.get(f"{BASE_URL}/tickets", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get('tickets', [])
    except Exception:
        pass
    return []

def main():
    st.markdown('<div class="main-header">ILLEGEAR COMMAND CENTER | AUTO-SYNC ACTIVE</div>', unsafe_allow_html=True)
    
    raw_tickets = fetch_tickets()
    if not raw_tickets:
        st.info("🛰️ Syncing signals... System standing by.")
        return

    df = pd.DataFrame(raw_tickets)
    now = datetime.now()
    
    # Safety checks for data columns
    if 'has_unread_ticket_comments' not in df.columns: df['has_unread_ticket_comments'] = False
    if 'due_date' not in df.columns: df['due_date'] = None
    
    df['due_date_dt'] = pd.to_datetime(df['due_date'], errors='coerce').dt.tz_localize(None)

    # Building the HTML string
    grid_html = '<div class="ticket-grid">'
    
    for _, row in df.iterrows():
        is_unread = row.get('has_unread_ticket_comments', False)
        due_dt = row['due_date_dt']
        is_overdue = pd.notnull(due_dt) and due_dt <= now
        
        # Define the Visual Tags
        reply_label = '<div class="reply-tag">📩 CUSTOMER REPLIED</div>' if is_unread else ""
        
        if pd.notnull(due_dt):
            due_time_str = due_dt.strftime('%d %b, %H:%M')
            due_label = f'<div class="due-tag">DUE: {due_time_str}</div>' if is_overdue else f'<div style="color:#888; font-size:0.8rem; margin-top:10px;">DUE: {due_time_str}</div>'
        else:
            due_label = '<div style="color:#444; font-size:0.8rem; margin-top:10px;">NO DUE DATE</div>'
        
        # Indicator logic
        indicator_style = "status-normal"
        if is_overdue: indicator_style = "status-overdue"
        elif is_unread: indicator_style = "status-unread"

        # Construct individual box
        grid_html += f"""
        <div class="ticket-box">
            <div class="indicator {indicator_style}"></div>
            {reply_label}
            <div class="ref-no">REF: #{row.get('number', '0000')}</div>
            <div class="cust-name">{row.get('customer_business_then_name', 'Unknown Customer')}</div>
            <div class="ticket-subject">{str(row.get('subject', 'No Subject'))[:70]}</div>
            {due_label}
        </div>
        """
    
    grid_html += '</div>'
    
    # FINAL RENDER: This must be the only call to display the grid
    st.markdown(grid_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
