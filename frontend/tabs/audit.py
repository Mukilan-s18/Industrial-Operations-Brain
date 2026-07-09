import streamlit as st
import pandas as pd
import sqlite3
import datetime
import time


def render():
    st.markdown(
        "<div class='clean-card'><h3>Security & Query Audit Logs</h3><p style='font-size:0.9em; color:#94A3B8;'>Full traceability of all user prompts, session logins, and security status. Satisfies corporate auditing requirements.</p></div>",
        unsafe_allow_html=True,
    )

    # Audit log search/filter
    st.text("System Audit Stream:")

    log_rows = ""
    for log in reversed(st.session_state.audit_logs):
        status_color = (
            "#059669" if log["status"] in ["SUCCESS", "SYNCED"] else "#dc2626"
        )
        log_rows += f"""
        <div style="border-bottom: 1px solid #e5e7eb; padding: 10px 0; display:flex; justify-content:space-between; font-family:'Work Sans', sans-serif; font-size:13px;">
            <span style="color:#0ea5e9;">[{log["timestamp"]}]</span>
            <span style="color:#111827; width: 160px; margin-left: 10px;">{log["role"]}</span>
            <span style="color:#94A3B8; flex-grow:1; margin-left: 15px;">Query: "{log["query"]}"</span>
            <span style="color:{status_color}; font-weight:500;">{log["status"]}</span>
        </div>
        """

    st.markdown(
        f"""
        <div style="background-color: #0A0A0B; border: 1px solid #333; border-radius: 6px; padding: 16px; max-height: 400px; overflow-y: auto;">
            {log_rows}
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Thumbs up/down feedback logging
    st.write("---")
    st.subheader("User Feedback Logging")
    st.write(
        "Capture user feedback to retrain vector embeddings and refine graph relations."
    )

    # Initialize SQLite database for feedback
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS feedback
                 (Timestamp TEXT, Persona TEXT, Query TEXT, Feedback INTEGER)""")
    conn.commit()

    try:
        fb_df = pd.read_sql_query("SELECT * FROM feedback", conn)
        if not fb_df.empty:
            st.dataframe(fb_df, use_container_width=True)
        else:
            st.info("No feedback registered yet.")
    except Exception:
        st.info("No feedback registered yet.")

    # Feedback simulation
    col_fb1, col_fb2, col_fb3 = st.columns([2, 1, 1])
    with col_fb1:
        fb_query = st.text_input(
            "Simulate feed-in query for rating",
            placeholder="e.g., Target torque for P-101",
        )
    with col_fb2:
        rating = st.selectbox("Feedback Score", ["+1 (Helpful)", "-1 (Unhelpful)"])
    with col_fb3:
        st.write(" ")
        st.write(" ")
        if st.button("Log Feedback"):
            if fb_query:
                # Thread-safe SQLite insert
                with sqlite3.connect("feedback.db", timeout=10) as insert_conn:
                    insert_c = insert_conn.cursor()
                    insert_c.execute(
                        "INSERT INTO feedback VALUES (?, ?, ?, ?)",
                        (
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            st.session_state.role,
                            fb_query,
                            1 if "+1" in rating else -1,
                        ),
                    )
                    insert_conn.commit()

                st.toast("Feedback registered.")
                time.sleep(1.0)
                st.rerun()
            else:
                st.error("Please enter a query to rate.")

    conn.close()
