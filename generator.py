"""
Day 3 & 4: Answer Generator with Contradiction Detection and Citation formatting.
"""
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.schema import NodeWithScore

def check_contradictions(nodes: list[NodeWithScore], llm: GoogleGenAI) -> bool:
    """
    Day 4: Pre-generation check.
    Prompt the LLM to see if the retrieved chunks contradict each other.
    """
    context = ""
    for idx, node in enumerate(nodes):
        context += f"--- Chunk {idx+1} ---\n{node.node.text}\n"
        
    prompt = f"""Look at these chunks. Do they contradict each other regarding key values (e.g. pressure values, torque specifications)? 
Respond with EXACTLY 'YES' or 'NO'.

{context}
"""
    response = llm.complete(prompt)
    return "YES" in str(response).upper()

def generate_answer(query: str, nodes: list[NodeWithScore], llm: GoogleGenAI, mode: str = "detailed") -> str:
    """Generate final answer with citations."""
    
    # Day 4: Abstention Check
    if len(nodes) == 1 and "[ABSTAIN]" in nodes[0].node.text:
        return "System Confidence Low: Escalate to engineer."
        
    # Day 4: Contradiction Check
    has_contradiction = check_contradictions(nodes, llm)
    
    # Prepare context with metadata for citations (Day 3 requirement)
    context = ""
    for idx, node in enumerate(nodes):
        source = node.node.metadata.get("source", "Unknown Source")
        rev = node.node.metadata.get("revision", "N/A")
        context += f"--- Source: [{source}, Rev {rev}] ---\n{node.node.text}\n\n"
        
    length_instruction = "Provide a brief, concise answer." if mode == "brief" else "Provide a detailed answer."
        
    prompt = f"""You are a helpful engineering assistant. 
    
Answer the user's query based ONLY on the provided context below.
You MUST cite your sources using the exact format: [Doc_Name, Rev X].

{length_instruction}

Context:
{context}

Query: {query}
"""

    if has_contradiction:
        prompt = f"""WARNING: The system detected contradictory information in the retrieved documents.
Please highlight the contradiction in your response, explicitly pointing out the differing values or instructions, and advise the user to consult an engineer.

""" + prompt

    response = llm.complete(prompt)
    return str(response)
