import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from frontend.api import builder, ner, get_graph_viz


def render():
    st.markdown(
        "<div class='clean-card'><h3>Knowledge Graph Explorer</h3><p style='font-size: 0.95em; color: #94A3B8;'>Explore plant asset relationships, compliance constraints, and failure modes interactively.</p></div>",
        unsafe_allow_html=True,
    )

    # Graph stats cards
    stats = builder.get_graph_stats()
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Total Entities (Nodes)", stats["node_count"])
    with col_stat2:
        st.metric("Total Relationships (Edges)", stats["edge_count"])
    with col_stat3:
        st.metric(
            "Equipment Compliance Coverage", f"{stats['equipment_coverage_pct']}%"
        )

    st.write("---")

    # Ego network visualization control
    col_viz_ctrl1, col_viz_ctrl2 = st.columns([1, 2])
    with col_viz_ctrl1:
        st.subheader("Graph Visualization Controls")
        st.write(
            "Select a node to view its local 1-hop ego network, or select 'All Nodes' for the global overview."
        )

        # Sort nodes alphabetically
        node_options = ["All Nodes"] + sorted(list(builder.G.nodes))
        selected_node = st.selectbox("Focus Asset Node", options=node_options)

        # Node Type Breakdown
        st.write(" ")
        st.write("**Entity Type Breakdown:**")
        for lbl, count in stats["nodes_by_type"].items():
            st.markdown(f"- **{lbl}**: {count}")

    with col_viz_ctrl2:
        # Load and render PyVis graph
        viz_node_id = None if selected_node == "All Nodes" else selected_node
        with st.spinner("Generating interactive visualization..."):
            html_content = get_graph_viz(viz_node_id, st.session_state.role)

        # Render the PyVis interactive graph
        components.html(html_content, height=520, scrolling=False)

    st.write("---")

    # NER Accuracy Metrics Report
    st.subheader("Model Accuracy & Quality Control (NER)")
    st.write(
        "The F1 score is evaluated against 10 annotated heavy-industry sentences covering equipment, regulations, failure modes, parameters, and dates."
    )

    with st.spinner("Evaluating NER accuracy metrics..."):
        eval_report = ner.evaluate_accuracy()

    col_acc1, col_acc2, col_acc3 = st.columns(3)
    with col_acc1:
        st.metric("NER F1 Score", f"{eval_report['f1_score'] * 100:.2f}%")
    with col_acc2:
        st.metric("Precision", f"{eval_report['precision'] * 100:.2f}%")
    with col_acc3:
        st.metric("Recall", f"{eval_report['recall'] * 100:.2f}%")

    with st.expander("Show Labeled Evaluation Corpus & Predictions"):
        # Format the predictions comparison
        eval_details = []
        for det in eval_report["details"]:
            gt_str = (
                ", ".join([f"{e['text']} ({e['label']})" for e in det["ground_truth"]])
                or "None"
            )
            ext_str = (
                ", ".join([f"{e['text']} ({e['label']})" for e in det["extracted"]])
                or "None"
            )
            eval_details.append(
                {
                    "Sentence": det["sentence"],
                    "Ground Truth Entities": gt_str,
                    "Extracted Entities": ext_str,
                }
            )
        st.dataframe(pd.DataFrame(eval_details), use_container_width=True)

    st.write("---")

    # Schema & Architecture Documentation
    st.subheader("Technical Architecture & Schema Spec")

    tab_doc1, tab_doc2 = st.tabs(
        ["1-Page Architecture Summary", "Mermaid.js ER Diagram"]
    )
    with tab_doc1:
        # Need to fix the path for architecture since we're in tabs dir
        arch_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "architecture",
            "technical_architecture.md",
        )
        if os.path.exists(arch_path):
            with open(arch_path, "r") as f:
                arch_text = f.read()
            st.markdown(arch_text)
        else:
            st.warning("Architecture summary document not found.")

    with tab_doc2:
        st.write(
            "This diagram specifies the entity-relationship ontology of our heavy-industry graph schema."
        )
        # Mermaid code
        er_code = """erDiagram
    DOCUMENT ||--o{ PERSON : "AUTHORED BY"
    DOCUMENT ||--o{ EQUIPMENT : "MENTIONS"
    DOCUMENT ||--o{ REGULATION : "MENTIONS"
    EQUIPMENT ||--o{ "FAILURE_MODE" : "HAS FAILURE"
    EQUIPMENT ||--o{ REGULATION : "GOVERNED BY"
    EQUIPMENT ||--o{ PARAMETER : "HAS PARAMETER"
    EQUIPMENT ||--o{ DATE : "HAS INSPECTION"
        """

        # Render Mermaid using browser-based compiler in iframe
        components.html(
            f"""
            <div style="background-color: #1F1F1F; padding: 20px; border-radius: 8px; display: flex; justify-content: center; align-items: center; border: 1px dashed #333333;">
                <pre class="mermaid" style="margin: 0; color: #F8FAFC;">
                {er_code}
                </pre>
            </div>
            <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true, theme: 'dark', securityLevel: 'loose' }});
            </script>
            """,
            height=300,
            scrolling=True,
        )
