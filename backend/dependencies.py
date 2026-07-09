import os
import json
import logging
import chromadb

from backend.settings import settings
from backend.src.ner_pipeline import NERPipeline
from backend.src.graph_builder import KnowledgeGraphBuilder
from backend.src.agent import build_rca_graph

logger = logging.getLogger(__name__)

# Initialize singletons
ner = NERPipeline()
builder = KnowledgeGraphBuilder()

# Load docs and build graph
if os.path.exists(settings.docs_path):
    try:
        with open(settings.docs_path, "r") as f:
            docs = json.load(f)
        builder.build_graph_from_extracted_data(docs, ner)
    except Exception as e:
        logger.error(f"Error loading docs: {e}")

# Build RCA agent graph
rca_graph = build_rca_graph()


def compute_corpus_coverage() -> float:
    """
    REAL corpus coverage metric.
    """
    try:
        client = chromadb.PersistentClient(path=settings.chroma_db_path)
        total_docs = 0
        for coll_name in ["sops", "work_orders", "regulations"]:
            try:
                coll = client.get_collection(coll_name)
                results = coll.get(include=["metadatas"])
                unique_sources = set()
                if results and results.get("metadatas"):
                    for meta in results["metadatas"]:
                        if meta and meta.get("source"):
                            unique_sources.add(meta["source"])
                total_docs += len(unique_sources)
            except Exception as e:
                logger.warning(
                    f"Collection {coll_name} not found or error accessing: {e}"
                )

        expected_docs = 4
        if os.path.exists(settings.docs_path):
            try:
                with open(settings.docs_path, "r") as f:
                    docs_list = json.load(f)
                expected_docs = len(docs_list)
            except Exception as e:
                logger.error(f"Error reading docs file for coverage: {e}")

        if expected_docs == 0:
            return 0.0
        return round((total_docs / expected_docs) * 100, 1)
    except Exception as e:
        logger.error(f"Error computing corpus coverage: {e}")
        return 0.0


CORPUS_COVERAGE_PCT = compute_corpus_coverage()
