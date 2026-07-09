"""
Day 2: Ingestion pipeline with Semantic Chunking and Metadata
Reads from data/corpus/ and creates distinct ChromaDB collections.
"""
import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv

from llama_index.core import Document, StorageContext, VectorStoreIndex, Settings
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import make_url

# Load environment variables
load_dotenv()

# Configuration
CORPUS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "corpus"))
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"
BUCKET_NAME = "industrial-corpus"

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=os.getenv("AWS_ENDPOINT_URL_S3", "http://localhost:9000"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        config=Config(signature_version='s3v4'),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    )

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
    
    # Process each doc_type directory
    for doc_type in ["sops", "work_orders", "regulations"]:
        type_dir = os.path.join(CORPUS_DIR, doc_type)
        if not os.path.exists(type_dir):
            continue
            
        print(f"\nProcessing {doc_type}...")
        
        url_str = os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/vectors").replace("+asyncpg", "")
        url = make_url(url_str)
        vector_store = PGVectorStore.from_params(
            database=url.database,
            host=url.host,
            password=url.password,
            port=url.port,
            user=url.username,
            table_name=doc_type,
            embed_dim=384,
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        s3 = get_s3_client()
        try:
            s3.head_bucket(Bucket=BUCKET_NAME)
        except:
            s3.create_bucket(Bucket=BUCKET_NAME)

        documents = []
        for filename in os.listdir(type_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(type_dir, filename)
                object_key = f"{doc_type}/{filename}"
                
                # Upload to Object Storage
                s3.upload_file(filepath, BUCKET_NAME, object_key)
                
                # Download/Read from Object Storage
                response = s3.get_object(Bucket=BUCKET_NAME, Key=object_key)
                text = response['Body'].read().decode('utf-8')
                
                # Add metadata
                doc = Document(
                    text=text,
                    metadata={
                        "doc_type": doc_type.upper(),
                        "source": f"s3://{BUCKET_NAME}/{object_key}",
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
        print("  -> Indexing in PGVector...")
        index = VectorStoreIndex(
            nodes,
            storage_context=storage_context,
            embed_model=embed_model
        )
        print(f"  -> Done indexing {doc_type}.")

if __name__ == "__main__":
    ingest()
