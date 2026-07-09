"""
Phase 5: Enterprise Scalability (Neo4j Exporter)
This script demonstrates the capability to migrate the in-memory NetworkX graph
to an enterprise-grade Neo4j database, proving the architecture scales beyond the hackathon.
"""

import os
import json
import networkx as nx

GRAPH_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "graph.json")
)


def export_to_neo4j_cypher(graph_file_path=GRAPH_FILE):
    print("Initializing Neo4j Enterprise Exporter...")

    if not os.path.exists(graph_file_path):
        print(f"Error: Could not find graph file at {graph_file_path}")
        return

    # Read the networkx graph
    try:
        with open(graph_file_path, "r") as f:
            data = json.load(f)
        G = nx.node_link_graph(data)
    except Exception as e:
        print(f"Failed to load graph: {e}")
        return

    cypher_queries = []

    # 1. Export Nodes
    print(f"Exporting {G.number_of_nodes()} nodes...")
    for node, attrs in G.nodes(data=True):
        label = attrs.get("label", "Entity")

        # Clean attributes for cypher injection
        props = []
        for k, v in attrs.items():
            if k == "label":
                continue
            if isinstance(v, str):
                safe_val = v.replace('"', "'")
                props.append(f'{k}: "{safe_val}"')
            else:
                props.append(f"{k}: {v}")

        # Add the ID itself as a property
        safe_id = str(node).replace('"', "'")
        props.append(f'id: "{safe_id}"')

        props_str = ", ".join(props)
        cypher = f"MERGE (n:{label} {{{props_str}}});"
        cypher_queries.append(cypher)

    # 2. Export Edges
    print(f"Exporting {G.number_of_edges()} edges...")
    for u, v, attrs in G.edges(data=True):
        rel_type = attrs.get("type", "RELATED_TO").upper().replace(" ", "_")

        props = []
        for k, val in attrs.items():
            if k == "type":
                continue
            if isinstance(val, str):
                safe_val = val.replace('"', "'")
                props.append(f'{k}: "{safe_val}"')
            else:
                props.append(f"{k}: {val}")

        props_str = f" {{{', '.join(props)}}}" if props else ""

        # Cypher MATCH and MERGE
        safe_u = str(u).replace('"', "'")
        safe_v = str(v).replace('"', "'")

        cypher = f"""MATCH (a {{id: "{safe_u}"}}), (b {{id: "{safe_v}"}}) 
MERGE (a)-[r:{rel_type}{props_str}]->(b);"""
        cypher_queries.append(cypher.replace("\n", " "))

    # 3. Write to file
    out_file = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "neo4j_migration.cypher"
        )
    )
    with open(out_file, "w") as f:
        f.write("\n".join(cypher_queries))

    print(f"\nMigration successful! Generated {len(cypher_queries)} Cypher statements.")
    print(f"Output saved to: {out_file}")
    print("\nTo deploy to enterprise Neo4j:")
    print("$ cat data/neo4j_migration.cypher | cypher-shell -u neo4j -p secret")


if __name__ == "__main__":
    export_to_neo4j_cypher()
