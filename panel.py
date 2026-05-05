def main():
    st.markdown('<div class="main-header">ILLEGEAR LIVE TICKET MONITOR</div>', unsafe_allow_html=True)
    
    tickets = fetch_tickets()
    
    # Check if we actually got a list back
    if not tickets:
        st.info("🛰️ Scanning for active signals... No tickets found.")
        return

    df = pd.DataFrame(tickets)
    
    # --- ROBUST COLUMN INITIALIZATION ---
    # We ensure these columns exist in our logic, even if the API didn't send them
    if 'has_unread_ticket_comments' not in df.columns:
        df['has_unread_ticket_comments'] = False
    
    if 'due_date' not in df.columns:
        df['due_date'] = None

    # Process Times safely
    now = datetime.now()
    df['due_date_dt'] = pd.to_datetime(df['due_date'], errors='coerce').dt.tz_localize(None)

    # --- SAFE METRIC CALCULATION ---
    # Now that we've guaranteed the columns exist above, these filters won't crash
    unread_df = df[df['has_unread_ticket_comments'] == True]
    unread_count = len(unread_df)
    
    overdue_df = df[df['due_date_dt'] <= now].dropna(subset=['due_date_dt'])
    overdue_count = len(overdue_df)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("ACTIVE SYSTEMS", len(df))
    m2.metric("UNREAD REPLIES", unread_count)
    m3.metric("CRITICAL OVERDUE", overdue_count)

    # Building the Grid
    grid_html = '<div class="ticket-grid">'
    
    for _, row in df.iterrows():
        # Determine Status logic
        status_class = "status-normal"
        status_text = "STABLE"
        time_display = ""
        
        is_unread = row['has_unread_ticket_comments']
        
        # Check if due_date_dt is a valid timestamp before comparing
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
            <div class="ticket-no">REF: #{row.get('number', '???')}</div>
            <div class="cust-name">{row.get('customer_business_then_name', 'UNKNOWN')}</div>
            <div class="ticket-subject">{str(row.get('subject', 'No Subject'))[:60]}</div>
            <div class="ticket-time" style="color: {'#ff3e3e' if is_overdue else '#00d4ff' if is_unread else '#ffaa00' if is_near else '#888'}">
                {status_text} <br> {time_display}
            </div>
        </div>
        """
    
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    if st.button('REFRESH SCAN'):
        st.rerun()
