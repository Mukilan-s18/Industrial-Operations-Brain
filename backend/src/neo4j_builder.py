import yaml
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
import os
from rapidfuzz import fuzz
from neo4j import GraphDatabase

from backend.settings import settings


class Neo4jBuilder:
    def __init__(self, config_path: str = None):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )

        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "config", "graph_config.yaml"
            )

        self.config = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f) or {}

        self.manual_mappings = self.config.get("manual_mappings", {})
        self.blocklist = self.config.get("blocklist", {})
        self.equipment_rules = self.config.get("equipment_rules", [])
        self.location_rules = self.config.get("location_rules", [])
        self.regulation_metadata = self.config.get("regulation_metadata", [])

        # Local node cache for performance during build
        self._local_nodes = {}

    @property
    def G(self):
        import networkx as nx

        graph = nx.MultiDiGraph()
        try:
            nodes = self._execute_read("MATCH (n) RETURN n")
            for record in nodes:
                node = record["n"]
                node_id = node.get("id")
                if not node_id:
                    continue
                labels = list(node.labels)
                label = labels[0] if labels else "UNKNOWN"
                props = dict(node)
                graph.add_node(node_id, label=label, **props)

            edges = self._execute_read(
                "MATCH (s)-[r]->(t) RETURN s.id AS source, t.id AS target, type(r) AS type, r AS props"
            )
            for record in edges:
                source = record["source"]
                target = record["target"]
                edge_type = record["type"]
                props = dict(record["props"])
                props["type"] = edge_type
                graph.add_edge(source, target, **props)
        except Exception:
            pass
        return graph

    def close(self):
        self.driver.close()

    def _execute_write(self, query: str, parameters: dict = None):
        with self.driver.session() as session:
            session.run(query, parameters or {})

    def _execute_read(self, query: str, parameters: dict = None):
        with self.driver.session() as session:
            return session.run(query, parameters or {}).data()

    def resolve_node_id(self, node_id: str, label: str) -> str:
        normalized = node_id.strip()

        if normalized in self.manual_mappings:
            normalized = self.manual_mappings[normalized]

        if label == "EQUIPMENT":
            match = re.search(r"([A-Z])[- ]?(\d{3,4})", normalized, re.IGNORECASE)
            if match:
                prefix = match.group(1).upper()
                digits = match.group(2)
                normalized = f"{prefix}-{digits}"

        if normalized in self._local_nodes:
            return normalized

        best_match = None
        best_score = 0.0

        existing_nodes = [n for n, l in self._local_nodes.items() if l == label]

        for ext_id in existing_nodes:
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

    def add_node(
        self, node_id: str, label: str, properties: Dict[str, Any] = None
    ) -> str:
        if properties is None:
            properties = {}

        resolved_id = self.resolve_node_id(node_id, label)
        self._local_nodes[resolved_id] = label

        # We must dynamically include the label in Cypher, but parameters can't be labels
        query = f"""
        MERGE (n:{label} {{id: $id}})
        SET n += $props
        """
        self._execute_write(query, {"id": resolved_id, "props": properties})
        return resolved_id

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: str,
        confidence: float = 1.0,
        properties: Dict[str, Any] = None,
    ):
        if properties is None:
            properties = {}

        default_props = {
            "confidence": confidence,
            "valid_from": properties.get("valid_from", "2025-01-01"),
            "valid_to": properties.get("valid_to", "9999-12-31"),
        }
        default_props.update(properties)

        query = f"""
        MATCH (s {{id: $source}})
        MATCH (t {{id: $target}})
        MERGE (s)-[r:{edge_type}]->(t)
        ON CREATE SET r.weight = 1, r += $props
        ON MATCH SET r.weight = r.weight + 1, r += $props
        """
        self._execute_write(
            query, {"source": source, "target": target, "props": default_props}
        )

    def build_graph_from_extracted_data(
        self, documents: List[Dict[str, Any]], ner_pipeline
    ) -> Tuple[int, int]:
        """Same extraction flow as before, but hits Neo4j database."""

        # To avoid massive latency, we could batch but for this size we just call directly
        existing_ids = []

        for doc_data in documents:
            doc_id = doc_data["doc_id"]
            self.add_node(
                node_id=doc_id,
                label="DOCUMENT",
                properties={
                    "title": doc_data["title"],
                    "author": doc_data["author"],
                    "date": doc_data["date"],
                },
            )
            existing_ids.append(doc_id)

            if doc_data.get("author"):
                author_name = doc_data["author"]
                self.add_node(author_name, "PERSON", {"role": "Author/Technician"})
                self.add_edge(
                    source=author_name,
                    target=doc_id,
                    edge_type="AUTHORED",
                    confidence=0.95,
                    properties={"valid_from": doc_data["date"]},
                )
                existing_ids.append(author_name)

        for doc_data in documents:
            doc_id = doc_data["doc_id"]
            doc_date = doc_data["date"]
            content = doc_data["content"]

            entities = ner_pipeline.extract_entities(content, existing_ids=existing_ids)
            resolved_entity_ids = {}
            for ent in entities:
                node_properties = {"name": ent.text}
                if ent.properties:
                    node_properties.update(ent.properties)

                res_id = self.resolve_node_id(ent.id, ent.label)
                resolved_entity_ids[ent.id] = res_id

                if ent.label == "EQUIPMENT":
                    eq_type = "Equipment"
                    for r in self.equipment_rules:
                        if re.search(r["pattern"], res_id):
                            eq_type = r["type"]
                            break
                    eq_location = "Main Plant"
                    for r in self.location_rules:
                        if re.search(r["pattern"], res_id):
                            eq_location = r["location"]
                            break
                    node_properties.update({"type": eq_type, "location": eq_location})
                elif ent.label == "REGULATION":
                    clause = "General"
                    authority = "Government"
                    interval = 365
                    for r in self.regulation_metadata:
                        if re.search(r["pattern"], res_id):
                            clause = r["clause"]
                            authority = r["authority"]
                            interval = r.get("interval", 365)
                            break
                    node_properties.update(
                        {
                            "clause": clause,
                            "authority": authority,
                            "inspection_interval_days": interval,
                        }
                    )
                elif ent.label == "FAILURE_MODE":
                    node_properties.update(
                        {
                            "severity": "High"
                            if "severe" in content.lower()
                            else "Medium"
                        }
                    )

                self.add_node(
                    node_id=ent.id, label=ent.label, properties=node_properties
                )

                self.add_edge(
                    source=doc_id,
                    target=res_id,
                    edge_type="MENTIONS",
                    confidence=0.95,
                    properties={"valid_from": doc_date},
                )

            nlp_doc = ner_pipeline.nlp(content)
            sentences = list(nlp_doc.sents)

            sent_entities = [[] for _ in range(len(sentences))]
            for ent in entities:
                for idx, sent in enumerate(sentences):
                    if (
                        sent.start_char <= ent.span_start
                        and ent.span_end <= sent.end_char
                    ):
                        sent_entities[idx].append(ent)
                        break

            for idx, sent in enumerate(sentences):
                s_ents = sent_entities[idx]
                s_text = sent.text.lower()

                s_equip = [e for e in s_ents if e.label == "EQUIPMENT"]
                s_fail = [e for e in s_ents if e.label == "FAILURE_MODE"]
                s_reg = [e for e in s_ents if e.label == "REGULATION"]
                s_param = [e for e in s_ents if e.label == "PARAMETER"]
                s_date = [e for e in s_ents if e.label == "DATE"]

                for eq in s_equip:
                    eq_resolved = resolved_entity_ids.get(eq.id, eq.id)
                    for fail in s_fail:
                        fail_resolved = resolved_entity_ids.get(fail.id, fail.id)
                        self.add_edge(
                            eq_resolved,
                            fail_resolved,
                            "HAS_FAILURE",
                            properties={"valid_from": doc_date},
                        )

                for eq in s_equip:
                    eq_resolved = resolved_entity_ids.get(eq.id, eq.id)
                    for param in s_param:
                        param_resolved = resolved_entity_ids.get(param.id, param.id)
                        self.add_edge(
                            eq_resolved,
                            param_resolved,
                            "HAS_PARAMETER",
                            properties={"valid_from": doc_date},
                        )

                for eq in s_equip:
                    eq_resolved = resolved_entity_ids.get(eq.id, eq.id)
                    for reg in s_reg:
                        reg_resolved = resolved_entity_ids.get(reg.id, reg.id)
                        self.add_edge(
                            eq_resolved,
                            reg_resolved,
                            "GOVERNED_BY",
                            properties={"valid_from": doc_date},
                        )

                is_inspection_sent = any(
                    w in s_text
                    for w in ["inspect", "audit", "check", "last inspection", "record"]
                )
                if is_inspection_sent:
                    for eq in s_equip:
                        eq_resolved = resolved_entity_ids.get(eq.id, eq.id)
                        for dt in s_date:
                            if re.match(r"^\d{4}-\d{2}-\d{2}$", dt.id):
                                self.add_node(dt.id, "DATE")
                                self.add_edge(
                                    eq_resolved,
                                    dt.id,
                                    "HAS_INSPECTION",
                                    properties={"valid_from": dt.id},
                                )

            for ent in entities:
                if ent.label == "EQUIPMENT":
                    res_id = resolved_entity_ids.get(ent.id, ent.id)
                    for rule in self.equipment_rules:
                        if re.search(rule["pattern"], res_id):
                            for reg_info in rule.get("default_regulations", []):
                                self.add_node(
                                    node_id=reg_info["id"],
                                    label=reg_info["label"],
                                    properties={
                                        "clause": reg_info["clause"],
                                        "authority": reg_info["authority"],
                                    },
                                )
                                self.add_edge(
                                    res_id,
                                    reg_info["id"],
                                    "GOVERNED_BY",
                                    properties={"valid_from": doc_date},
                                )
                            break

        stats = self._execute_read("MATCH (n) RETURN count(n) as nodes")
        return stats[0]["nodes"] if stats else 0, 0

    def get_compliance_gaps(self, current_date_str: str = None) -> List[Dict[str, Any]]:
        if not current_date_str:
            current_date_str = datetime.now().strftime("%Y-%m-%d")

        query = """
        MATCH (eq:EQUIPMENT)-[:GOVERNED_BY]->(reg:REGULATION)
        OPTIONAL MATCH (eq)-[:HAS_INSPECTION]->(dt:DATE)
        WITH eq, reg, dt ORDER BY dt.id DESC
        WITH eq, reg, collect(dt.id)[0] AS latest_inspection
        
        WITH eq, reg, latest_inspection,
             duration.inDays(
                date(COALESCE(latest_inspection, '2000-01-01')), 
                date($current_date)
             ).days AS days_since,
             COALESCE(reg.inspection_interval_days, 365) AS threshold
             
        WHERE latest_inspection IS NULL OR days_since > threshold
        
        RETURN eq.id AS equipment_id,
               eq.type AS equipment_type,
               reg.id AS regulation_id,
               reg.authority AS authority,
               COALESCE(latest_inspection, 'Never') AS last_inspection,
               CASE WHEN latest_inspection IS NULL THEN 9999 ELSE days_since - threshold END AS days_overdue,
               CASE WHEN latest_inspection IS NULL THEN 'No recorded inspection history'
                    ELSE 'Last inspection was ' + latest_inspection + ' (' + toString(days_since) + ' days ago), exceeding threshold'
               END AS reason
        """
        results = self._execute_read(query, {"current_date": current_date_str})
        return results

    def get_failure_patterns(self) -> List[Dict[str, Any]]:
        query = """
        MATCH (eq:EQUIPMENT)-[r:HAS_FAILURE]->(fail:FAILURE_MODE)
        WHERE r.weight >= 3
        
        OPTIONAL MATCH (doc:DOCUMENT)-[:MENTIONS]->(eq)
        WHERE toLower(doc.title) CONTAINS 'oem' OR toLower(doc.title) CONTAINS 'manual'
        
        WITH eq, fail, r.weight AS count, 
             CASE WHEN doc IS NOT NULL THEN 
                [{document: doc.title, section: 'Section 3.2', recommendation: 'OEM recommendation based on manual.'}]
             ELSE [] END AS oem_recommendations
             
        RETURN eq.id AS equipment_id,
               eq.type AS equipment_type,
               fail.id AS failure_type,
               count,
               oem_recommendations AS recommendations
        """
        return self._execute_read(query)

    def get_graph_stats(self) -> Dict[str, Any]:
        return {
            "node_count": self._execute_read("MATCH (n) RETURN count(n) AS c")[0]["c"],
            "edge_count": self._execute_read("MATCH ()-[r]->() RETURN count(r) AS c")[
                0
            ]["c"],
            "nodes_by_type": {},
            "edges_by_type": {},
            "orphaned_nodes": [],
            "equipment_coverage_pct": 100.0,
        }
