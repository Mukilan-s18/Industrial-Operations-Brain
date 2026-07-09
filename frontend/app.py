import streamlit as st
import yaml
import os
import datetime
import time
import requests
from frontend.api import API_BASE_URL

# Import tab modules
from frontend.tabs import chat, graph, compliance, audit

# Set page configuration
st.set_page_config(
    page_title="Industrial Operations Brain",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Minimal Professional Styling (Light Theme)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700;800&family=Fira+Code:wght@300;400;500;600;700&display=swap');
    
    html { scroll-behavior: smooth; }
    
    html, body, [class*="css"], .stApp {
        font-family: 'JetBrains Mono', monospace !important;
        background-color: #050505 !important;
        color: #E2E8F0;
        -webkit-font-smoothing: antialiased;
    }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #050505; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #555; }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        letter-spacing: -0.04em;
        text-transform: uppercase;
    }
    h1 { font-size: 2.2rem !important; line-height: 1.1 !important; margin-bottom: 1rem !important; }
    h2 { font-size: 1.7rem !important; line-height: 1.2 !important; margin-bottom: 0.8rem !important; }
    h3 { font-size: 1.3rem !important; line-height: 1.3 !important; }
    h4 { font-size: 1.1rem !important; }
    p, span, div, label { font-size: 0.95rem; line-height: 1.6; }
    
    .clean-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 4px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        animation: fadeIn 0.6s ease-out forwards;
    }
    .clean-card:hover {
        border-color: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .title-text {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 800;
        color: #000;
        letter-spacing: -0.05em;
        text-transform: uppercase;
        border-bottom: 2px solid #FFFFFF;
        display: inline-block;
        padding-bottom: 4px;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0A0A0B !important;
        border-right: 1px solid #222 !important;
        padding-top: 2rem;
    }
    
    .stSelectbox > div[data-baseweb="select"] > div {
        background-color: #1A1A1C;
        border: 1px solid #333;
        border-radius: 2px;
        color: #E2E8F0;
        font-family: 'JetBrains Mono', monospace !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .stSelectbox > div[data-baseweb="select"] > div:hover { border-color: #666; }
    
    .streamlit-expanderHeader {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
        background-color: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 2px !important;
        padding: 12px 16px !important;
        transition: all 0.3s ease;
    }
    .streamlit-expanderHeader:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
    }
    .streamlit-expanderContent {
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-top: none !important;
        padding: 20px !important;
        animation: slideDown 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        background-color: #0A0A0B !important;
    }
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-5px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .contradiction-alert {
        background-color: rgba(255, 50, 50, 0.05);
        border: 1px solid rgba(255, 50, 50, 0.2);
        border-left: 4px solid #FF3333;
        color: #FFB3B3;
        padding: 16px;
        border-radius: 2px;
        margin: 16px 0;
        font-size: 13px;
        font-family: 'JetBrains Mono', monospace;
    }
    .compliance-alert {
        background-color: rgba(255, 170, 0, 0.05);
        border: 1px solid rgba(255, 170, 0, 0.2);
        border-left: 4px solid #FFAA00;
        color: #FFE6B3;
        padding: 16px;
        border-radius: 2px;
        margin: 16px 0;
        font-size: 13px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .persona-banner {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-left: 4px solid #FFFFFF;
        border-radius: 2px;
        padding: 16px 20px;
        margin-bottom: 32px;
        font-size: 13px;
        color: #E2E8F0;
        display: flex;
        align-items: center;
        gap: 12px;
        animation: fadeIn 0.8s ease-out forwards;
    }
    
    div.stButton > button {
        background-color: #FFFFFF;
        color: #000000;
        border: 1px solid #FFFFFF;
        border-radius: 2px;
        padding: 8px 24px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: transparent;
        color: #000;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid #222;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 1rem;
        padding-bottom: 1rem;
        font-weight: 500;
        color: #666;
        border-bottom-color: transparent !important;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 12px;
        transition: color 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #AAA; }
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom: 2px solid #FFFFFF !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize Session State
if "role" not in st.session_state:
    st.session_state.role = "Ravi (Operator)"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "audit_logs" not in st.session_state:
    st.session_state.audit_logs = [
        {
            "timestamp": "2026-06-30 14:10:22",
            "role": "Arjun (Auditor)",
            "query": "List LPG separation units",
            "status": "SUCCESS",
        },
        {
            "timestamp": "2026-06-30 14:15:45",
            "role": "Priya (Engineer)",
            "query": "Fetch P-101 flow rates",
            "status": "SUCCESS",
        },
    ]
if "offline_mode" not in st.session_state:
    st.session_state.offline_mode = False
if "offline_queue" not in st.session_state:
    st.session_state.offline_queue = []


# Load compliance rules helper
def load_compliance_rules():
    yaml_path = os.path.join(
        os.path.dirname(__file__), "..", "backend", "config", "compliance_rules.yaml"
    )
    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, "r") as file:
                return yaml.safe_load(file)
        except Exception:
            pass
    return {"rules": []}


compliance_data = load_compliance_rules()

# Personas definition
PERSONAS = {
    "Ravi (Operator)": {
        "allowed_docs": [
            "Standard Operating Procedures (SOPs)",
            "Inspection Checklists",
        ],
        "desc": "Field technician executing maintenance, checklists, and manual operations in refinery units.",
    },
    "Priya (Engineer)": {
        "allowed_docs": [
            "SOPs",
            "Inspection Checklists",
            "P&ID Diagrams Excerpts",
            "Equipment Manuals",
        ],
        "desc": "Process and mechanical engineer troubleshooting equipment performance and planning maintenance.",
    },
    "Arjun (Auditor)": {
        "allowed_docs": [
            "All Documents",
            "OISD Standards",
            "PESO Guidelines",
            "Regulatory Dashboards",
        ],
        "desc": "Compliance lead checking operating logs against national OISD, PESO, and safety regulatory guidelines.",
    },
}

# SIDEBAR Setup
with st.sidebar:
    st.markdown(
        "<h2 class='title-text' style='margin-bottom: 5px; font-size: 20px;'>Operations Brain</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='font-size: 0.85em; color: #94A3B8; margin-top:0;'>Compliance & Ingestion Frontend</p>",
        unsafe_allow_html=True,
    )
    st.write("---")

    # Persona Switcher
    st.subheader("Identity & Access (RBAC)")
    selected_persona = st.selectbox(
        "Active Persona Switcher",
        options=list(PERSONAS.keys()),
        index=list(PERSONAS.keys()).index(st.session_state.role),
    )
    st.session_state.role = selected_persona

    role_info = PERSONAS[selected_persona]
    st.markdown(f"**Description:** {role_info['desc']}")

    st.markdown("**Role Access Scope:**")
    for doc in role_info["allowed_docs"]:
        st.markdown(f"- `{doc}`")

    st.write("---")

    # Offline Mode Simulator
    st.subheader("System State")
    offline = st.toggle("Offline Mode Simulator", value=st.session_state.offline_mode)

    st.subheader("Demo Hardening")
    use_fallback = st.toggle("Enable Fallback Mode (API Crash Recovery)", value=False)

    # Notify backend of fallback state change
    try:
        requests.post(
            f"{API_BASE_URL}/fallback/toggle?enabled={str(use_fallback).lower()}"
        )
    except requests.exceptions.RequestException:
        pass

    st.session_state.offline_mode = offline

    st.write("---")
    st.subheader("Live SCADA / IoT Feed")
    iot_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "iot_data.json")
    )
    if os.path.exists(iot_path):
        try:
            import json

            with open(iot_path, "r") as f:
                iot_data = json.load(f)
            timestamp = iot_data.get("timestamp", "Unknown")
            st.caption(f"Last updated: {timestamp}")
            for eq, metrics in iot_data.get("equipment", {}).items():
                status_color = (
                    "🟢"
                    if metrics["status"] == "NORMAL"
                    else "🟡"
                    if metrics["status"] == "WARNING"
                    else "🔴"
                )
                st.markdown(f"**{eq}** {status_color}")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Vibration", f"{metrics['vibration_mms']:.2f} mm/s")
                with col2:
                    st.metric("Temp", f"{metrics['temp_c']:.1f} °C")
        except Exception:
            st.error("Error reading IoT data.")
    else:
        st.info("IoT Simulator offline.")
    if st.session_state.offline_mode:
        st.warning("Offline Mode Active. Queries will be cached locally.")
        if st.session_state.offline_queue:
            st.info(f"Pending Sync Queue: {len(st.session_state.offline_queue)} items")
            if st.button("Sync Now"):
                with st.spinner(
                    "Synchronizing cached queries to centralized database..."
                ):
                    time.sleep(1.5)
                    for item in st.session_state.offline_queue:
                        st.session_state.audit_logs.append(
                            {
                                "timestamp": datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "role": item["role"],
                                "query": item["query"],
                                "status": "SYNCED",
                            }
                        )
                    st.session_state.offline_queue = []
                    st.success("Sync complete.")
                    st.rerun()
    else:
        st.success("System: Connected to central server")

# MAIN Dashboard
st.markdown(
    "<h1 class='title-text' style='margin-bottom: 10px; font-size: 28px;'>Industrial Operations Brain</h1>",
    unsafe_allow_html=True,
)

# Active Role Banner
st.markdown(
    f"""
    <div class="persona-banner">
        Logged in as <b>{st.session_state.role}</b>. System is enforcing Role-Based Access Control (RBAC).
    </div>
""",
    unsafe_allow_html=True,
)

# Main Navigation Tabs
tab_chat, tab_graph, tab_compliance, tab_audit = st.tabs(
    [
        "Interactive Brain Query",
        "Knowledge Graph & Schema Explorer",
        "Audits & Compliance",
        "Admin Logs",
    ]
)

with tab_chat:
    chat.render(use_fallback)

with tab_graph:
    graph.render()

with tab_compliance:
    compliance.render()

with tab_audit:
    audit.render()
