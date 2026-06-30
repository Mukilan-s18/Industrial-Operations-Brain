import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import yaml
import os
import datetime
import time
import requests
import sqlite3
from src.app import builder, ner, get_graph_viz

# Set page configuration
st.set_page_config(
    page_title="Industrial Operations Brain",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Minimal Professional Styling (Light Theme)
st.markdown("""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #f8f9fa;
        color: #1f2937;
    }
    
    /* Bold Headings */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 800 !important;
    }
    
    /* Clean Cards */
    .clean-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* Minimal Title */
    .title-text {
        font-weight: 800;
        color: #111827;
        letter-spacing: -0.5px;
    }
    
    /* Alert Styles */
    .contradiction-alert {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        color: #991b1b;
        padding: 12px 16px;
        border-radius: 4px;
        margin: 12px 0;
        font-size: 14px;
    }
    .compliance-alert {
        background-color: #fffbeb;
        border-left: 4px solid #f59e0b;
        color: #92400e;
        padding: 12px 16px;
        border-radius: 4px;
        margin: 12px 0;
        font-size: 14px;
    }
    
    /* Persona Banner */
    .persona-banner {
        background-color: #f3f4f6;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 24px;
        font-size: 14px;
        color: #4b5563;
    }
    
    /* Buttons */
    div.stButton > button {
        background-color: transparent;
        color: #0284c7;
        border: 1px solid #0ea5e9;
        border-radius: 4px;
        padding: 6px 16px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: rgba(14, 165, 233, 0.05);
        color: #0369a1;
        border-color: #0284c7;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'role' not in st.session_state:
    st.session_state.role = "Ravi (Operator)"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = [
        {"timestamp": "2026-06-30 14:10:22", "role": "Arjun (Auditor)", "query": "List LPG separation units", "status": "SUCCESS"},
        {"timestamp": "2026-06-30 14:15:45", "role": "Priya (Engineer)", "query": "Fetch P-101 flow rates", "status": "SUCCESS"}
    ]
if 'offline_mode' not in st.session_state:
    st.session_state.offline_mode = False
if 'offline_queue' not in st.session_state:
    st.session_state.offline_queue = []

# Load compliance rules helper
def load_compliance_rules():
    yaml_path = os.path.join(os.path.dirname(__file__), "compliance_rules.yaml")
    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception:
            pass
    return {"rules": []}

compliance_data = load_compliance_rules()

# Personas definition
PERSONAS = {
    "Ravi (Operator)": {
        "allowed_docs": ["Standard Operating Procedures (SOPs)", "Inspection Checklists"],
        "desc": "Field technician executing maintenance, checklists, and manual operations in refinery units."
    },
    "Priya (Engineer)": {
        "allowed_docs": ["SOPs", "Inspection Checklists", "P&ID Diagrams Excerpts", "Equipment Manuals"],
        "desc": "Process and mechanical engineer troubleshooting equipment performance and planning maintenance."
    },
    "Arjun (Auditor)": {
        "allowed_docs": ["All Documents", "OISD Standards", "PESO Guidelines", "Regulatory Dashboards"],
        "desc": "Compliance lead checking operating logs against national OISD, PESO, and safety regulatory guidelines."
    }
}

# SIDEBAR Setup
with st.sidebar:
    st.markdown("<h2 class='title-text' style='margin-bottom: 5px; font-size: 20px;'>Operations Brain</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.85em; color: #6b7280; margin-top:0;'>Compliance & Ingestion Frontend</p>", unsafe_allow_html=True)
    st.write("---")
    
    # Persona Switcher
    st.subheader("Identity & Access (RBAC)")
    selected_persona = st.selectbox(
        "Active Persona Switcher",
        options=list(PERSONAS.keys()),
        index=list(PERSONAS.keys()).index(st.session_state.role)
    )
    st.session_state.role = selected_persona
    
    role_info = PERSONAS[selected_persona]
    st.markdown(f"**Description:** {role_info['desc']}")
    
    st.markdown("**Role Access Scope:**")
    for doc in role_info['allowed_docs']:
        st.markdown(f"- `{doc}`")
        
    st.write("---")
    
    # Offline Mode Simulator
    st.subheader("System State")
    offline = st.toggle("Offline Mode Simulator", value=st.session_state.offline_mode)
    st.session_state.offline_mode = offline
    
    if st.session_state.offline_mode:
        st.warning("Offline Mode Active. Queries will be cached locally.")
        if st.session_state.offline_queue:
            st.info(f"Pending Sync Queue: {len(st.session_state.offline_queue)} items")
            if st.button("Sync Now"):
                with st.spinner("Synchronizing cached queries to centralized database..."):
                    time.sleep(1.5)
                    for item in st.session_state.offline_queue:
                        st.session_state.audit_logs.append({
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "role": item["role"],
                            "query": item["query"],
                            "status": "SYNCED"
                        })
                    st.session_state.offline_queue = []
                    st.success("Sync complete.")
                    st.rerun()
    else:
        st.success("System: Connected to central server")

# MAIN Dashboard
st.markdown("<h1 class='title-text' style='margin-bottom: 10px; font-size: 28px;'>Industrial Operations Brain</h1>", unsafe_allow_html=True)

# Active Role Banner
st.markdown(f"""
    <div class="persona-banner">
        Logged in as <b>{st.session_state.role}</b>. System is enforcing Role-Based Access Control (RBAC).
    </div>
""", unsafe_allow_html=True)

# Main Navigation Tabs
tab_chat, tab_graph, tab_compliance, tab_audit = st.tabs([
    "Interactive Brain Query", 
    "Knowledge Graph & Schema Explorer", 
    "Audits & Compliance", 
    "Admin Logs"
])

# Tab 1: Interactive Brain Query
with tab_chat:
    st.markdown("<div class='clean-card'><h4>Intelligent Operations Query</h4><p style='font-size:0.9em; color:#6b7280;'>Ask the Brain about operating instructions, specs, or logs. Try checking casing bolt torques for P-101.</p></div>", unsafe_allow_html=True)
    
    # Speech Recognition Simulation HTML/JS Injector
    st.markdown("##### Speech-to-Text Input")
    speech_html = """
    <div style="background-color: #ffffff; border: 1px solid #e5e7eb; padding: 12px; border-radius: 6px; display: flex; align-items: center; gap: 15px; margin-bottom: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
        <button id="mic-btn" style="background: transparent; border: 1px solid #0ea5e9; border-radius: 4px; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
        </button>
        <span id="mic-status" style="font-size: 0.9em; color: #6b7280;">Click to speak...</span>
        <input type="text" id="transcription-box" placeholder="Transcript..." style="flex-grow: 1; padding: 8px 12px; border-radius: 4px; border: 1px solid #d1d5db; background: #f9fafb; color: #1f2937; font-family: 'Inter', sans-serif;" readonly>
        <button id="copy-btn" style="background: #f3f4f6; border: 1px solid #0ea5e9; border-radius: 4px; color: #0284c7; padding: 8px 12px; cursor: pointer; font-family: 'Inter', sans-serif;">Copy</button>
    </div>
    
    <script>
        const micBtn = document.getElementById('mic-btn');
        const micStatus = document.getElementById('mic-status');
        const transBox = document.getElementById('transcription-box');
        const copyBtn = document.getElementById('copy-btn');
        const micSvg = micBtn.querySelector('svg');
        
        let recognition;
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            
            recognition.onstart = () => {
                micBtn.style.background = 'rgba(14, 165, 233, 0.1)';
                micSvg.setAttribute('stroke', '#0ea5e9');
                micStatus.innerText = 'Listening...';
            };
            
            recognition.onend = () => {
                micBtn.style.background = 'transparent';
                micStatus.innerText = 'Click to speak...';
            };
            
            recognition.onresult = (event) => {
                const speechToText = event.results[0][0].transcript;
                transBox.value = speechToText;
            };
            
            recognition.onerror = (event) => {
                micStatus.innerText = 'Error: ' + event.error;
            };
        } else {
            micStatus.innerText = 'Speech API not supported.';
            micBtn.disabled = true;
        }
        
        micBtn.addEventListener('click', () => {
            if (recognition) {
                recognition.start();
            }
        });
        
        copyBtn.addEventListener('click', () => {
            if (transBox.value) {
                navigator.clipboard.writeText(transBox.value);
            }
        });
    </script>
    """
    components.html(speech_html, height=80)
    
    # Custom Chat Container
    for msg in st.session_state.chat_history:
        role_label = st.session_state.role if msg["is_user"] else "Brain"
        with st.chat_message("user" if msg["is_user"] else "assistant"):
            st.markdown(f"**{role_label}**")
            st.write(msg["text"])
            if not msg["is_user"] and msg.get("html_payload"):
                st.markdown(msg["html_payload"], unsafe_allow_html=True)
            if not msg["is_user"] and msg.get("citations"):
                with st.expander("Citations & Sources"):
                    for cite in msg["citations"]:
                        st.info(f"**Source:** {cite['source']} (Confidence: {cite['confidence']}%)\n\n{cite['text']}")

    # Form handling input
    query = st.chat_input("Enter your operations query...")
    
    if query:
        # Add to history
        st.session_state.chat_history.append({"is_user": True, "text": query})
        
        # Check Offline Mode
        if st.session_state.offline_mode:
            st.session_state.offline_queue.append({"role": st.session_state.role, "query": query})
            st.session_state.chat_history.append({
                "is_user": False,
                "text": "System offline. Your query has been cached locally in the offline queue and will sync when connection resumes."
            })
            st.rerun()
            
        # Determine Status
        status = "SUCCESS"
        citations = []
        html_payload = ""
        
        # Query Routing logic (Mock RAG + RBAC)
        q_lower = query.lower()
        
        # Scenario 1: Operator checking torque limits
        if "torque" in q_lower and "p-101" in q_lower and "spec" in q_lower:
            response_text = "Target casing bolt tightening torque specifications for centrifugal pump **P-101** are documented as follows:"
            
            # Contradiction injection!
            html_payload = """
                <div class="contradiction-alert">
                    <b>CONTRADICTION DETECTED IN INGESTED CORPUS</b><br>
                    - <b>SOP-P-101-REV3 (2022)</b>: Specifies tightening torque of <b>50 Nm</b>.<br>
                    - <b>SOP-P-101-REV4 (2024)</b>: Specifies revised tightening torque of <b>80 Nm</b>.<br>
                    <i>Resolving Conflict: SOP-P-101-REV4 is currently flagged active and OISD compliant. Target torque: 80 Nm.</i>
                </div>
            """
            citations = [
                {"source": "sop_pump_p101_rev4.txt", "confidence": 98, "text": "Target casing bolt tightening torque is: 80 Nm (+/- 5%). Ensure all bolts are torqued in three progressive stages (30 Nm, 60 Nm, then final 80 Nm)."},
                {"source": "sop_pump_p101_rev3.txt", "confidence": 92, "text": "Target casing bolt tightening torque is: 50 Nm (+/- 5%)."}
            ]
            
        # Scenario 2: Performed torque work order query (Audit / Breach detection)
        elif "work order" in q_lower or ("torque" in q_lower and "suresh" in q_lower) or ("torque" in q_lower and "p-101" in q_lower and "tightened" in q_lower):
            response_text = "Retrieving operational logs from `work_orders_june2024.csv` for pump **P-101** bolt tightening job:"
            
            # Compliance gap alert injection
            html_payload = """
                <div class="compliance-alert">
                    <b>REGULATORY COMPLIANCE BREACH (OISD-118-SEC-4.1)</b><br>
                    - <b>Work Order:</b> WO-901 (2024-06-05)<br>
                    - <b>Performed Torque:</b> 50 Nm by technician Suresh Kumar.<br>
                    - <b>Requirement:</b> SOP-P-101-REV4 requires 80 Nm (+/- 5%, tolerance 76 - 84 Nm).<br>
                    - <b>OISD Breach:</b> Casing torque of 50 Nm is below the 75 Nm safety threshold. Vapor leak risk flagged.
                </div>
            """
            citations = [
                {"source": "work_orders_june2024.csv", "confidence": 100, "text": "WO-901,P-101,2024-06-05,Seal Replacement & Bolt Tightening,50,Suresh Kumar,Closed,Re-assembled casing. Tightened casing bolts to 50 Nm as per SOP standard."},
                {"source": "oisd_118_excerpt.txt", "confidence": 95, "text": "Under-tightening casing bolts (below 75 Nm) is flagged as a high-criticality regulatory breach of OISD safety standard due to pressure gasket release risks."}
            ]
            
        # Scenario 3: Heat Exchanger E-201 check (RBAC block simulation)
        elif "e-201" in q_lower or "exchanger" in q_lower:
            if st.session_state.role == "Ravi (Operator)":
                status = "ACCESS DENIED"
                response_text = "**Access Denied**: Your current persona does not have clearance to view engineering inspection checklists."
                html_payload = """
                    <div style="background-color: #fef2f2; border: 1px solid #ef4444; color: #991b1b; padding: 12px; border-radius: 4px; font-size: 14px;">
                        <b>RBAC Enforced:</b> Operators do not have read permission for static vessel inspection logs. Switch to Priya (Engineer) or Arjun (Auditor) to review static vessel status.
                    </div>
                """
            else:
                response_text = "Standard Operating Status for Heat Exchanger **E-201** retrieved from inspection records:"
                citations = [
                    {"source": "inspection_checklist_e201.txt", "confidence": 99, "text": "The static vessel E-201 is certified for continued operations... Shell thickness pass. Next hydrotesting and internal inspection scheduled for June 2029 (5-year cycle per PESO guidelines)."}
                ]
                html_payload = """
                    <div style="margin-top: 10px; padding: 12px; background-color: #ecfdf5; border-left: 4px solid #10b981; color: #065f46; border-radius: 4px; font-size: 14px;">
                        <b>Status: Compliant</b>. Integrity check completed on 18-June-2024. Next due: June 2029.
                    </div>
                """
        
        # General response fallback
        else:
            response_text = f"This is a live mock response from the **Industrial Operations Brain**.\n\nAs a **{st.session_state.role}**, you queried: `\"{query}\"`.\n\nIn the final integrated backend, this query is routed through a LangGraph agent that reads from files you are authorized to access, searches vector spaces/graphs, performs verification checks, and outputs compliance analysis."
            citations = []
            
        # Append response to history
        st.session_state.chat_history.append({
            "is_user": False,
            "text": response_text,
            "html_payload": html_payload,
            "citations": citations
        })
        
        # Log to audit trail
        st.session_state.audit_logs.append({
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "role": st.session_state.role,
            "query": query,
            "status": status
        })
        st.rerun()

# Tab: Knowledge Graph & Schema Explorer
with tab_graph:
    st.markdown("<div class='clean-card'><h3>Knowledge Graph Explorer</h3><p style='font-size: 0.95em; color: #4b5563;'>Explore plant asset relationships, compliance constraints, and failure modes interactively.</p></div>", unsafe_allow_html=True)
    
    # Graph stats cards
    stats = builder.get_graph_stats()
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Total Entities (Nodes)", stats["node_count"])
    with col_stat2:
        st.metric("Total Relationships (Edges)", stats["edge_count"])
    with col_stat3:
        st.metric("Equipment Compliance Coverage", f"{stats['equipment_coverage_pct']}%")
        
    st.write("---")
    
    # Ego network visualization control
    col_viz_ctrl1, col_viz_ctrl2 = st.columns([1, 2])
    with col_viz_ctrl1:
        st.subheader("Graph Visualization Controls")
        st.write("Select a node to view its local 1-hop ego network, or select 'All Nodes' for the global overview.")
        
        # Sort nodes alphabetically
        node_options = ["All Nodes"] + sorted(list(builder.G.nodes))
        selected_node = st.selectbox("Focus Asset Node", options=node_options)
        
        # Node Type Breakdown
        st.write(" ")
        st.write("**Entity Type Breakdown:**")
        for lbl, count in stats["nodes_by_type"].items():
            st.markdown(f"- **{lbl}**: {count}")
            
    with col_viz_ctrl2:
        # Load and render PyVis graph
        viz_node_id = None if selected_node == "All Nodes" else selected_node
        with st.spinner("Generating interactive visualization..."):
            html_content = get_graph_viz(viz_node_id, st.session_state.role)
        
        # Render the PyVis interactive graph
        components.html(html_content, height=520, scrolling=False)
        
    st.write("---")
    
    # NER Accuracy Metrics Report (Day 9)
    st.subheader("Model Accuracy & Quality Control (NER)")
    st.write("The F1 score is evaluated against 10 annotated heavy-industry sentences covering equipment, regulations, failure modes, parameters, and dates.")
    
    with st.spinner("Evaluating NER accuracy metrics..."):
        eval_report = ner.evaluate_accuracy()
        
    col_acc1, col_acc2, col_acc3 = st.columns(3)
    with col_acc1:
        st.metric("NER F1 Score", f"{eval_report['f1_score'] * 100:.2f}%")
    with col_acc2:
        st.metric("Precision", f"{eval_report['precision'] * 100:.2f}%")
    with col_acc3:
        st.metric("Recall", f"{eval_report['recall'] * 100:.2f}%")
        
    with st.expander("Show Labeled Evaluation Corpus & Predictions"):
        # Format the predictions comparison
        eval_details = []
        for det in eval_report["details"]:
            gt_str = ", ".join([f"{e['text']} ({e['label']})" for e in det["ground_truth"]]) or "None"
            ext_str = ", ".join([f"{e['text']} ({e['label']})" for e in det["extracted"]]) or "None"
            eval_details.append({
                "Sentence": det["sentence"],
                "Ground Truth Entities": gt_str,
                "Extracted Entities": ext_str
            })
        st.dataframe(pd.DataFrame(eval_details), use_container_width=True)
        
    st.write("---")
    
    # Schema & Architecture Documentation (Day 10)
    st.subheader("Technical Architecture & Schema Spec")
    
    tab_doc1, tab_doc2 = st.tabs(["1-Page Architecture Summary", "Mermaid.js ER Diagram"])
    with tab_doc1:
        arch_path = os.path.join(os.path.dirname(__file__), "docs", "technical_architecture.md")
        if os.path.exists(arch_path):
            with open(arch_path, "r") as f:
                arch_text = f.read()
            st.markdown(arch_text)
        else:
            st.warning("Architecture summary document not found.")
            
    with tab_doc2:
        st.write("This diagram specifies the entity-relationship ontology of our heavy-industry graph schema.")
        # Mermaid code
        er_code = """erDiagram
    DOCUMENT ||--o{ PERSON : AUTHORED_BY
    DOCUMENT ||--o{ EQUIPMENT : MENTIONS
    DOCUMENT ||--o{ REGULATION : MENTIONS
    EQUIPMENT ||--o{ FAILURE_MODE : HAS_FAILURE
    EQUIPMENT ||--o{ REGULATION : GOVERNED_BY
    EQUIPMENT ||--o{ PARAMETER : HAS_PARAMETER
    EQUIPMENT ||--o{ DATE : HAS_INSPECTION"""
        
        # Render Mermaid using browser-based compiler in iframe
        components.html(
            f"""
            <div style="background-color: #0F172A; padding: 20px; border-radius: 8px; display: flex; justify-content: center; align-items: center; border: 1px solid #334155;">
                <pre class="mermaid" style="margin: 0; color: #F8FAFC;">
                {er_code}
                </pre>
            </div>
            <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true, theme: 'dark', securityLevel: 'loose' }});
            </script>
            """,
            height=300,
            scrolling=True
        )

# Tab 3: Audits & Compliance
with tab_compliance:
    # Wire RBAC check: only Arjun (Auditor) can see this screen
    if st.session_state.role != "Arjun (Auditor)":
        st.error("Access Restrained. You must be logged in as Arjun (Auditor) to view the compliance matrix and generate evidence bundles.")
        st.info("Hint: Switch your persona to 'Arjun (Auditor)' in the left sidebar to unlock this tab.")
    else:
        st.markdown("<div class='clean-card'><h3>Regulatory Compliance Dashboard</h3><p style='font-size: 0.95em; color: #4b5563;'>This matrix maps equipment operations and maintenance history against statutory Indian standards (OISD, PESO).</p></div>", unsafe_allow_html=True)
        
        # Fetch Compliance Matrix Data from Backend API
        try:
            response = requests.get(f"http://127.0.0.1:8000/api/compliance-gaps?role={st.session_state.role}")
            if response.status_code == 200:
                gaps = response.json()
                if gaps:
                    formatted_data = []
                    for gap in gaps:
                        formatted_data.append({
                            "Equipment ID": gap.get("equipment_id", ""),
                            "Equipment Description": gap.get("equipment_type", ""),
                            "Standard": gap.get("regulation_id", ""),
                            "Last Audit Date": gap.get("last_inspection", ""),
                            "Assigned Status": "CRITICAL GAP",
                            "Details": gap.get("reason", "")
                        })
                    compliance_matrix = pd.DataFrame(formatted_data)
                else:
                    compliance_matrix = pd.DataFrame([{"Assigned Status": "COMPLIANT", "Details": "No compliance gaps found in the knowledge graph."}])
            else:
                st.error("Failed to fetch compliance data from backend API.")
                compliance_matrix = pd.DataFrame([{"Assigned Status": "UNKNOWN", "Details": "API Error"}])
        except requests.exceptions.ConnectionError:
            st.error("Backend API is unreachable. Please ensure FastAPI is running on port 8000.")
            compliance_matrix = pd.DataFrame([{"Assigned Status": "UNKNOWN", "Details": "Connection Error"}])
        
        # Format styling for Streamlit
        def style_status(val):
            if val == "COMPLIANT":
                return "color: #059669; font-weight: 500;"
            elif val == "CRITICAL GAP":
                return "color: #dc2626; font-weight: 500;"
            return "color: #d97706; font-weight: 500;"
            
        styled_df = compliance_matrix.style.map(style_status, subset=['Assigned Status'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Evidence generation section
        st.write("---")
        st.subheader("Generate Evidence Package")
        st.write("Collect verified documentation (SOPs, checklists, inspection photos, logs) compiled into a package ready to export to regulatory auditors.")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Generate Evidence Package"):
                with st.spinner("Bundling PDFs, CSV logs, and schemas..."):
                    time.sleep(2.0)
                st.success("Evidence package generated successfully.")
                
                # Mock download button
                zip_data = b"MOCK_ZIP_DATA"
                st.download_button(
                    label="Download Evidence Package (ZIP)",
                    data=zip_data,
                    file_name="oisd_evidence_package_p101.zip",
                    mime="application/zip"
                )
        with col2:
            st.markdown("""
                **Package includes:**
                - `sop_pump_p101_rev4.pdf` (Active SOP reference)
                - `work_orders_june2024.csv` (Tightening records with flagged anomaly)
                - `oisd_118_excerpt.pdf` (Statutory regulation mapping)
                - `integrity_hash_sign.sha256` (Security validation hash)
            """)

# Tab 4: Admin Logs
with tab_audit:
    st.markdown("<div class='clean-card'><h3>Security & Query Audit Logs</h3><p style='font-size:0.9em; color:#4b5563;'>Full traceability of all user prompts, session logins, and security status. Satisfies corporate auditing requirements.</p></div>", unsafe_allow_html=True)
    
    # Audit log search/filter
    st.text("System Audit Stream:")
    
    log_rows = ""
    for log in reversed(st.session_state.audit_logs):
        status_color = "#059669" if log["status"] in ["SUCCESS", "SYNCED"] else "#dc2626"
        log_rows += f"""
        <div style="border-bottom: 1px solid #e5e7eb; padding: 10px 0; display:flex; justify-content:space-between; font-family:'JetBrains Mono', monospace; font-size:13px;">
            <span style="color:#0ea5e9;">[{log['timestamp']}]</span>
            <span style="color:#111827; width: 160px; margin-left: 10px;">{log['role']}</span>
            <span style="color:#4b5563; flex-grow:1; margin-left: 15px;">Query: "{log['query']}"</span>
            <span style="color:{status_color}; font-weight:500;">{log['status']}</span>
        </div>
        """
    
    st.markdown(f"""
        <div style="background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 6px; padding: 16px; max-height: 400px; overflow-y: auto;">
            {log_rows}
        </div>
    """, unsafe_allow_html=True)
    
    # Thumbs up/down feedback logging
    st.write("---")
    st.subheader("User Feedback Logging")
    st.write("Capture user feedback to retrain vector embeddings and refine graph relations.")
    
    # Initialize SQLite database for feedback
    conn = sqlite3.connect("feedback.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS feedback
                 (Timestamp TEXT, Persona TEXT, Query TEXT, Feedback INTEGER)''')
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
        fb_query = st.text_input("Simulate feed-in query for rating", placeholder="e.g., Target torque for P-101")
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
                    insert_c.execute("INSERT INTO feedback VALUES (?, ?, ?, ?)", 
                                     (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                      st.session_state.role, 
                                      fb_query, 
                                      1 if "+1" in rating else -1))
                    insert_conn.commit()
                    
                st.toast("Feedback registered.")
                time.sleep(1.0)
                st.rerun()
            else:
                st.error("Please enter a query to rate.")
                
    conn.close()
