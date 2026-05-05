import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = "T6d9c84acd6b1bf2d4-138a57ae68df0b79ab964e01ad2147ba"
SUBDOMAIN = "illegearticket" 
BASE_URL = f"https://{SUBDOMAIN}.repairshopr.com/api/v1"

st.set_page_config(page_title="Illegear Live Monitor", layout="wide", initial_sidebar_state="collapsed")

def fetch_tickets():
    headers = {'Authorization': f'Bearer {API_KEY}'}
    try:
        response = requests.get(f"{BASE_URL}/tickets", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get('tickets', [])
    except: pass
    return []

def main():
    # Regular Streamlit Header
    st.markdown('<h1 style="color:#00ffcc; text-align:center; font-family:monospace; border:1px solid #00ffcc; padding:10px;">ILLEGEAR COMMAND CENTER</h1>', unsafe_allow_html=True)
    
    raw_tickets = fetch_tickets()
    if not raw_tickets:
        st.info("🛰️ Syncing signals...")
        return

    df = pd.DataFrame(raw_tickets)
    now = datetime.now()
    
    # Data Normalization
    if 'has_unread_ticket_comments' not in df.columns: df['has_unread_ticket_comments'] = False
    if 'due_date' not in df.columns: df['due_date'] = None
    df['due_date_dt'] = pd.to_datetime(df['due_date'], errors='coerce').dt.tz_localize(None)

    # --- HTML & CSS CONSTRUCTION ---
    # We build the entire page (Styles + Refresh + Grid) as one string
    grid_items = ""
    for _, row in df.iterrows():
        is_unread = row.get('has_unread_ticket_comments', False)
        due_dt = row['due_date_dt']
        is_overdue = pd.notnull(due_dt) and due_dt <= now
        
        indicator = "status-normal"
        if is_overdue: indicator = "status-overdue"
        elif is_unread: indicator = "status-unread"

        reply_tag = '<div class="reply-tag">📩 CUSTOMER REPLIED</div>' if is_unread else ""
        due_color = "#ff3e3e" if is_overdue else "#888"
        due_val = due_dt.strftime('%d %b, %H:%M') if pd.notnull(due_dt) else "NO DUE DATE"

        grid_items += f"""
        <div class="ticket-box">
            <div class="indicator {indicator}"></div>
            {reply_tag}
            <div class="ref-no">REF: #{row.get('number', '0000')}</div>
            <div class="cust-name">{row.get('customer_business_then_name', 'Unknown')}</div>
            <div class="ticket-subject">{str(row.get('subject', ''))[:60]}</div>
            <div class="due-tag" style="color:{due_color}">DUE: {due_val}</div>
        </div>"""

    full_html = f"""
    <meta http-equiv="refresh" content="30">
    <style>
        body {{ background-color: #05070a; color: #e0e0e0; font-family: sans-serif; margin: 0; }}
        .ticket-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px; padding: 20px;
        }}
        .ticket-box {{
            background: #11141b; border: 1px solid #2d3139;
            border-radius: 4px; padding: 15px; position: relative;
        }}
        .indicator {{ height: 5px; width: 100%; position: absolute; top: 0; left: 0; }}
        .status-unread {{ background: #00d4ff; box-shadow: 0 0 10px #00d4ff; }}
        .status-overdue {{ background: #ff3e3e; box-shadow: 0 0 10px #ff3e3e; }}
        .status-normal {{ background: #444; }}
        .reply-tag {{ background: #00d4ff; color: black; font-size: 10px; font-weight: bold; padding: 2px 5px; border-radius: 3px; display: inline-block; margin-bottom: 5px; }}
        .cust-name {{ font-size: 18px; font-weight: bold; color: white; margin: 5px 0; }}
        .ticket-subject {{ font-size: 14px; color: #bbb; min-height: 40px; }}
        .ref-no {{ font-size: 11px; color: #666; }}
        .due-tag {{ font-size: 13px; font-weight: bold; margin-top: 10px; }}
    </style>
    <div class="ticket-grid">
        {grid_items}
    </div>
    """

    # --- THE MAGIC FIX ---
    # We use components.html which creates a dedicated frame for the HTML
    # height should be large enough to handle your grid (e.g., 2000px)
    components.html(full_html, height=1200, scrolling=True)

if __name__ == "__main__":
    main()
