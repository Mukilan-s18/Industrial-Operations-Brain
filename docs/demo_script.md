# Demo Video Script (2-Minutes)

**Format:** Screencast with voiceover. Keep the pace brisk.

---

### [0:00 - 0:15] The Operator Experience (Role: Ravi)
**[Action]**: Start on the login screen. Select "Ravi (Operator)". 
**[Voiceover]**: "Welcome to the Industrial Operations Brain. I'm logged in as Ravi, a field operator. I'm about to perform maintenance on pump P-101, but my hands are dirty, so I use the voice assistant."
**[Action]**: Click the microphone icon. Type (or speak): *“Target torque for P-101”*. 

### [0:15 - 0:40] GraphRAG in Action
**[Action]**: Show the assistant responding with the OISD standard torque limit. Click to expand the "Source Evidence" accordion to show the PDF snippet.
**[Voiceover]**: "The system instantly queries our GraphRAG backend, cross-referencing OEM manuals with strict OISD compliance standards. It doesn't just guess; it provides the exact source document as verifiable evidence."

### [0:40 - 1:00] The Auditor Experience (Role: Arjun)
**[Action]**: Switch role in the sidebar to "Arjun (Auditor)". Navigate to the **Audits & Compliance** tab.
**[Voiceover]**: "Now let's switch to the Auditor persona. Because of our strict backend Role-Based Access Control, Arjun sees a completely different dashboard. Here, the system has automatically traversed the knowledge graph to detect compliance gaps."
**[Action]**: Highlight the "CRITICAL GAP" row for P-101.
**[Voiceover]**: "It flagged that an operator previously tightened P-101 to 50 Nm, which violates the 80 Nm safety standard."

### [1:00 - 1:20] Evidence Packaging
**[Action]**: Click the "Generate Evidence Package" button. Show the success toast and download button.
**[Voiceover]**: "With one click, Arjun generates an encrypted evidence package for regulatory bodies, automatically compiling the flagged work orders and the OISD standard PDFs."

### [1:20 - 1:45] Knowledge Graph Visualization
**[Action]**: Navigate to the **Knowledge Graph** tab. Zoom in on the PyVis interactive graph.
**[Voiceover]**: "How does it know all this? This live Knowledge Graph. It maps relationships between physical equipment, historical failures, and regulatory rules in real-time, completely extracted from unstructured text."

### [1:45 - 2:00] Closing
**[Action]**: Navigate to **Admin Logs** tab to show the audit stream.
**[Voiceover]**: "Everything is logged securely in an immutable audit trail. The Industrial Operations Brain breaks down data silos to prevent catastrophic failures before they happen. Thank you."
