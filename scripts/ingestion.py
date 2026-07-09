"""
Day 2: Ingestion pipeline with Semantic Chunking and Metadata
Reads from data/corpus/ and creates distinct ChromaDB collections.
"""
import os
from dotenv import load_dotenv

import chromadb
from llama_index.core import Document, StorageContext, VectorStoreIndex, Settings
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

# Load environment variables
load_dotenv()

# Configuration
CORPUS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "corpus"))
CHROMA_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"

def get_revision(text: str) -> int:
    """Extract revision number from text if present, else 1."""
    for line in text.splitlines()[:5]:
        if "Revision:" in line:
            try:
                return int(line.split("Revision:")[1].strip())
            except ValueError:
                pass
    return 1

def ingest():
    print(f"Loading embedding model: {EMBED_MODEL_NAME}")
    embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)
    Settings.embed_model = embed_model
    
    # Initialize Semantic Splitter
    # Tuning breakpoint percentile threshold. Default is 95, lower means more splits.
    print("Initializing SemanticSplitterNodeParser...")
    splitter = SemanticSplitterNodeParser(
        buffer_size=1, 
        breakpoint_percentile_threshold=90, 
        embed_model=embed_model
    )
    
    # Initialize Chroma Client
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    # Process each doc_type directory
    for doc_type in ["sops", "work_orders", "regulations"]:
        type_dir = os.path.join(CORPUS_DIR, doc_type)
        if not os.path.exists(type_dir):
            continue
            
        print(f"\nProcessing {doc_type}...")
        
        # Reset collection
        try:
            chroma_client.delete_collection(doc_type)
            print(f"  -> Cleared existing collection: {doc_type}")
        except Exception:
            pass
            
        collection = chroma_client.get_or_create_collection(doc_type)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        documents = []
        for filename in os.listdir(type_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(type_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                
                # Add metadata
                doc = Document(
                    text=text,
                    metadata={
                        "doc_type": doc_type.upper(),
                        "source": filename,
                        "revision": get_revision(text)
                    }
                )
                documents.append(doc)
                
        if not documents:
            print(f"  -> No documents found in {type_dir}")
            continue
            
        print(f"  -> Loaded {len(documents)} document(s)")
        
        # Split into nodes using semantic chunking
        nodes = splitter.get_nodes_from_documents(documents)
        print(f"  -> Created {len(nodes)} semantic chunks")
        
        # Index
        print("  -> Indexing in ChromaDB...")
        index = VectorStoreIndex(
            nodes,
            storage_context=storage_context,
            embed_model=embed_model
        )
        print(f"  -> Done indexing {doc_type}.")

if __name__ == "__main__":
    ingest()
