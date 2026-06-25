# RAG LLM Pipeline

A basic Retrieval-Augmented Generation (RAG) pipeline built with LlamaIndex, ChromaDB, and Google Gemini.

## Overview

This project loads a PDF document, splits it into chunks, embeds those chunks locally, stores them in a vector database, and lets you query the document using Gemini as the LLM.

**Pipeline:**
1. Load a text-based PDF using LlamaIndex's PDF reader
2. Chunk the text using `SentenceSplitter` (sentence-aware, fixed-size chunking)
3. Embed chunks locally using `BAAI/bge-small-en-v1.5` (no API key required for embeddings)
4. Store vectors in ChromaDB (persistent local storage)
5. Query the indexed document using Gemini 2.5 Flash Lite

## Tech Stack

- [LlamaIndex](https://www.llamaindex.ai/) — orchestration framework
- [ChromaDB](https://www.trychroma.com/) — local vector store
- [Hugging Face Embeddings](https://huggingface.co/BAAI/bge-small-en-v1.5) — local embedding model
- [Google Gemini](https://ai.google.dev/) — LLM for answering queries

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/Mukilan-s18/Industrial-Operations-Brain.git
cd Industrial-Operations-Brain
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your API key
Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_api_key_here
```
Get a key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 5. (Optional) Generate the demo PDF
If `data/demo.pdf` isn't already included:
```bash
python create_demo_pdf.py
```

## Usage

```bash
python main.py setup     # Load PDF, chunk, embed, and store in ChromaDB
python main.py query     # Run the default test query
python main.py ask "Your question here"   # Ask a custom question
python main.py chat      # Interactive Q&A mode
python main.py both      # Run setup + a test query (default)
```

## Test Gemini API Key

To verify your API key works and check which Gemini models are available to you:
```bash
python test_gemini.py
```

## Project Structure

```
rag-llm-pipeline/
├── main.py              # Core RAG pipeline (setup + query)
├── create_demo_pdf.py   # Generates a sample PDF for testing
├── test_gemini.py       # Standalone Gemini API connectivity test
├── requirements.txt     # Python dependencies
├── .env                 # API keys (not committed)
├── .gitignore
├── data/                # Source PDFs
└── chroma_db/           # Persisted vector store (generated, not committed)
```

## Configuration

Key settings in `main.py`:

| Setting | Value |
|---|---|
| Chunk size | 1024 tokens |
| Chunk overlap | 200 tokens |
| Embedding model | `BAAI/bge-small-en-v1.5` |
| LLM | `gemini-2.5-flash-lite` |
| Vector store | ChromaDB (persistent, local) |

## Notes

- Embeddings run locally — no API calls or cost for the embedding step.
- The script includes retry-with-backoff logic for Gemini API rate limits (429 errors).
- ChromaDB data persists in `./chroma_db` between runs; delete this folder to start fresh.
