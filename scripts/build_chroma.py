"""
RAG Pipeline - Day 1: Basic RAG with LlamaIndex + ChromaDB + Gemini
====================================================================
- Loads a text-based PDF directly using LlamaIndex's PDF reader
- Chunks it with SentenceSplitter (fixed-size, sentence-aware)
- Embeds chunks using BAAI/bge-small-en-v1.5 (local, no API needed)
- Stores vectors in ChromaDB (persistent local storage)
- Queries using Gemini 2.5 Flash Lite as the LLM

Chunking Strategy: Fixed-size via SentenceSplitter
  - chunk_size=1024 tokens, chunk_overlap=200 tokens
  - Splits at sentence boundaries (not mid-word)
  - Good baseline for well-structured documents
  - Can upgrade to semantic chunking later if retrieval quality is poor

Usage:
    python main.py setup     # Load PDF, chunk, embed, store in ChromaDB
    python main.py query     # Run a test query against the indexed document
    python main.py both      # Do both setup + query (default)
"""

import sys
import os

# Fix Windows console encoding for special characters
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

# --- Load environment ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("[ERROR] GOOGLE_API_KEY not found in .env file")
    sys.exit(1)

# --- Configuration ---
PDF_PATH = os.path.join("data", "demo.pdf")
CHROMA_DB_PATH = "./chroma_db"
CHROMA_COLLECTION_NAME = "rag_demo"
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 200
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"
LLM_MODEL_NAME = "models/gemini-2.5-flash-lite"


# =====================================================================
# STEP 3: ChromaDB + PDF Loading/Chunking
# =====================================================================

def setup_index():
    """Load PDF, chunk it, embed, and store in ChromaDB."""
    import chromadb
    from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.core import Settings

    # 1. Configure embedding model (local, no API key needed)
    print(f"\n[1/4] Loading embedding model: {EMBED_MODEL_NAME}")
    embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)
    Settings.embed_model = embed_model
    print("  -> Embedding model loaded (dimension: 384)")

    # 2. Load the PDF
    print(f"\n[2/4] Loading PDF: {PDF_PATH}")
    if not os.path.exists(PDF_PATH):
        print(f"  [ERROR] File not found: {PDF_PATH}")
        sys.exit(1)

    reader = SimpleDirectoryReader(input_files=[PDF_PATH])
    documents = reader.load_data()
    total_chars = sum(len(d.text) for d in documents)
    print(f"  -> Loaded {len(documents)} page(s), {total_chars:,} characters")

    # 3. Chunk the documents
    print(f"\n[3/4] Chunking with SentenceSplitter (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    nodes = splitter.get_nodes_from_documents(documents)
    print(f"  -> Created {len(nodes)} chunks")

    # Show a preview of the first few chunks
    for i, node in enumerate(nodes[:3]):
        text_preview = node.text[:100].replace("\n", " ")
        print(f"  -> Chunk {i+1}: [{len(node.text)} chars] \"{text_preview}...\"")
    if len(nodes) > 3:
        print(f"  -> ... and {len(nodes) - 3} more chunks")

    # 4. Set up ChromaDB and store embeddings
    print(f"\n[4/4] Setting up ChromaDB at: {CHROMA_DB_PATH}")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Delete existing collection if it exists (fresh start)
    try:
        chroma_client.delete_collection(CHROMA_COLLECTION_NAME)
        print(f"  -> Cleared existing collection: {CHROMA_COLLECTION_NAME}")
    except Exception:
        pass

    chroma_collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print(f"  -> Embedding and indexing {len(nodes)} chunks (this may take a moment)...")
    index = VectorStoreIndex(
        nodes,
        storage_context=storage_context,
        embed_model=embed_model,
    )

    print(f"  -> Done! {chroma_collection.count()} vectors stored in ChromaDB")
    print("\n[SETUP COMPLETE] Index is ready for queries.")
    return index


# =====================================================================
# STEP 4: Query the index
# =====================================================================

def query_index(query_text: str = "Your question here"):
    """Load the existing ChromaDB index and run a query."""
    import chromadb
    import time
    from llama_index.core import VectorStoreIndex
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.llms.google_genai import GoogleGenAI
    from llama_index.core import Settings

    # 1. Load embedding model
    print(f"\n[1/3] Loading embedding model: {EMBED_MODEL_NAME}")
    embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)
    Settings.embed_model = embed_model

    # 2. Connect to existing ChromaDB
    print(f"[2/3] Connecting to ChromaDB at: {CHROMA_DB_PATH}")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    chroma_collection = chroma_client.get_collection(CHROMA_COLLECTION_NAME)
    print(f"  -> Found {chroma_collection.count()} vectors in collection")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=embed_model,
    )

    # 3. Set up Gemini LLM and query
    print(f"[3/3] Querying with Gemini ({LLM_MODEL_NAME})...")
    llm = GoogleGenAI(model=LLM_MODEL_NAME, api_key=GOOGLE_API_KEY)
    Settings.llm = llm

    query_engine = index.as_query_engine(llm=llm, similarity_top_k=3)

    print(f"\n{'='*60}")
    print(f"QUERY: {query_text}")
    print(f"{'='*60}")

    # Retry with backoff if rate limited
    max_retries = 3
    response = None
    for attempt in range(max_retries):
        try:
            response = query_engine.query(query_text)
            break
        except Exception as e:
            error_msg = str(e)
            if ("429" in error_msg or "quota" in error_msg.lower()) and attempt < max_retries - 1:
                wait_time = 60 * (attempt + 1)
                print(f"\n[RATE LIMITED] Waiting {wait_time}s before retry (attempt {attempt+2}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise

    print(f"\nANSWER:\n{response.response}")
    print(f"\n{'='*60}")
    print(f"Sources used: {len(response.source_nodes)} chunks")
    for i, node in enumerate(response.source_nodes):
        score = node.score if node.score else 0.0
        text_preview = node.text[:80].replace("\n", " ")
        print(f"  [{i+1}] score={score:.4f} | \"{text_preview}...\"")
    print(f"{'='*60}")

    return response



# =====================================================================
# CLI entry point
# =====================================================================

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"

    if mode == "setup":
        setup_index()
    elif mode == "query":
        query_index()
    elif mode == "ask":
        # Pass a custom question: python main.py ask "Your question here"
        if len(sys.argv) < 3:
            print("Usage: python main.py ask \"Your question here\"")
            sys.exit(1)
        question = " ".join(sys.argv[2:])
        query_index(question)
    elif mode == "chat":
        # Interactive mode: ask multiple questions in a loop
        print("\n[CHAT MODE] Ask questions about the document. Type 'exit' to quit.\n")
        while True:
            question = input("You: ").strip()
            if question.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break
            if not question:
                continue
            query_index(question)
            print()
    elif mode == "both":
        setup_index()
        print("\n" + "=" * 60)
        print("Now running a test query...")
        print("=" * 60)
        query_index()
    else:
        print("Usage: python main.py [setup|query|ask|chat|both]")
        print("  setup  - Load PDF, chunk, embed, store in ChromaDB")
        print("  query  - Run the default test query")
        print('  ask    - Ask a question:  python main.py ask "Your question"')
        print("  chat   - Interactive mode: ask multiple questions")
        print("  both   - Do setup then query (default)")
