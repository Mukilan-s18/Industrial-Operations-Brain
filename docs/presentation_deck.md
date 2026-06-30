# Pitch Deck: Industrial Operations Brain

````carousel
# Slide 1: Title
## Industrial Operations Brain
### Intelligent Compliance & Operations Copilot
**Team**: [Your Team Name]
**Problem**: Heavy industries face critical safety risks and massive fines due to siloed data (SOPs vs. Maintenance logs) and manual compliance checks.

<!-- slide -->
# Slide 2: The Problem
## Why Did We Build This?
- **Data Fragmentation**: Mechanics look at work orders; Auditors look at OISD/PESO regulations. They never cross-reference in real-time.
- **Safety Risk**: A pump tightened to 50 Nm might seem fine to a mechanic, but violates OISD-118's 80 Nm requirement.
- **Consequences**: Catastrophic failures, unplanned downtime, and regulatory fines.

<!-- slide -->
# Slide 3: Our Solution
## The "Operations Brain"
An AI-powered copilot that understands the **relationships** between physical equipment, maintenance records, and complex statutory regulations.
- **Role-Based**: Tailored UI for Operators, Engineers, and Auditors.
- **Voice-Enabled**: Hands-free queries for workers in the field.
- **Graph-Powered**: Doesn't just search text; it traverses relationships.

<!-- slide -->
# Slide 4: Architecture
## Under the Hood
1. **Ingestion**: OCR parses unstructured PDFs (OISD guidelines, OEM Manuals).
2. **Processing**: spaCy NER extracts entities (Equipment, Regulations, Parameters).
3. **Storage**: NetworkX/Neo4j builds the Knowledge Graph; ChromaDB handles semantic embeddings.
4. **Intelligence**: LangGraph processes queries using GraphRAG logic.
5. **Frontend**: Streamlit provides a responsive, role-based dashboard.

<!-- slide -->
# Slide 5: Key Feature 1 - GraphRAG
## Beyond Standard RAG
Standard RAG fails at complex industrial logic. Our approach:
- **Semantic + Relational**: We combine ChromaDB semantic search with Graph traversal.
- **Compliance Gap Detection**: We automatically query the graph to find *Equipment* governed by *Regulations* that lack a recent *Inspection*.

<!-- slide -->
# Slide 6: Key Feature 2 - Enterprise Security
## Role-Based Access Control (RBAC)
- **Zero Trust**: Roles are enforced at the API backend, not just hidden on the frontend.
- **Operators**: See only specific operational manuals and equipment.
- **Auditors**: See the full graph, including sensitive compliance gaps and inspection failures.
- **Audit Logging**: Every query and access attempt is logged for corporate accountability.

<!-- slide -->
# Slide 7: Competitive Landscape
## Harvey Balls Benchmark Matrix

| Feature | Industrial Brain (Ours) | Standard ChatGPT | Manual Audits |
|---------|:---:|:---:|:---:|
| **Understands Private Data** | 🌕 | 🌑 | 🌕 |
| **Real-time Cross-Referencing** | 🌕 | 🌗 | 🌑 |
| **Data Privacy (On-Prem)** | 🌕 | 🌑 | 🌕 |
| **Graph-based Logic** | 🌕 | 🌑 | 🌑 |
| **Hands-free Field Access** | 🌕 | 🌗 | 🌑 |

*(Key: 🌕 Full | 🌗 Partial | 🌑 None)*

<!-- slide -->
# Slide 8: Future Roadmap
## What's Next?
1. **Live IIoT Integration**: Feed live SCADA/PLC sensor data directly into the Knowledge Graph to detect anomalies.
2. **AR/VR Headset Port**: Deploy the frontend to RealWear headsets for completely hands-free compliance checks on the rig.
3. **Predictive Maintenance**: Use the graph's failure patterns to train predictive maintenance models.
````
