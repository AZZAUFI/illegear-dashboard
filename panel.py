import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = "T6d9c84acd6b1bf2d4-138a57ae68df0b79ab964e01ad2147ba"
SUBDOMAIN = "illegearticket" 
BASE_URL = f"https://{SUBDOMAIN}.repairshopr.com/api/v1"

st.set_page_config(page_title="Illegear Command Center", layout="wide", initial_sidebar_state="collapsed")

# --- RESPONSIVE AUTO-GRID STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #e0e0e0; }
    header {visibility: hidden;}
    
    /* Title Bar */
    .main-header {
        font-family: 'Courier New', monospace;
        color: #00ffcc;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        padding: 10px;
        border: 1px solid #00ffcc;
        margin-bottom: 20px;
        box-shadow: 0 0 10px rgba(0, 255, 204, 0.2);
    }

    /* THE MAGIC: Auto-detecting Responsive Grid */
    .ticket-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 15px;
        padding: 10px;
    }

    /* Individual Ticket Box */
    .ticket-box {
        background: #11141b;
        border: 1px solid #2d3139;
        border-radius: 4px;
        padding: 15px;
        position: relative;
        transition: transform 0.2s;
    }
    
    .ticket-box:hover {
        border-color: #00ffcc;
        transform: translateY(-2px);
    }

    /* Status Indicators */
    .indicator {
        height: 4px;
        width: 100%;
        position: absolute;
        top: 0;
        left: 0;
        border-radius: 4px 4px 0 0;
    }
    .status-unread { background: #00d4ff; box-shadow: 0 0 10px #00d4ff; }
    .status-overdue { background: #ff3e3e; box-shadow: 0 0 10px #ff3e3e; }
    .status-warning { background: #ffaa00; box-shadow: 0 0 10px #ffaa00; }
    .status-normal { background: #444; }

    .ticket-no { font-size: 0.75rem; color: #888; font-family: monospace; }
    .cust-name { font-size: 1.1rem; font-weight: bold; color: #fff; margin-top: 5px; }
    .ticket-subject { font-size: 0.85rem; color: #bbb; margin: 8px 0; min-height: 40px; }
    .ticket-time { font-size: 0.8rem; font-weight: bold; }
    
    /* Metric styling */
    div[data-testid="stMetricValue"] { color: #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

def fetch_tickets():
    headers = {'Authorization': f'Bearer {API_KEY}'}
    try:
        response = requests.get(f"{BASE_URL}/tickets", headers=headers, timeout=10)
        return response.json().get('tickets', []) if response.status_code == 200 else []
    except: return []

def main():
    st.markdown('<div class="main-header">ILLEGEAR LIVE TICKET MONITOR</div>', unsafe_allow_html=True)
    
    # Top Stats
    tickets = fetch_tickets()
    df = pd.DataFrame(tickets)
    
    if df.empty:
        st.info("Searching for active signals...")
        return

    # Process Times
    now = datetime.now()
    df['due_date_dt'] = pd.to_datetime(df['due_date'], errors='coerce').dt.tz_localize(None)

    # Metrics
    unread_count = len(df[df.get('has_unread_ticket_comments', False) == True])
    overdue_count = len(df[df['due_date_dt'] <= now].dropna(subset=['due_date_dt']))
    
    m1, m2, m3 = st.columns(3)
    m1.metric("ACTIVE SYSTEMS", len(df))
    m2.metric("UNREAD REPLIES", unread_count)
    m3.metric("CRITICAL OVERDUE", overdue_count)

    # Building the Grid
    grid_html = '<div class="ticket-grid">'
    
    for _, row in df.iterrows():
        # Determine Status
        status_class = "status-normal"
        status_text = "STABLE"
        time_display = ""
        
        is_unread = row.get('has_unread_ticket_comments', False)
        is_overdue = pd.notnull(row['due_date_dt']) and row['due_date_dt'] <= now
        is_near = pd.notnull(row['due_date_dt']) and (now < row['due_date_dt'] <= now + pd.Timedelta(hours=24))

        if is_overdue:
            status_class = "status-overdue"
            status_text = "CRITICAL: OVERDUE"
            time_display = row['due_date_dt'].strftime('%d %b %H:%M')
        elif is_unread:
            status_class = "status-unread"
            status_text = "NEW MESSAGE"
            time_display = "Action Required"
        elif is_near:
            status_class = "status-warning"
            status_text = "URGENT: DUE SOON"
            time_display = row['due_date_dt'].strftime('%H:%M Today')
        
        grid_html += f"""
        <div class="ticket-box">
            <div class="indicator {status_class}"></div>
            <div class="ticket-no">REF: #{row.get('number')}</div>
            <div class="cust-name">{row.get('customer_business_then_name', 'UNKNOWN')}</div>
            <div class="ticket-subject">{row.get('subject', 'No Subject')[:60]}</div>
            <div class="ticket-time" style="color: {'#ff3e3e' if is_overdue else '#00d4ff' if is_unread else '#ffaa00' if is_near else '#888'}">
                {status_text} <br> {time_display}
            </div>
        </div>
        """
    
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    # Invisible auto-refresh (reloads every time user interacts or clicks)
    if st.button('REFRESH SCAN'):
        st.rerun()

if __name__ == "__main__":
    main()
