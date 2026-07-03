# System Architecture

This architecture outlines the complete pipeline for the **Industrial Operations Brain**.

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
        I -->|Live Compliance & PyVis Graph| K[Streamlit UI]
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

## Key Components
- **Ingestion**: Handles unstructured PDFs and structured maintenance records.
- **Processing**: Extracts entities using SpaCy and builds relationships.
- **Intelligence**: Combines vector search (ChromaDB) with graph traversals (FastAPI) to answer complex regulatory questions.
- **Presentation**: A Streamlit frontend with built-in RBAC (Role-Based Access Control) to serve personalized dashboards to operators and auditors.
