"""
Day 3: Mock Graph API (Simulating Person 2's API)
Returns structured knowledge graph data for hybrid RAG.
"""

def query_graph_neighbors(entity: str) -> str:
    """Mock API returning 1-hop neighbors from the Knowledge Graph."""
    entity = entity.upper()
    
    # Mock data for demonstration
    graph_data = {
        "P-101": [
            {"relation": "HAS_FAILURE_MODE", "target": "Seal Leak", "date": "2025-11-04"},
            {"relation": "IS_LOCATED_IN", "target": "Unit 3"},
            {"relation": "HAS_COMPONENT", "target": "HV-204"},
            {"relation": "HAS_FAILURE_MODE", "target": "Vibration Trip", "date": "2024-06-15"}
        ],
        "HV-204": [
            {"relation": "PART_OF", "target": "P-101"},
            {"relation": "HAS_SPEC", "target": "Max Pressure 120 PSI"}
        ]
    }
    
    if entity in graph_data:
        neighbors = graph_data[entity]
        context = f"Graph Context for {entity}:\n"
        for n in neighbors:
            date_str = f" (Date: {n['date']})" if 'date' in n else ""
            context += f"- {entity} {n['relation']} {n['target']}{date_str}\n"
        return context
        
    return ""

def extract_entities(query: str) -> list[str]:
    """Extremely naive entity extraction for the mock."""
    entities = []
    if "P-101" in query.upper() or "P101" in query.upper():
        entities.append("P-101")
    if "HV-204" in query.upper() or "HV204" in query.upper():
        entities.append("HV-204")
    return entities
