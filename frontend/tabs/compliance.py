import streamlit as st
import pandas as pd
import requests
import time
from frontend.api import API_BASE_URL


def render():
    # Wire RBAC check: only Arjun (Auditor) can see this screen
    if st.session_state.role != "Arjun (Auditor)":
        st.error(
            "Access Restrained. You must be logged in as Arjun (Auditor) to view the compliance matrix and generate evidence bundles."
        )
        st.info(
            "Hint: Switch your persona to 'Arjun (Auditor)' in the left sidebar to unlock this tab."
        )
    else:
        st.markdown(
            "<div class='clean-card'><h3>Regulatory Compliance Dashboard</h3><p style='font-size: 0.95em; color: #94A3B8;'>This matrix maps equipment operations and maintenance history against statutory Indian standards (OISD, PESO).</p></div>",
            unsafe_allow_html=True,
        )

        # Fetch Compliance Matrix Data from Backend API
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/compliance-gaps?role={st.session_state.role}"
            )
            if response.status_code == 200:
                gaps = response.json()
                if gaps:
                    formatted_data = []
                    for gap in gaps:
                        formatted_data.append(
                            {
                                "Equipment ID": gap.get("equipment_id", ""),
                                "Equipment Description": gap.get("equipment_type", ""),
                                "Standard": gap.get("regulation_id", ""),
                                "Last Audit Date": gap.get("last_inspection", ""),
                                "Assigned Status": "CRITICAL GAP",
                                "Details": gap.get("reason", ""),
                            }
                        )
                    compliance_matrix = pd.DataFrame(formatted_data)
                else:
                    compliance_matrix = pd.DataFrame(
                        [
                            {
                                "Assigned Status": "COMPLIANT",
                                "Details": "No compliance gaps found in the knowledge graph.",
                            }
                        ]
                    )
            else:
                st.error("Failed to fetch compliance data from backend API.")
                compliance_matrix = pd.DataFrame(
                    [{"Assigned Status": "UNKNOWN", "Details": "API Error"}]
                )
        except requests.exceptions.ConnectionError:
            st.error(
                f"Backend API is unreachable. Please ensure FastAPI is running at {API_BASE_URL}."
            )
            compliance_matrix = pd.DataFrame(
                [{"Assigned Status": "UNKNOWN", "Details": "Connection Error"}]
            )

        # Format styling for Streamlit
        def style_status(val):
            if val == "COMPLIANT":
                return "color: #059669; font-weight: 500;"
            elif val == "CRITICAL GAP":
                return "color: #dc2626; font-weight: 500;"
            return "color: #d97706; font-weight: 500;"

        styled_df = compliance_matrix.style.map(
            style_status, subset=["Assigned Status"]
        )
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Evidence generation section
        st.write("---")
        st.subheader("Generate Evidence Package")
        st.write(
            "Collect verified documentation (SOPs, checklists, inspection photos, logs) compiled into a package ready to export to regulatory auditors."
        )

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
                    mime="application/zip",
                )
        with col2:
            st.markdown("""
                **Package includes:**
                - `sop_pump_p101_rev4.pdf` (Active SOP reference)
                - `work_orders_june2024.csv` (Tightening records with flagged anomaly)
                - `oisd_118_excerpt.pdf` (Statutory regulation mapping)
                - `integrity_hash_sign.sha256` (Security validation hash)
            """)
