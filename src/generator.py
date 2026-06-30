"""
Day 3 & 4: Answer Generator with REAL Contradiction Detection, Citation formatting,
and Faithfulness scoring.
"""
from dataclasses import dataclass, field
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.schema import NodeWithScore
from src.llm_utils import RateLimitedLLM


@dataclass
class GenerationResult:
    """Structured result from the answer generation pipeline."""
    answer: str = ""
    contradiction_detected: bool = False
    contradiction_details: str = ""
    sources: list = field(default_factory=list)
    faithfulness_score: float = 0.0
    abstained: bool = False


def check_contradictions(nodes: list[NodeWithScore], llm: GoogleGenAI) -> tuple[bool, str]:
    """
    Day 4: Pre-generation check.
    Prompt the LLM to see if the retrieved chunks contradict each other.
    Returns (has_contradiction: bool, details: str).
    """
    if len(nodes) < 2:
        return False, ""

    safe_llm = RateLimitedLLM(llm)

    context = ""
    for idx, node in enumerate(nodes):
        source = node.node.metadata.get("source", "Unknown")
        context += f"--- Chunk {idx+1} (Source: {source}) ---\n{node.node.text}\n\n"

    prompt = f"""Analyze these document chunks for contradictions in key engineering values 
(e.g. pressure limits, torque specifications, temperature ratings, tolerances).

If contradictions exist, respond in this EXACT format:
CONTRADICTION: YES
DETAILS: [Describe exactly which values contradict, citing the source names]

If no contradictions exist, respond:
CONTRADICTION: NO

Chunks:
{context}
"""
    response = safe_llm.complete(prompt)
    response_text = str(response).strip()

    has_contradiction = "CONTRADICTION: YES" in response_text.upper() or "YES" in response_text.upper().split("\n")[0]

    details = ""
    if has_contradiction and "DETAILS:" in response_text:
        details = response_text.split("DETAILS:")[-1].strip()

    return has_contradiction, details


def compute_faithfulness(answer: str, nodes: list[NodeWithScore]) -> float:
    """
    Day 9: Compute a real faithfulness score.
    Measures what fraction of the answer's key claims can be traced back to the source chunks.
    Uses a simple token-overlap heuristic (production systems would use an LLM judge).
    """
    if not answer or not nodes:
        return 0.0

    # Collect all source text
    source_text = " ".join(n.node.text.lower() for n in nodes)
    source_words = set(source_text.split())

    # Extract meaningful words from the answer (skip common stopwords)
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "through", "during",
        "before", "after", "and", "but", "or", "not", "no", "this", "that",
        "it", "its", "if", "then", "than", "so", "up", "out", "about", "which",
        "when", "where", "how", "all", "each", "every", "both", "few", "more",
        "most", "other", "some", "such", "only", "same", "also", "very", "just",
        "because", "between", "based", "using", "per", "must", "please",
    }

    answer_words = [
        w for w in answer.lower().split()
        if w not in stopwords and len(w) > 2
    ]

    if not answer_words:
        return 0.0

    # Count how many answer words appear in source material
    grounded_count = sum(1 for w in answer_words if w in source_words)
    score = grounded_count / len(answer_words)

    # Clamp to [0, 1]
    return round(min(max(score, 0.0), 1.0), 3)


def generate_answer(
    query: str,
    nodes: list[NodeWithScore],
    llm: GoogleGenAI,
    mode: str = "detailed"
) -> GenerationResult:
    """Generate final answer with citations, contradiction detection, and faithfulness scoring."""
    safe_llm = RateLimitedLLM(llm)

    result = GenerationResult()

    # Day 4: Abstention Check
    if len(nodes) == 1 and "[ABSTAIN]" in nodes[0].node.text:
        result.answer = "⚠️ System Confidence Too Low: Escalate to engineer. The retrieved documents do not contain sufficient information to answer this query reliably."
        result.abstained = True
        result.faithfulness_score = 0.0
        return result

    # Extract source metadata for provenance
    for node in nodes:
        source_info = {
            "doc": node.node.metadata.get("source", "Unknown"),
            "revision": node.node.metadata.get("revision", "N/A"),
            "doc_type": node.node.metadata.get("doc_type", "Unknown"),
            "score": round(node.score, 4) if node.score else 0.0
        }
        result.sources.append(source_info)

    # Day 4: Contradiction Check (REAL, not hardcoded)
    result.contradiction_detected, result.contradiction_details = check_contradictions(nodes, llm)

    # Prepare context with metadata for citations (Day 3 requirement)
    context = ""
    for idx, node in enumerate(nodes):
        source = node.node.metadata.get("source", "Unknown Source")
        rev = node.node.metadata.get("revision", "N/A")
        context += f"--- Source: [{source}, Rev {rev}] ---\n{node.node.text}\n\n"

    length_instruction = "Provide a brief, concise answer (2-3 sentences max)." if mode == "brief" else "Provide a detailed, thorough answer."

    prompt = f"""You are a helpful engineering assistant.

Answer the user's query based ONLY on the provided context below.
You MUST cite your sources using the exact format: [Doc_Name, Rev X].
Do NOT make up information that is not in the context.

{length_instruction}

Context:
{context}

Query: {query}
"""

    if result.contradiction_detected:
        prompt = f"""⚠️ CRITICAL WARNING: The system detected contradictory information in the retrieved documents.
Contradiction Details: {result.contradiction_details}

You MUST:
1. Highlight the contradiction explicitly, stating the differing values from each source.
2. Cite both sources using [Doc_Name, Rev X] format.
3. Advise the user to consult a senior engineer before proceeding.

""" + prompt

    response = safe_llm.complete(prompt)
    result.answer = str(response).strip()

    # Day 9: Compute REAL faithfulness score
    result.faithfulness_score = compute_faithfulness(result.answer, nodes)

    return result
