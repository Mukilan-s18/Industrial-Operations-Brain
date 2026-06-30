# Demo Script: Industrial Operations Brain

This guide details the scripted flow to demonstrate the frontend functionality and OISD compliance integration of the **Industrial Operations Brain** to judges.

---

## Scenario Setup
- **Objective:** Demonstrate how the Brain detects document contradictions, flags compliance breaches in maintenance logs, enforces RBAC, and simplifies regulatory reporting for plant managers.
- **Project Directory:** `C:\Users\mukesh kumar\.gemini\antigravity-ide\scratch\projects\Industrial-Operations-Brain`

---

## 🎭 Flow 1: Operator Torque Check (Version Contradiction Alert)
1. **Set Up:** Ensure active persona is set to **Ravi (Operator)** in the sidebar.
2. **Action:** Enter the query in the chat input:
   ```text
   What is the torque specification for pump P-101?
   ```
3. **Wow Moment:** 
   - Point out the red **CONTRADICTION DETECTED** banner.
   - The Brain cross-references past documents and warns the operator that `SOP-P-101-REV3` (50 Nm) conflicts with `SOP-P-101-REV4` (80 Nm).
   - The system automatically resolves this conflict by recommending the active Rev 4 standard (80 Nm).
   - Expand the **Citations & Sources** expander to show exactly which lines in the documents generated this result.

---

## 🛠️ Flow 2: Maintenance Audit (Compliance Breach Alert)
1. **Set Up:** Keep persona as **Ravi (Operator)**.
2. **Action:** Enter the query in the chat input:
   ```text
   What torque was P-101 tightened to in June?
   ```
3. **Wow Moment:**
   - Point out the yellow **REGULATORY COMPLIANCE BREACH (OISD-118-SEC-4.1)** alert.
   - The Brain scans the Excel/CSV maintenance logs, identifies `WO-901` where technician Suresh Kumar tightened the casing bolts to 50 Nm, and alerts that this is below the OISD safety standard lower threshold of 75 Nm.
   - It demonstrates how the system prevents safety accidents by comparing operational data with statutory regulations.

---

## 🔒 Flow 3: Role-Based Access Control (RBAC Enforced)
1. **Set Up:** Keep persona as **Ravi (Operator)**.
2. **Action:** Enter the query:
   ```text
   Show status of heat exchanger E-201
   ```
3. **Wow Moment:**
   - Note the **Access Denied** card. Ravi, as a field operator, is blocked from viewing static vessel engineering checklists.
4. **Action:** Switch the persona in the sidebar to **Priya (Engineer)**.
5. **Action:** Resubmit the same query:
   ```text
   Show status of heat exchanger E-201
   ```
6. **Wow Moment:**
   - The system now grants access, displaying the integrity check results (passed shell thickness, next hydrotesting due in June 2029) and citing `inspection_checklist_e201.txt`.

---

## 📊 Flow 4: Auditor Portal & One-Click Evidence Bundling
1. **Set Up:** Switch the persona in the sidebar to **Arjun (Auditor)**.
2. **Action:** Click on the **Audits & Compliance** tab in the main panel.
3. **Wow Moment:**
   - Show the matrix showing the compliance status of P-101, P-102, E-201, and V-201.
   - Point out that **P-101** is highlighted in red as a **CRITICAL GAP** because of the 50 Nm tightening job.
   - Click the **"Generate Evidence Package"** button.
   - After a brief loading spinner, show the **Download Evidence Package (ZIP)** button. Explain that this bundles all referenced SOPs, log lines, and regulations for regulatory auditors, reducing audit preparation time.

---

## 📴 Flow 5: Speech Input & Offline Resilience
1. **Action:** Demonstrate voice search by clicking the red microphone icon in the Speech Input Widget. Speak:
   ```text
   Check LPG vessel status
   ```
   *Note: If browser microphone permissions are blocked, copy the transcribed text using the "Copy to Chat" helper button.*
2. **Action:** Toggle **Offline Mode Simulator** to **ON** in the sidebar.
3. **Action:** Submit a query:
   ```text
   What are the safety distances?
   ```
4. **Wow Moment:**
   - Explain how field operators in remote steel/chemical yards with poor cellular reception can continue to query.
   - The chat displays: "System offline. Your query has been cached locally."
   - Toggle **Offline Mode** to **OFF**, click the **Sync Now** button in the sidebar, and show that the cached query seamlessly merges back into the **Admin Logs** audit trail.
