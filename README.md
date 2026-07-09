# Industrial Operations Brain 🧠⚙️

An intelligent, context-aware RAG and Knowledge Graph system designed for industrial and manufacturing environments. This system ingests complex industrial documents (SOPs, Work Orders, P&IDs, OEM Manuals, Regulations), builds a semantic knowledge graph, and provides role-based, accurate answers to operators, engineers, and auditors using an advanced LangGraph reasoning agent.

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Data Ingestion Layer
        A[OISD Regulations PDF] --> D[Document Parser & OCR]
        B[OEM Manuals PDF] --> D
        C[Work Orders CSV] --> D
    end

    subgraph Processing & Knowledge Graph Layer
        D -->|Extracted Text| E[spaCy NER Pipeline]
        E -->|Entities: Equipment, Dates, Standards| F[Knowledge Graph Builder]
        F -->|Edges: HAS_INSPECTION, GOVERNED_BY| G[(Neo4j / NetworkX InMemory)]
        D -->|Vector Embeddings| H[(ChromaDB)]
    end

    subgraph Intelligence Layer
        G -->|Graph Stats & Paths| I[FastAPI Backend]
        H -->|Semantic Search| J[LangGraph Agent]
        I -->|REST API| J
    end

    subgraph Presentation & Security Layer
        I -->|Live Compliance & API Routes| K[Next.js Dashboard]
        J -->|LLM Responses| K
        K -->|RBAC Filtering| K
    end

    subgraph Field User
        U((Operator / Auditor)) -->|Query / Voice| K
        K -->|Role-Specific Views| U
    end

    classDef db fill:#f9f,stroke:#333,stroke-width:2px,color:#000;
    classDef processing fill:#bbf,stroke:#333,stroke-width:2px,color:#000;
    classDef ui fill:#bfb,stroke:#333,stroke-width:2px,color:#000;

    class G,H db;
    class D,E,F,I,J processing;
    class K ui;
```

---

## ✨ Core Features

1. **Multi-Format Document Ingestion**: Seamlessly ingests text PDFs, scanned documents (Tesseract OCR), Excel files, CSVs, and mixed-language formats. Handles deduplication and version conflict detection.
2. **Dynamic Knowledge Graph**: Uses configuration-driven rules (`graph_config.yaml`, `compliance_rules.yaml`) and fuzzy alias resolution to map relationships between Equipment, Documents, Regulations, and Maintenance Dates.
3. **LangGraph Reasoning Agent**: An intelligent backend agent that coordinates between vector search (ChromaDB), graph queries, and LLM synthesis to ensure highly faithful and accurate responses while preventing hallucinations.
4. **Real-time Metrics & Fallback Strategy**: Tracks RAG faithfulness scores, corpus coverage, and API latency. Features an emergency fallback toggle for live demos.
5. **Full-stack Security & RBAC**: Implements Role-Based Access Control (RBAC) across both the Next.js frontend and the FastAPI backend (`X-User-Role` headers). 
6. **Interactive Visualization**: Explores the knowledge graph visually using an embedded PyVis dashboard via an iframe inside Next.js.
7. **Agentic Closed-Loop Actions**: The AI can execute automated actions (e.g. creating SAP Work Orders) based on equipment diagnosis.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js (v18+)
- Tesseract OCR (`brew install tesseract` or `apt-get install tesseract-ocr`)

### 1. Install Dependencies
```bash
# Backend dependencies
pip install -r requirements.txt
pip install -e .

# Frontend dependencies
cd frontend-next
npm install
cd ..
```

### 2. Generate Demo Corpus
Generate the synthetic dataset of 7 industrial documents (SOPs, Work Orders, OEM Manuals, Checklists):
```bash
python scripts/generate_demo_docs.py
```

### 3. Run the Unified Application
We use a single script to launch the FastAPI backend (port 8000), IoT Simulator, and the Next.js frontend (port 3000):
```bash
./run.sh
```
> The UI will be available at `http://localhost:3000`.
> The API will be available at `http://localhost:8000`. Swagger UI is at `http://localhost:8000/docs`.

---

## 📡 API Endpoints

### Ingestion API
- `POST /ingest/`: Upload documents to the pipeline (async chunking & OCR).
- `GET /ingest/status/{task_id}`: Check the progress of a large document.
- `GET /ingest/list`: View all successfully ingested files.
- `POST /ingest/reset`: Purge the vector DB and graph for a clean demo run.

### Agent API
- `POST /chat`: Submit a query to the LangGraph RAG pipeline (requires `X-User-Role` header).
- `POST /stream`: Stream the reasoning chain tokens directly to the frontend.
- `GET /metrics`: Fetch live metrics (corpus coverage, cache size).
- `POST /fallback/toggle`: Toggle the static emergency demo fallback mode.

---

## 🛡️ Role-Based Access Control (RBAC)

The system supports 3 default personas. Queries triggering restricted terms (e.g., `e-201`, `audit log`) are actively blocked at the backend for unauthorized roles.

| Role | Access Scope | Description |
|------|-------------|-------------|
| **Ravi (Operator)** | SOPs, Checklists | Field technician executing manual operations. Denied access to sensitive compliance or engineering logs. |
| **Priya (Engineer)** | SOPs, P&IDs, OEM Manuals | Process engineer troubleshooting equipment performance. |
| **Arjun (Auditor)** | All Documents, Standards | Compliance lead checking logs against national standards (OISD, PESO). |

---

## 📂 Project Structure

```text
├── backend/
│   ├── app.py                 # Main FastAPI server
│   ├── routers/               # API routes (chat, graph, compliance)
│   └── src/                   # Agent logic, retriever, graph builder
├── frontend-next/             # Next.js UI
│   ├── src/app                # Next.js Pages and routing
│   └── src/components         # React Components (ChatInterface, KnowledgeGraph, LiveMetrics)
├── ingestion/                 # Multi-format document processing engine
│   ├── main.py                # Ingestion API routes
│   └── processors/            # PDF, OCR, Excel, CSV processors
├── data/                      # Output generated graphs and vector DBs
├── demo_docs/                 # Sample industrial documents
└── scripts/                   # Utility scripts (e.g. data generation, tests)
```

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python
- **Frontend:** Next.js 14, Tailwind CSS, React
- **AI/LLM:** LangChain, LangGraph, Google Gemini
- **Vector DB:** ChromaDB
- **Knowledge Graph:** NetworkX, PyVis
- **Document Processing:** PyMuPDF, Tesseract OCR, Pandas
