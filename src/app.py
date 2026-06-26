import os
import json
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pyvis.network import Network
from pydantic import BaseModel
from src.ner_pipeline import NERPipeline
from src.graph_builder import KnowledgeGraphBuilder
from src.rag_agent import RagAgent

app = FastAPI(title="Industrial Copilot - Knowledge Graph API")

# Initialize and build graph on startup
ner = NERPipeline()
builder = KnowledgeGraphBuilder()
rag_agent = RagAgent(builder)

class QueryRequest(BaseModel):
    query: str
    role: str

@app.post("/query")
def process_query(req: QueryRequest):
    return rag_agent.query(req.query, req.role)

# Load mock documents and build graph
DOCS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "documents.json")
if os.path.exists(DOCS_PATH):
    with open(DOCS_PATH, "r") as f:
        docs = json.load(f)
    builder.build_graph_from_extracted_data(docs, ner)
else:
    docs = []

# Serve static files (HTML, CSS, JS)
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/api/stats")
def get_stats():
    return builder.get_graph_stats()

@app.get("/api/compliance-gaps")
def get_compliance_gaps(date: str = "2025-09-01"):
    return builder.get_compliance_gaps(date)

@app.get("/api/failure-patterns")
def get_failure_patterns():
    return builder.get_failure_patterns()

@app.get("/api/nodes")
def get_nodes():
    nodes_list = []
    for node_id, data in builder.G.nodes(data=True):
        nodes_list.append({
            "id": node_id,
            "label": data.get("label", "UNKNOWN"),
            "properties": {k: v for k, v in data.items() if k != "label"}
        })
    return nodes_list

@app.get("/api/edges")
def get_edges():
    edges_list = []
    for u, v, data in builder.G.edges(data=True):
        edges_list.append({
            "source": u,
            "target": v,
            "type": data.get("type", "UNKNOWN"),
            "confidence": data.get("confidence", 1.0),
            "weight": data.get("weight", 1),
            "properties": {k: v for k, v in data.items() if k not in ["type", "confidence", "weight"]}
        })
    return edges_list

@app.get("/api/graph-viz", response_class=HTMLResponse)
def get_graph_viz(node_id: str = Query(None, description="Ego network center node")):
    """
    Generates a PyVis interactive visualization of the graph.
    If node_id is provided, generates the 1-hop ego network for that node.
    """
    # Color scheme for different entity types
    colors = {
        "EQUIPMENT": "#3B82F6",    # Vibrant Blue
        "REGULATION": "#EF4444",   # Vivid Ruby Red
        "FAILURE_MODE": "#F59E0B", # Warm Amber
        "PARAMETER": "#10B981",    # Emerald Green
        "PERSON": "#8B5CF6",       # Deep Violet
        "DOCUMENT": "#06B6D4",     # Cool Cyan
        "DATE": "#6B7280"          # Slate Grey
    }

    # Decide which sub-graph to render
    if node_id:
        if not builder.G.has_node(node_id):
            raise HTTPException(status_code=404, detail="Node not found")
        # Extract ego network (neighbors and edges between neighbors)
        ego_nodes = [node_id] + list(builder.G.successors(node_id)) + list(builder.G.predecessors(node_id))
        sub_g = builder.G.subgraph(ego_nodes)
        title = f"Ego Network - {node_id}"
    else:
        sub_g = builder.G
        title = "Plant Knowledge Graph"

    # Create PyVis Network
    net = Network(
        height="500px", 
        width="100%", 
        bgcolor="#0F172A", # Deep slate background
        font_color="#E2E8F0", # Slate 200 text
        directed=True,
        notebook=False
    )
    
    # Enable physics options to make it interactive and not a "hairball"
    net.set_options("""
    {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "shadow": true,
        "shape": "dot",
        "size": 25,
        "font": {
          "size": 14,
          "face": "Inter, Roboto, sans-serif"
        }
      },
      "edges": {
        "color": {
          "color": "#475569",
          "highlight": "#60A5FA",
          "hover": "#60A5FA",
          "inherit": false
        },
        "smooth": {
          "type": "cubicBezier",
          "forceDirection": "vertical",
          "roundness": 0.5
        },
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.5
          }
        }
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -12000,
          "centralGravity": 0.3,
          "springLength": 120,
          "springConstant": 0.04,
          "damping": 0.09,
          "avoidOverlap": 0.8
        },
        "minVelocity": 0.75
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100
      }
    }
    """)

    # Add nodes to PyVis
    for n, data in sub_g.nodes(data=True):
        label_type = data.get("label", "UNKNOWN")
        color = colors.get(label_type, "#94A3B8")
        
        # Build clean tooltip HTML
        properties_html = "<br>".join([f"<b>{k}:</b> {v}" for k, v in data.items() if k != "label"])
        tooltip = f"<b>{n}</b> ({label_type})<br>{properties_html}"
        
        # Distinguish source node visually in ego-network view
        is_center = node_id and n == node_id
        size = 35 if is_center else 20 if label_type == "DOCUMENT" else 25
        
        net.add_node(
            n, 
            label=n, 
            title=tooltip, 
            color=color, 
            size=size,
            borderWidth=4 if is_center else 2,
            borderWidthSelected=6 if is_center else 4
        )

    # Add edges to PyVis
    for u, v, data in sub_g.edges(data=True):
        edge_type = data.get("type", "UNKNOWN")
        weight = data.get("weight", 1)
        confidence = data.get("confidence", 1.0)
        
        tooltip = f"<b>Relation:</b> {edge_type}<br><b>Weight:</b> {weight}<br><b>Confidence:</b> {confidence}"
        # Set thicker lines for heavier relations
        width = 1 + (weight - 1) * 1.5
        
        # Color edges by relation type
        edge_color = "#3B82F6" if edge_type == "HAS_FAILURE" else "#10B981" if edge_type == "HAS_INSPECTION" else "#EF4444" if edge_type == "GOVERNED_BY" else "#475569"
        
        net.add_edge(
            u, 
            v, 
            title=tooltip, 
            value=weight, 
            width=width,
            color=edge_color
        )

    # Write HTML file and read it to return
    # Use static directory so it's clean and served safely
    temp_file = os.path.join(static_dir, f"temp_graph_{node_id or 'all'}.html")
    net.write_html(temp_file)
    
    with open(temp_file, "r") as f:
        html_content = f.read()
        
    # Clean up temp file
    try:
        os.remove(temp_file)
    except OSError:
        pass
        
    return html_content
