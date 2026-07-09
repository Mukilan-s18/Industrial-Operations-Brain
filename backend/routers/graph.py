import os
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import HTMLResponse

from backend.settings import settings
from backend.dependencies import builder
from pyvis.network import Network

router = APIRouter()


@router.get("/api/stats")
def get_stats():
    return builder.get_graph_stats()


@router.get("/api/nodes")
def get_nodes():
    nodes_list = []
    for node_id, data in builder.G.nodes(data=True):
        nodes_list.append(
            {
                "id": node_id,
                "label": data.get("label", "UNKNOWN"),
                "properties": {k: v for k, v in data.items() if k != "label"},
            }
        )
    return nodes_list


@router.get("/api/edges")
def get_edges():
    edges_list = []
    for u, v, data in builder.G.edges(data=True):
        edges_list.append(
            {
                "source": u,
                "target": v,
                "type": data.get("type", "UNKNOWN"),
                "confidence": data.get("confidence", 1.0),
                "weight": data.get("weight", 1),
                "properties": {
                    k: v
                    for k, v in data.items()
                    if k not in ["type", "confidence", "weight"]
                },
            }
        )
    return edges_list


@router.get("/api/graph-viz", response_class=HTMLResponse)
def get_graph_viz(
    node_id: str = Query(None, description="Ego network center node"),
    role: str = Query(None, description="User Role"),
):
    colors = {
        "EQUIPMENT": "#3B82F6",
        "REGULATION": "#EF4444",
        "FAILURE_MODE": "#F59E0B",
        "PARAMETER": "#10B981",
        "PERSON": "#8B5CF6",
        "DOCUMENT": "#06B6D4",
        "DATE": "#6B7280",
    }

    if node_id:
        if not builder.G.has_node(node_id):
            raise HTTPException(status_code=404, detail="Node not found")
        ego_nodes = (
            [node_id]
            + list(builder.G.successors(node_id))
            + list(builder.G.predecessors(node_id))
        )
        sub_g = builder.G.subgraph(ego_nodes).copy()
    else:
        sub_g = builder.G.copy()

    if role and "Operator" in role:
        restricted_nodes = [
            n for n, d in sub_g.nodes(data=True) if d.get("label") == "REGULATION"
        ]
        sub_g.remove_nodes_from(restricted_nodes)

    net = Network(
        height="500px",
        width="100%",
        bgcolor="#0F172A",
        font_color="#E2E8F0",
        directed=True,
        notebook=False,
    )

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

    for n, data in sub_g.nodes(data=True):
        label_type = data.get("label", "UNKNOWN")
        color = colors.get(label_type, "#94A3B8")

        properties_html = "<br>".join(
            [f"<b>{k}:</b> {v}" for k, v in data.items() if k != "label"]
        )
        tooltip = f"<b>{n}</b> ({label_type})<br>{properties_html}"

        is_center = node_id and n == node_id
        size = 35 if is_center else 20 if label_type == "DOCUMENT" else 25

        net.add_node(
            n,
            label=n,
            title=tooltip,
            color=color,
            size=size,
            borderWidth=4 if is_center else 2,
            borderWidthSelected=6 if is_center else 4,
        )

    for u, v, data in sub_g.edges(data=True):
        edge_type = data.get("type", "UNKNOWN")
        weight = data.get("weight", 1)
        confidence = data.get("confidence", 1.0)

        tooltip = f"<b>Relation:</b> {edge_type}<br><b>Weight:</b> {weight}<br><b>Confidence:</b> {confidence}"
        width = 1 + (weight - 1) * 1.5

        edge_color = (
            "#3B82F6"
            if edge_type == "HAS_FAILURE"
            else "#10B981"
            if edge_type == "HAS_INSPECTION"
            else "#EF4444"
            if edge_type == "GOVERNED_BY"
            else "#475569"
        )

        net.add_edge(u, v, title=tooltip, value=weight, width=width, color=edge_color)

    temp_file = os.path.join(settings.static_dir, f"temp_graph_{node_id or 'all'}.html")
    net.write_html(temp_file)

    with open(temp_file, "r") as f:
        html_content = f.read()

    try:
        os.remove(temp_file)
    except OSError:
        pass

    return html_content
