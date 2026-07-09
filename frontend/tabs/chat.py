import streamlit as st
import streamlit.components.v1 as components
import os
import requests
import datetime
from frontend.api import API_BASE_URL


def render(use_fallback):
    st.markdown(
        "<div class='clean-card'><h4>Intelligent Operations Query</h4><p style='font-size:0.9em; color:#94A3B8;'>Ask the Brain about operating instructions, specs, or logs. Try checking casing bolt torques for P-101.</p></div>",
        unsafe_allow_html=True,
    )

    # Speech Recognition Simulation HTML/JS Injector
    st.markdown("##### Speech-to-Text Input")
    speech_html = """
    <div style="background-color: #0A0A0B; border: 1px solid #333; padding: 12px; border-radius: 6px; display: flex; align-items: center; gap: 15px; margin-bottom: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
        <button id="mic-btn" style="background: transparent; border: 1px solid #0ea5e9; border-radius: 4px; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
        </button>
        <span id="mic-status" style="font-size: 0.85em; color: #38BDF8; font-family: 'JetBrains Mono', monospace; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 8px;"><span style="display:inline-block; width:6px; height:6px; background-color:#38BDF8; border-radius:50%; box-shadow: 0 0 8px #38BDF8; animation: pulse 2s infinite;"></span> Click to speak...</span>
<style>@keyframes pulse { 0% { opacity: 0.5; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1.2); } 100% { opacity: 0.5; transform: scale(0.8); } }</style>
        <input type="text" id="transcription-box" placeholder="Transcript..." style="flex-grow: 1; padding: 8px 12px; border-radius: 4px; border: 1px solid #d1d5db; background: #f9fafb; color: #1f2937; font-family: 'Work Sans', sans-serif;" readonly>
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
                        st.info(
                            f"**Source:** {cite['source']} (Confidence: {cite['confidence']}%)\n\n{cite['text']}"
                        )
            if not msg["is_user"] and msg.get("metrics"):
                m = msg["metrics"]
                st.caption(
                    f"⏱️ Latency: {m.get('latency_sec', 0)}s | 🛡️ Faithfulness: {int(m.get('faithfulness_score', 0) * 100)}% | 📚 Corpus Coverage: {m.get('corpus_coverage_pct', 0)}%"
                )

    # Form handling input
    query = st.chat_input("Enter your operations query...")

    if query:
        # Add to history
        st.session_state.chat_history.append({"is_user": True, "text": query})

        # Check Offline Mode
        if st.session_state.offline_mode:
            st.session_state.offline_queue.append(
                {"role": st.session_state.role, "query": query}
            )
            st.session_state.chat_history.append(
                {
                    "is_user": False,
                    "text": "System offline. Your query has been cached locally in the offline queue and will sync when connection resumes.",
                }
            )
            st.rerun()

        # Determine Status
        status = "SUCCESS"
        citations = []
        html_payload = ""

        q_lower = query.lower()

        # Keep the RBAC block simulation for E-201
        if (
            "e-201" in q_lower or "exchanger" in q_lower
        ) and st.session_state.role == "Ravi (Operator)":
            status = "ACCESS DENIED"
            response_text = "**Access Denied**: Your current persona does not have clearance to view engineering inspection checklists."
            html_payload = """
                <div style="background-color: #fef2f2; border: 1px solid #ef4444; color: #991b1b; padding: 12px; border-radius: 4px; font-size: 14px;">
                    <b>RBAC Enforced:</b> Operators do not have read permission for static vessel inspection logs. Switch to Priya (Engineer) or Arjun (Auditor) to review static vessel status.
                </div>
            """
        else:
            # Call REAL LangGraph Backend
            try:
                # Update backend fallback state if toggled
                if use_fallback:
                    os.environ["USE_FALLBACK"] = "true"
                else:
                    os.environ["USE_FALLBACK"] = "false"

                res = requests.post(
                    f"{API_BASE_URL}/chat",
                    json={"query": query},
                    headers={
                        "X-User-Role": st.session_state.role.split("(")[-1]
                        .rstrip(")")
                        .strip()
                        .lower()
                    },
                )

                if res.status_code == 403:
                    response_text = f"**Access Denied**: {res.json().get('detail', 'You do not have permission to view this content.')}"
                    status = "ACCESS DENIED"
                elif res.status_code == 200:
                    data = res.json()
                    response_text = data.get("answer", "")

                    # Convert backend metrics and contradictions into our UI elements
                    if data.get("contradiction_detected"):
                        html_payload = f"""
                            <div class="contradiction-alert">
                                <b>CONTRADICTION DETECTED IN INGESTED CORPUS</b><br>
                                {data.get("contradiction_details", "")}
                            </div>
                        """

                    if data.get("action_taken") == "CREATE_SAP_WO":
                        action_res = data.get("action_result", "")
                        html_payload += f"""
                            <div style="background-color: #f0fdf4; border-left: 4px solid #16a34a; color: #166534; padding: 12px 16px; border-radius: 4px; margin: 12px 0; font-size: 14px;">
                                <b>🤖 AGENT ACTION EXECUTED: SAP CMMS Tool</b><br>
                                {action_res}
                            </div>
                        """

                    # Format citations
                    raw_sources = data.get("sources", [])
                    citations = []
                    for src in raw_sources:
                        citations.append(
                            {
                                "source": f"{src.get('doc', 'Unknown')} (Rev {src.get('revision', 'N/A')})",
                                "confidence": int(src.get("score", 0) * 100),
                                "text": "Extracted context match.",
                            }
                        )

                    # Also append metrics payload to display if needed
                    metrics = data.get("metrics", {})
                    st.session_state.latest_metrics = metrics

                else:
                    response_text = f"Backend Error {res.status_code}: {res.text}"
                    status = "ERROR"
            except requests.exceptions.ConnectionError:
                response_text = f"Backend API is unreachable. Please ensure FastAPI is running at {API_BASE_URL}."
                status = "ERROR"

        # Append response to history
        st.session_state.chat_history.append(
            {
                "is_user": False,
                "text": response_text,
                "html_payload": html_payload,
                "citations": citations,
                "metrics": st.session_state.get("latest_metrics", {}),
            }
        )

        # Log to audit trail
        st.session_state.audit_logs.append(
            {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "role": st.session_state.role,
                "query": query,
                "status": status,
            }
        )
        st.rerun()
