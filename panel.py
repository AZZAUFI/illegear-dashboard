import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = "T6d9c84acd6b1bf2d4-138a57ae68df0b79ab964e01ad2147ba"
SUBDOMAIN = "illegearticket" 
BASE_URL = f"https://{SUBDOMAIN}.repairshopr.com/api/v1"

st.set_page_config(page_title="Illegear Command Center", layout="wide", initial_sidebar_state="collapsed")

# --- CSS STYLING ---
# Ensure there are NO spaces between the triple quotes and the <style> tag
st.markdown("""<style>
    .stApp { background-color: #05070a; color: #e0e0e0; }
    header {visibility: hidden;}
    .main-header {
        font-family: 'Courier New', monospace;
        color: #00ffcc;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        padding: 10px;
        border: 1px solid #00ffcc;
        margin-bottom: 20px;
    }
    .ticket-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 15px;
        padding: 10px;
    }
    .ticket-box {
        background: #11141b;
        border: 1px solid #2d3139;
        border-radius: 4px;
        padding: 15px;
        position: relative;
    }
    .indicator {
        height: 5px; width: 100%; position: absolute;
        top: 0; left: 0; border-radius: 4px 4px 0 0;
    }
    .status-unread { background: #00d4ff; }
    .status-overdue { background: #ff3e3e; }
    .status-warning { background: #ffaa00; }
    .status-normal { background: #444; }
    .ticket-no { font-size: 0.75rem; color: #888; }
    .cust-name { font-size: 1.1rem; font-weight: bold; color: #fff; }
    .ticket-subject { font-size: 0.85rem; color: #bbb; margin: 8px 0; }
    div[data-testid="stMetricValue"] { color: #00ffcc !important; }
</style>""", unsafe_allow_html=True)

def fetch_tickets():
    headers = {'Authorization': f'Bearer {API_KEY}'}
    try:
        response = requests.get(f"{BASE_URL}/tickets", headers=headers, timeout=10)
        return response.json().get('tickets', []) if response.status_code == 200 else []
    except: return []

def main():
    st.markdown('<div class="main-header">ILLEGEAR LIVE TICKET MONITOR</div>', unsafe_allow_html=True)
    tickets = fetch_tickets()
    
    if not tickets:
        st.info("🛰️ Scanning for active signals...")
        return

    df = pd.DataFrame(tickets)
    if 'has_unread_ticket_comments' not in df.columns: df['has_unread_ticket_comments'] = False
    if 'due_date' not in df.columns: df['due_date'] = None

    now = datetime.now()
    df['due_date_dt'] = pd.to_datetime(df['due_date'], errors='coerce').dt.tz_localize(None)

    m1, m2, m3 = st.columns(3)
    m1.metric("TOTAL SYSTEMS", len(df))
    m2.metric("UNREAD", len(df[df['has_unread_ticket_comments'] == True]))
    m3.metric("OVERDUE", len(df[df['due_date_dt'] <= now].dropna(subset=['due_date_dt'])))

    # --- GRID RENDERING ---
    grid_items = ""
    for _, row in df.iterrows():
        is_unread = row['has_unread_ticket_comments']
        is_overdue = pd.notnull(row['due_date_dt']) and row['due_date_dt'] <= now
        
        status = "status-normal"
        if is_overdue: status = "status-overdue"
        elif is_unread: status = "status-unread"

        # Build individual ticket HTML
        grid_items += f"""
        <div class="ticket-box">
            <div class="indicator {status}"></div>
            <div class="ticket-no">REF: #{row.get('number', '???')}</div>
            <div class="cust-name">{row.get('customer_business_then_name', 'UNKNOWN')}</div>
            <div class="ticket-subject">{str(row.get('subject', 'No Subject'))[:60]}</div>
        </div>"""
    
    # Render the final container
    st.markdown(f'<div class="ticket-grid">{grid_items}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
