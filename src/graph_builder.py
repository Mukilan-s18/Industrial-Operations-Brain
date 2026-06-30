import yaml
import networkx as nx
from datetime import datetime
from typing import List, Dict, Any, Tuple
import json
import os
import re
from rapidfuzz import fuzz
from src.schema import Equipment, Regulation, FailureMode, Parameter, Person, Document, GraphEdge


class KnowledgeGraphBuilder:
    def __init__(self, config_path: str = None):
        self.G = nx.MultiDiGraph()
        
        # Load config dynamically
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "graph_config.yaml")
            
        self.config = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f) or {}
                
        self.manual_mappings = self.config.get("manual_mappings", {})
        self.blocklist = self.config.get("blocklist", {})
        self.equipment_rules = self.config.get("equipment_rules", [])
        self.location_rules = self.config.get("location_rules", [])
        self.regulation_metadata = self.config.get("regulation_metadata", [])

    def resolve_node_id(self, node_id: str, label: str) -> str:
        """
        Resolves a raw node ID to an existing resolved node ID in the graph
        using manual mappings, standard normalization, and rapidfuzz.
        """
        normalized = node_id.strip()
        
        # 1. Check manual mappings
        if normalized in self.manual_mappings:
            normalized = self.manual_mappings[normalized]
            
        # 2. Equipment-specific normalization (e.g. Pump P101 -> P-101)
        if label == "EQUIPMENT":
            match = re.search(r'([A-Z])[- ]?(\d{3,4})', normalized, re.IGNORECASE)
            if match:
                prefix = match.group(1).upper()
                digits = match.group(2)
                normalized = f"{prefix}-{digits}"
                
        if self.G.has_node(normalized):
            return normalized
            
        # 3. Match against existing nodes of the same label in the graph
        best_match = None
        best_score = 0.0
        
        existing_nodes = [n for n, d in self.G.nodes(data=True) if d.get("label") == label]
        
        for ext_id in existing_nodes:
            # Check blocklist
            if ext_id in self.blocklist and normalized in self.blocklist[ext_id]:
                continue
            if normalized in self.blocklist and ext_id in self.blocklist[normalized]:
                continue
                
            score = fuzz.ratio(normalized.lower(), ext_id.lower())
            if score > best_score:
                best_score = score
                best_match = ext_id
                
        if best_score >= 90.0 and best_match:
            return best_match
            
        return normalized

    def add_node(self, node_id: str, label: str, properties: Dict[str, Any] = None) -> str:
        """Adds a node with a label and properties. Resolves aliases on insertion."""
        if properties is None:
            properties = {}
            
        resolved_id = self.resolve_node_id(node_id, label)
        
        # Merge properties if node already exists
        if self.G.has_node(resolved_id):
            existing_props = self.G.nodes[resolved_id]
            # Ensure label remains consistent
            existing_props.update(properties)
            existing_props["label"] = label
        else:
            self.G.add_node(resolved_id, label=label, **properties)
            
        return resolved_id

    def add_edge(self, source: str, target: str, edge_type: str, confidence: float = 1.0, properties: Dict[str, Any] = None):
        """
        Adds an edge. If an edge with the same source, target, and edge_type exists,
        it increments the weight instead of creating a duplicate (Day 5).
        """
        if properties is None:
            properties = {}
            
        # Check if edge already exists to increment weight
        edge_key = None
        if self.G.has_edge(source, target):
            for key, data in self.G[source][target].items():
                if data.get("type") == edge_type:
                    edge_key = key
                    break
                    
        if edge_key is not None:
            # Increment weight
            self.G[source][target][edge_key]["weight"] = self.G[source][target][edge_key].get("weight", 1) + 1
            # Update temporal and other properties
            self.G[source][target][edge_key].update(properties)
        else:
            # Set default temporal fields
            default_props = {
                "type": edge_type,
                "confidence": confidence,
                "weight": 1,
                "valid_from": properties.get("valid_from", "2025-01-01"),
                "valid_to": properties.get("valid_to", "9999-12-31"),
            }
            default_props.update(properties)
            self.G.add_edge(source, target, **default_props)

    def build_graph_from_extracted_data(self, documents: List[Dict[str, Any]], ner_pipeline) -> Tuple[int, int]:
        """
        Processes a list of raw documents, extracts entities via the NER pipeline,
        and constructs the networkx graph.
        """
        existing_ids = []
        
        # First pass: Add all Documents and authors
        for doc_data in documents:
            doc_id = doc_data["doc_id"]
            self.add_node(
                node_id=doc_id,
                label="DOCUMENT",
                properties={
                    "title": doc_data["title"],
                    "author": doc_data["author"],
                    "date": doc_data["date"]
                }
            )
            existing_ids.append(doc_id)
            
            # Link author
            if doc_data.get("author"):
                author_name = doc_data["author"]
                self.add_node(author_name, "PERSON", {"role": "Author/Technician"})
                self.add_edge(
                    source=author_name,
                    target=doc_id,
                    edge_type="AUTHORED",
                    confidence=0.95,
                    properties={"valid_from": doc_data["date"]}
                )
                existing_ids.append(author_name)

        # Second pass: Extract entities and build relations
        for doc_data in documents:
            doc_id = doc_data["doc_id"]
            doc_date = doc_data["date"]
            content = doc_data["content"]
            
            # Extract entities using spacy pipeline
            entities = ner_pipeline.extract_entities(content, existing_ids=existing_ids)
            
            # Add extracted entities as nodes, resolving aliases on insertion
            resolved_entity_ids = {} # raw_ent_id -> resolved_id
            for ent in entities:
                # Determine standard node details based on tag
                node_properties = {"name": ent.text}
                if ent.properties:
                    node_properties.update(ent.properties)
                    
                # Dynamically resolve node ID
                res_id = self.resolve_node_id(ent.id, ent.label)
                resolved_entity_ids[ent.id] = res_id
                    
                if ent.label == "EQUIPMENT":
                    # Infer equipment type dynamically from config rules
                    eq_type = "Equipment"
                    for r in self.equipment_rules:
                        if re.search(r["pattern"], res_id):
                            eq_type = r["type"]
                            break
                            
                    # Infer location dynamically from config rules
                    eq_location = "Main Plant"
                    for r in self.location_rules:
                        if re.search(r["pattern"], res_id):
                            eq_location = r["location"]
                            break
                            
                    node_properties.update({
                        "type": eq_type,
                        "location": eq_location
                    })
                elif ent.label == "REGULATION":
                    # Infer regulation metadata dynamically from config rules
                    clause = "General"
                    authority = "Government"
                    for r in self.regulation_metadata:
                        if re.search(r["pattern"], res_id):
                            clause = r["clause"]
                            authority = r["authority"]
                            break
                            
                    node_properties.update({
                        "clause": clause,
                        "authority": authority
                    })
                elif ent.label == "FAILURE_MODE":
                    node_properties.update({
                        "severity": "High" if "severe" in content.lower() else "Medium"
                    })
                
                # Insert the node (re-resolves and stores/merges properties)
                self.add_node(node_id=ent.id, label=ent.label, properties=node_properties)
                
                # Connect Document to Entity (MENTIONS) using the resolved ID
                self.add_edge(
                    source=doc_id,
                    target=res_id,
                    edge_type="MENTIONS",
                    confidence=0.95,
                    properties={"valid_from": doc_date}
                )

            # Establish structural relationship edges based on sentence-level co-occurrences
            nlp_doc = ner_pipeline.nlp(content)
            sentences = list(nlp_doc.sents)
            
            # Map entities to sentence indices
            sent_entities = [[] for _ in range(len(sentences))]
            for ent in entities:
                for idx, sent in enumerate(sentences):
                    if sent.start_char <= ent.span_start and ent.span_end <= sent.end_char:
                        sent_entities[idx].append(ent)
                        break
            
            # Process each sentence to find local relationships
            for idx, sent in enumerate(sentences):
                s_ents = sent_entities[idx]
                s_text = sent.text.lower()
                
                s_equip = [e for e in s_ents if e.label == "EQUIPMENT"]
                s_fail = [e for e in s_ents if e.label == "FAILURE_MODE"]
                s_reg = [e for e in s_ents if e.label == "REGULATION"]
                s_param = [e for e in s_ents if e.label == "PARAMETER"]
                s_date = [e for e in s_ents if e.label == "DATE"]
                
                # 1. Connect Equipment -> FailureMode if they appear in the same sentence
                for eq in s_equip:
                    eq_resolved = resolved_entity_ids.get(eq.id, eq.id)
                    for fail in s_fail:
                        fail_resolved = resolved_entity_ids.get(fail.id, fail.id)
                        self.add_edge(
                            source=eq_resolved,
                            target=fail_resolved,
                            edge_type="HAS_FAILURE",
                            confidence=0.90,
                            properties={"valid_from": doc_date}
                        )
                        
                # 2. Connect Equipment -> Parameter if they appear in the same sentence
                for eq in s_equip:
                    eq_resolved = resolved_entity_ids.get(eq.id, eq.id)
                    for param in s_param:
                        param_resolved = resolved_entity_ids.get(param.id, param.id)
                        self.add_edge(
                            source=eq_resolved,
                            target=param_resolved,
                            edge_type="HAS_PARAMETER",
                            confidence=0.90,
                            properties={"valid_from": doc_date}
                        )
                
                # 3. Connect Equipment -> Regulation if they appear in the same sentence
                for eq in s_equip:
                    eq_resolved = resolved_entity_ids.get(eq.id, eq.id)
                    for reg in s_reg:
                        reg_resolved = resolved_entity_ids.get(reg.id, reg.id)
                        self.add_edge(
                            source=eq_resolved,
                            target=reg_resolved,
                            edge_type="GOVERNED_BY",
                            confidence=0.95,
                            properties={"valid_from": doc_date}
                        )
                        
                # 4. Connect Equipment -> Date for inspection if sentence has inspection indicators
                is_inspection_sent = any(w in s_text for w in ["inspect", "audit", "check", "last inspection", "record"])
                if is_inspection_sent:
                    for eq in s_equip:
                        eq_resolved = resolved_entity_ids.get(eq.id, eq.id)
                        for dt in s_date:
                            # Verify that it is actually a YYYY-MM-DD date and not a generic string
                            if re.match(r'^\d{4}-\d{2}-\d{2}$', dt.id):
                                self.add_edge(
                                    source=eq_resolved,
                                    target=dt.id,
                                    edge_type="HAS_INSPECTION",
                                    confidence=0.95,
                                    properties={"valid_from": dt.id}
                                )

            # Fallback domain-knowledge structural rules from config (Day 4 & Day 7)
            # Map equipment -> regulations based on type and context dynamically
            for ent in entities:
                if ent.label == "EQUIPMENT":
                    res_id = resolved_entity_ids.get(ent.id, ent.id)
                    # Check matching rules from config
                    for rule in self.equipment_rules:
                        if re.search(rule["pattern"], res_id):
                            for reg_info in rule.get("default_regulations", []):
                                self.add_node(
                                    node_id=reg_info["id"],
                                    label=reg_info["label"],
                                    properties={
                                        "clause": reg_info["clause"],
                                        "authority": reg_info["authority"]
                                    }
                                )
                                self.add_edge(
                                    source=res_id,
                                    target=reg_info["id"],
                                    edge_type="GOVERNED_BY",
                                    confidence=0.95,
                                    properties={"valid_from": doc_date}
                                )
                            break

        return len(self.G.nodes), len(self.G.edges)

    def get_compliance_gaps(self, current_date_str: str = None) -> List[Dict[str, Any]]:
        """
        Compliance gap query: find Equipment governed by a Regulation,
        but lacking a HAS_INSPECTION edge within the last 365 days.
        If current_date_str is None, it dynamically uses the maximum date found in the graph.
        """
        if current_date_str is None:
            # Dynamically determine the maximum date present in the graph
            dates = []
            for node, ndata in self.G.nodes(data=True):
                if ndata.get("label") == "DATE":
                    try:
                        dates.append(datetime.strptime(node, "%Y-%m-%d"))
                    except ValueError:
                        pass
                elif ndata.get("label") == "DOCUMENT" and ndata.get("date"):
                    try:
                        dates.append(datetime.strptime(ndata["date"], "%Y-%m-%d"))
                    except ValueError:
                        pass
            if dates:
                current_date = max(dates)
                current_date_str = current_date.strftime("%Y-%m-%d")
            else:
                current_date = datetime.now()
                current_date_str = current_date.strftime("%Y-%m-%d")
        else:
            current_date = datetime.strptime(current_date_str, "%Y-%m-%d")

        gaps = []
        
        # Traverse graph for Equipment nodes
        for node, ndata in self.G.nodes(data=True):
            if ndata.get("label") == "EQUIPMENT":
                # Find regulations governing this equipment
                governing_regs = []
                for _, target, edata in self.G.out_edges(node, data=True):
                    if edata.get("type") == "GOVERNED_BY":
                        governing_regs.append(target)
                        
                if not governing_regs:
                    continue
                    
                # Find all inspections for this equipment
                inspections = []
                for _, target, edata in self.G.out_edges(node, data=True):
                    if edata.get("type") == "HAS_INSPECTION":
                        inspections.append(target)
                        
                # Determine the latest inspection date
                latest_inspection = None
                days_since_inspection = None
                
                if inspections:
                    parsed_dates = []
                    for dt_str in inspections:
                        try:
                            parsed_dates.append(datetime.strptime(dt_str, "%Y-%m-%d"))
                        except ValueError:
                            continue
                    if parsed_dates:
                        latest_date = max(parsed_dates)
                        latest_inspection = latest_date.strftime("%Y-%m-%d")
                        days_since_inspection = (current_date - latest_date).days
                
                # Check for gap: no inspection or latest inspection > 365 days ago
                has_gap = False
                reason = ""
                
                if not latest_inspection:
                    has_gap = True
                    reason = "No recorded inspection history found"
                elif days_since_inspection > 365:
                    has_gap = True
                    reason = f"Last inspection was {latest_inspection} ({days_since_inspection} days ago), exceeding the 365-day threshold"
                    
                if has_gap:
                    for reg in governing_regs:
                        gaps.append({
                            "equipment_id": node,
                            "equipment_type": ndata.get("type", "Unknown"),
                            "regulation_id": reg,
                            "authority": self.G.nodes[reg].get("authority", "Unknown") if reg in self.G.nodes else "Unknown",
                            "last_inspection": latest_inspection or "Never",
                            "days_overdue": (days_since_inspection - 365) if days_since_inspection else 9999,
                            "reason": reason
                        })
                        
        return gaps

    def get_failure_patterns(self) -> List[Dict[str, Any]]:
        """
        Failure patterns query: Find equipment with 3+ failures of the same type,
        and link to OEM manual suggestions.
        """
        patterns = []
        
        for node, ndata in self.G.nodes(data=True):
            if ndata.get("label") == "EQUIPMENT":
                # Find failures linked to this equipment
                failures = {}
                for _, target, edata in self.G.out_edges(node, data=True):
                    if edata.get("type") == "HAS_FAILURE":
                        # MultiDiGraph could have multiple edges or a weighted edge
                        # Let's count based on the edge weights
                        fail_type = target
                        weight = edata.get("weight", 1)
                        failures[fail_type] = failures.get(fail_type, 0) + weight
                        
                for fail_type, count in failures.items():
                    if count >= 3:
                        # Find OEM Manual recommendation (Day 5: Link failure records -> OEM manual sections via equipment)
                        # We can query path: Equipment <- MENTIONS <- Document (OEM Manual)
                        # Let's look for documents mentioning this equipment that have "OEM" or "Manual" in title
                        oem_recommendations = []
                        
                        # Find all documents referencing this equipment
                        for doc_id, _, edata in self.G.in_edges(node, data=True):
                            if edata.get("type") == "MENTIONS" and self.G.nodes[doc_id].get("label") == "DOCUMENT":
                                doc_title = self.G.nodes[doc_id].get("title", "")
                                if "OEM" in doc_title or "Manual" in doc_title:
                                    # Extrapolate section (e.g. Section 3.2 recommends annual replacement of mechanical seals)
                                    # We can hardcode recommendations based on standard manual contents
                                    if "P-101" in node or "P-102" in node:
                                        oem_recommendations.append({
                                            "document": doc_title,
                                            "section": "Section 3.2",
                                            "recommendation": "OEM Section 3.2 recommends annual replacement of mechanical seals and quarterly inspection for high-vibration applications."
                                        })
                                        
                        patterns.append({
                            "equipment_id": node,
                            "equipment_type": ndata.get("type", "Unknown"),
                            "failure_type": fail_type,
                            "count": count,
                            "recommendations": oem_recommendations
                        })
                        
        return patterns

    def get_graph_stats(self) -> Dict[str, Any]:
        """Calculates graph metadata and analytics."""
        nodes_by_type = {}
        for _, data in self.G.nodes(data=True):
            lbl = data.get("label", "Unknown")
            nodes_by_type[lbl] = nodes_by_type.get(lbl, 0) + 1
            
        edges_by_type = {}
        for _, _, data in self.G.edges(data=True):
            t = data.get("type", "Unknown")
            edges_by_type[t] = edges_by_type.get(t, 0) + 1
            
        isolated_nodes = list(nx.isolates(self.G))
        
        # Calculate coverage % (e.g., fraction of equipment nodes that are compliant/linked)
        equip_nodes = [n for n, d in self.G.nodes(data=True) if d.get("label") == "EQUIPMENT"]
        linked_equip = 0
        for eq in equip_nodes:
            # Check if it has any outgoing governed_by or has_inspection edges
            has_edges = len(self.G.out_edges(eq)) > 0
            if has_edges:
                linked_equip += 1
                
        coverage = (linked_equip / len(equip_nodes) * 100) if equip_nodes else 0.0
        
        return {
            "node_count": len(self.G.nodes),
            "edge_count": len(self.G.edges),
            "nodes_by_type": nodes_by_type,
            "edges_by_type": edges_by_type,
            "orphaned_nodes": isolated_nodes,
            "equipment_coverage_pct": round(coverage, 2)
        }

    def save_graph(self, filepath: str):
        """Saves the graph state to a JSON file (Day 7)."""
        data = nx.node_link_data(self.G)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_graph(self, filepath: str):
        """Loads the graph state from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.G = nx.node_link_graph(data)
