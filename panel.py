import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = "T6d9c84acd6b1bf2d4-138a57ae68df0b79ab964e01ad2147ba"
SUBDOMAIN = "illegearticket" 
BASE_URL = f"https://{SUBDOMAIN}.repairshopr.com/api/v1"

# Force wide mode and hide sidebar for maximum screen real estate
st.set_page_config(page_title="Illegear Command Center", layout="wide", initial_sidebar_state="collapsed")

# --- GRID & HOSPITAL UI STYLING ---
st.markdown("""
    <style>
    /* Global Styles */
    .stApp { background-color: #05070a; color: #e0e0e0; }
    header {visibility: hidden;}
    .main-header {
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #00ffcc;
        text-align: center;
        font-size: 1.8rem;
        font-weight: 800;
        letter-spacing: 3px;
        margin-bottom: 5px;
        padding: 10px;
        background: rgba(0, 255, 204, 0.05);
        border-bottom: 1px solid #00ffcc;
    }

    /* Fixed Height Scrollable Containers */
    .grid-container {
        height: 75vh;
        overflow-y: auto;
        padding-right: 10px;
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #0e1117; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }

    /* Panel Card Styling */
    .panel-card {
        background: #11141a;
        border-radius: 4px;
        padding: 12px;
        margin-bottom: 8px;
        border-left: 4px solid #444;
    }
    .unread-border { border-left-color: #00d4ff; box-shadow: inset 5px 0 10px -5px #00d4ff; }
    .overdue-border { border-left-color: #ff3e3e; box-shadow: inset 5px 0 10px -5px #ff3e3e; }
    .neardue-border { border-left-color: #ffaa00; box-shadow: inset 5px 0 10px -5px #ffaa00; }

    .card-id { font-size: 0.7rem; color: #888; font-weight: bold; }
    .card-title { font-size: 1rem; font-weight: 700; color: #fff; margin: 2px 0; }
    .card-meta { font-size: 0.8rem; color: #bbb; }
    
    /* Metric styling */
    div[data-testid="stMetricValue"] { font-size: 2rem !important; color: #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

def fetch_tickets():
    headers = {'Authorization': f'Bearer {API_KEY}'}
    try:
        response = requests.get(f"{BASE_URL}/tickets", headers=headers, timeout=10)
        return response.json().get('tickets', []) if response.status_code == 200 else []
    except:
        return []

def main():
    st.markdown('<div class="main-header">ILLEGEAR COMMAND CENTER : MONITOR 01</div>', unsafe_allow_html=True)
    
    # Auto-refresh helper (simulated by a small button)
    cols = st.columns([6, 1])
    with cols[1]:
        if st.button('REFRESH'): st.rerun()

    tickets = fetch_tickets()
    df = pd.DataFrame(tickets)

    unread = overdue = near_due = pd.DataFrame()

    if not df.empty:
        if 'has_unread_ticket_comments' in df.columns:
            unread = df[df['has_unread_ticket_comments'] == True]
        if 'due_date' in df.columns:
            df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce').dt.tz_localize(None)
            now = datetime.now()
            overdue = df[df['due_date'] <= now].dropna(subset=['due_date'])
            near_due = df[(df['due_date'] > now) & (df['due_date'] <= now + pd.Timedelta(hours=24))]

    # --- TOP ANALYTICS BAR ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TOTAL QUEUE", len(df))
    m2.metric("UNREAD REPLIES", len(unread))
    m3.metric("CRITICAL OVERDUE", len(overdue))
    m4.metric("DUE 24H", len(near_due))

    st.markdown("<br>", unsafe_allow_html=True)

    # --- TRIPLE GRID LAYOUT ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📩 REPLIES")
        st.markdown('<div class="grid-container">', unsafe_allow_html=True)
        if not unread.empty:
            for _, row in unread.iterrows():
                st.markdown(f"""<div class="panel-card unread-border">
                    <div class="card-id">TICKET #{row.get('number')}</div>
                    <div class="card-title">{row.get('customer_business_then_name', 'N/A')}</div>
                    <div class="card-meta">{row.get('subject', '')[:40]}...</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No unread replies.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("### 🚨 OVERDUE")
        st.markdown('<div class="grid-container">', unsafe_allow_html=True)
        if not overdue.empty:
            for _, row in overdue.iterrows():
                st.markdown(f"""<div class="panel-card overdue-border">
                    <div class="card-id">TICKET #{row.get('number')}</div>
                    <div class="card-title">🚨 OVERDUE</div>
                    <div class="card-meta">Expired: {row['due_date'].strftime('%d %b %H:%M')}</div>
                    <div class="card-meta">{row.get('customer_business_then_name', '')[:25]}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.success("No overdue tickets.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown("### ⏳ DUE SOON")
        st.markdown('<div class="grid-container">', unsafe_allow_html=True)
        if not near_due.empty:
            for _, row in near_due.iterrows():
                st.markdown(f"""<div class="panel-card neardue-border">
                    <div class="card-id">TICKET #{row.get('number')}</div>
                    <div class="card-title">WARNING</div>
                    <div class="card-meta">Due: {row['due_date'].strftime('%H:%M Today')}</div>
                    <div class="card-meta">{row.get('subject', '')[:35]}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No upcoming deadlines.")
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
