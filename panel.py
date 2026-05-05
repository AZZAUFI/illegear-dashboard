import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = "T6d9c84acd6b1bf2d4-138a57ae68df0b79ab964e01ad2147ba"
SUBDOMAIN = "illegearticket" 
BASE_URL = f"https://{SUBDOMAIN}.repairshopr.com/api/v1"

st.set_page_config(page_title="Illegear Command Center", layout="wide", initial_sidebar_state="collapsed")

# --- MODERN HOSPITAL UI STYLING ---
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Header styling */
    .main-header {
        font-family: 'Courier New', Courier, monospace;
        color: #00ffcc;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
        padding: 10px;
        border-bottom: 2px solid #00ffcc;
        margin-bottom: 20px;
    }

    /* Panel Card Styling */
    .status-card {
        background-color: #1a1c24;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #00ffcc;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0, 255, 204, 0.1);
    }

    .critical-card {
        background-color: #241a1a;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.1);
    }
    
    /* Heartbeat animation */
    .heartbeat {
        color: #ff4b4b;
        animation: beat .25s infinite alternate;
        display: inline-block;
    }
    @keyframes beat{
        to { transform: scale(1.2); }
    }

    /* Metric numbers */
    .metric-val {
        font-size: 2.5rem;
        font-weight: bold;
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

def fetch_tickets():
    headers = {'Authorization': f'Bearer {API_KEY}'}
    try:
        response = requests.get(f"{BASE_URL}/tickets", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get('tickets', [])
        return []
    except:
        return []

def main():
    # --- TOP BAR ---
    st.markdown('<h1 class="main-header">✚ ILLEGEAR TICKET COMMAND CENTER</h1>', unsafe_allow_html=True)
    
    col_t1, col_t2, col_t3 = st.columns([1, 1, 1])
    with col_t2:
        st.markdown(f"<div style='text-align:center; color:#888;'>SYSTEM LIVE | LAST SYNC: {datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)
    
    tickets = fetch_tickets()
    df = pd.DataFrame(tickets)

    # --- DATA PROCESSING ---
    unread = pd.DataFrame()
    overdue = pd.DataFrame()
    near_due = pd.DataFrame()

    if not df.empty:
        if 'has_unread_ticket_comments' in df.columns:
            unread = df[df['has_unread_ticket_comments'] == True]
        
        if 'due_date' in df.columns:
            df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce').dt.tz_localize(None)
            now = datetime.now()
            overdue = df[df['due_date'] <= now].dropna(subset=['due_date'])
            near_due = df[(df['due_date'] > now) & (df['due_date'] <= now + pd.Timedelta(hours=24))]

    # --- TOP METRICS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("PENDING REPLIES", len(unread))
    m2.metric("OVERDUE", len(overdue), delta_color="inverse")
    m3.metric("DUE 24H", len(near_due))

    st.markdown("---")

    # --- MAIN DASHBOARD GRID ---
    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown("### <span class='heartbeat'>♥</span> INCOMING REPLIES", unsafe_allow_html=True)
        if not unread.empty:
            for _, row in unread.iterrows():
                st.markdown(f"""
                <div class="status-card">
                    <div style="color:#00ffcc; font-size:0.8rem;">PATIENT/TICKET #{row.get('number')}</div>
                    <div style="font-size:1.2rem; font-weight:bold; color:white;">{row.get('customer_business_then_name')}</div>
                    <div style="color:#aaa;">{row.get('subject')[:50]}...</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No active alerts.")

    with right_col:
        st.markdown("### ⚠️ CRITICAL DEADLINES", unsafe_allow_html=True)
        
        # Show Overdue First
        if not overdue.empty:
            for _, row in overdue.iterrows():
                st.markdown(f"""
                <div class="critical-card">
                    <div style="color:#ff4b4b; font-size:0.8rem;">STATUS: OVERDUE</div>
                    <div style="font-size:1.2rem; font-weight:bold; color:white;">Ticket #{row.get('number')}</div>
                    <div style="color:#ff8888;">Expired: {row['due_date'].strftime('%H:%M | %d %b')}</div>
                </div>
                """, unsafe_allow_html=True)

        # Show Near Due
        if not near_due.empty:
            for _, row in near_due.iterrows():
                st.markdown(f"""
                <div class="status-card" style="border-left: 5px solid #f1c40f;">
                    <div style="color:#f1c40f; font-size:0.8rem;">STATUS: NEAR EXPIRY</div>
                    <div style="font-size:1.1rem; font-weight:bold; color:white;">Ticket #{row.get('number')}</div>
                    <div style="color:#aaa;">Due in: {((row['due_date'] - datetime.now()).seconds // 3600)} Hours</div>
                </div>
                """, unsafe_allow_html=True)

    # --- AUTO-REFRESH BUTTON ---
    if st.button('MANUAL SYSTEM RE-SCAN'):
        st.rerun()

if __name__ == "__main__":
    main()
