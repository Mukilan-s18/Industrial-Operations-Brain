# Person 2: Knowledge Graph & Entity Extraction (Micro-Task Level)

**Role Overview:**
You are the Knowledge Graph Lead. You use spaCy, networkx/Neo4j, and BERT to perform entity resolution and build the structured graph backbone of the Copilot.

---

## Daily Schedule with Micro-Tasks

### Day 1: Foundation (Graph schema + ontology design)
*   **Design industrial entity schema: Equipment, Document, Parameter, Person, Regulation, FailureMode**
    *   *Micro-tasks:* Define properties for each node. Equipment needs `id`, `type`, `location`. Regulation needs `clause`, `authority`.
*   **Choose networkx for demo (Neo4j optional)**
    *   *Micro-tasks:* Setup `networkx` `MultiDiGraph` (to allow multiple edges between same nodes). If using Neo4j, set up local Docker container and connect via `neo4j-driver`.
*   **Create entity JSON schema spec**
    *   *Micro-tasks:* Write a Pydantic model for the exact JSON format you expect from Person 1.
*   **Write first NER test with spaCy**
    *   *Micro-tasks:* Install `spacy`. Download `en_core_web_sm` (or `trf` for better accuracy). Write a dummy string and run `.ents`.
*   **Output:** Entity schema document + NER stub

### Day 2: Foundation (NER pipeline + entity extraction)
*   **Fine-tune spaCy NER on industrial tags: EQUIPMENT, PARAMETER, REGULATION, PERSON, DATE, FAILURE_MODE**
    *   *Micro-tasks:* Use spaCy `EntityRuler` to add hardcoded regex patterns for things like Equipment Tags (e.g., `[A-Z]{2,3}-\d{3,4}`). This is faster and more reliable than fine-tuning a transformer model in a hackathon.
*   **Run on extracted text from Person A**
    *   *Micro-tasks:* Build a processing loop that iterates over Person 1's JSON chunks.
*   **Output entity list with spans and types**
    *   *Micro-tasks:* Store start/end character offsets for highlighting in the UI later.
*   **Test alias detection: "P-101" vs "Pump P101"**
    *   *Micro-tasks:* Write unit tests covering 5 different ways a technician might write "P-101".
*   **Output:** NER pipeline extracting entities

### Day 3: Foundation (Knowledge graph builder)
*   **Build graph from NER output: nodes = entities, edges = co-occurrence + relationship**
    *   *Micro-tasks:* If Entity A and Entity B appear in the same sentence, create an edge `CO_OCCURS_WITH`. If a failure is mentioned near equipment, create `HAS_FAILURE`.
*   **Add temporal edges: `valid_from`, `valid_to`**
    *   *Micro-tasks:* Default `valid_to` to `9999-12-31`. Extract dates from the document metadata to populate `valid_from`.
*   **Add confidence score to each edge**
    *   *Micro-tasks:* Give rule-based extractions (regex) 0.95 confidence. Give statistical NLP extractions 0.70 confidence.
*   **Implement basic alias resolver (rapidfuzz)**
    *   *Micro-tasks:* Install `rapidfuzz`. When adding a new node, calculate `fuzz.ratio` against existing nodes. If > 90%, merge them.
*   **Output:** Populated knowledge graph (networkx)

### Day 4: Core Features (Regulatory entity mapping)
*   **Add OISD-118, PESO, Factory Act clauses as graph nodes**
    *   *Micro-tasks:* Manually curate a CSV of 10-15 key regulations for the demo. Load them directly into the graph as ground truth nodes.
*   **Map equipment -> applicable regulations via graph edges**
    *   *Micro-tasks:* Create `GOVERNED_BY` edges. E.g., Pump P-101 is GOVERNED_BY OISD-118.
*   **Build "compliance gap" query: equipment with missing inspection records**
    *   *Micro-tasks:* Write a Cypher query (or NetworkX path traversal) to find Equipment nodes that have a `GOVERNED_BY` edge to a Regulation, but lack a `HAS_INSPECTION` edge within the last 365 days.
*   **Output:** Gap list with equipment + missing regulation (Compliance gap detection via graph)

### Day 5: Core Features (Failure pattern analysis)
*   **Graph query: find equipment with 3+ failures of same type**
    *   *Micro-tasks:* Query nodes of type `Equipment` connected to >3 nodes of type `FailureMode` where `type == "Seal Leak"`.
*   **Link failure records -> OEM manual sections (via equipment entity)**
    *   *Micro-tasks:* Create paths: `FailureMode` -> `Equipment` -> `Document (OEM Manual)`.
*   **Output: "Pump P-101 has 4 seal failures — OEM section 3.2 recommends annual replacement"**
    *   *Micro-tasks:* Structure this output cleanly as a JSON object so Person 3's RCA agent can consume it.
*   **Add failure frequency edge weights to graph**
    *   *Micro-tasks:* Instead of 4 separate edges, create 1 edge with `weight=4`.
*   **Output:** Failure pattern query working

### Day 6: Full integration test + bug bash (Graph quality checks)
*   **Run orphaned node detection — flag entities with no edges**
    *   *Micro-tasks:* In NetworkX: `list(nx.isolates(G))`. Delete or review them.
*   **Check alias resolution accuracy on full corpus**
    *   *Micro-tasks:* Print all merged nodes. Verify that `P-101` didn't accidentally merge with `P-102`.
*   **Add graph statistics endpoint: node count, edge count, coverage %**
    *   *Micro-tasks:* Create a FastAPI endpoint `/graph/stats` that returns `{'nodes': len(G.nodes), 'edges': len(G.edges)}`.
*   **Fix top 3 NER false positives**
    *   *Micro-tasks:* Add negative lookarounds to your regex rules to stop extracting things like "Page 3" as equipment.
*   **Output:** Graph health metrics dashboard

### Day 7: P1 bug fixes + demo corpus finalisation (Entity resolution improvements)
*   **Fix false positive merges from alias resolver**
    *   *Micro-tasks:* Increase `rapidfuzz` threshold from 85 to 92 to be safer.
*   **Add manual override: "these two tags are NOT the same entity"**
    *   *Micro-tasks:* Implement a blocklist dictionary for alias resolution (e.g., `{"Pump A": ["Pump B"]}`).
*   **Improve regulation-to-equipment mapping recall**
    *   *Micro-tasks:* Add fuzzy matching for regulation names (e.g., "OISD 118" vs "OISD-118").
*   **Run final graph on all 5 docs — verify edge counts**
    *   *Micro-tasks:* Freeze the graph data state. Save the NetworkX graph to a `.gpickle` or JSON file.
*   **Output:** Entity graph accurate on demo corpus

### Day 8: Demo video recording + presentation polish (Knowledge graph visualisation)
*   **Add networkx -> pyvis graph visualization endpoint**
    *   *Micro-tasks:* Install `pyvis`. Write a function to convert the networkx graph to a PyVis HTML file. Customize node colors (Equipment=Blue, Regulation=Red).
*   **Show in UI: click equipment -> see all connected documents, regulations, failures**
    *   *Micro-tasks:* Configure PyVis to enable physics/interaction, but cap it so it doesn't lag.
*   **Add graph stats card: X entities, Y documents linked, Z compliance gaps found**
    *   *Micro-tasks:* Format these numbers for Person 4's UI dashboard.
*   **This is a visual showstopper for judges**
    *   *Micro-tasks:* Ensure the graph isn't a "hairball". Filter it to show only ego-networks (1-hop neighbors) around key nodes during the demo.
*   **Output:** Interactive graph viz in UI

### Day 9: Hardening + judge Q&A prep (Graph + NER accuracy report)
*   **Generate entity extraction accuracy report (precision/recall on 10 labeled entities)**
    *   *Micro-tasks:* Create a mini-spreadsheet of 10 sentences with hand-labeled ground truth. Run your NER pipeline and calculate F1 score. 
*   **Document: what the knowledge graph knows about each demo equipment**
    *   *Micro-tasks:* Create a cheat sheet for the presenter (Person 4) detailing exactly what queries will yield rich graph responses.
*   **Prepare "graph depth" talking point for judges**
    *   *Micro-tasks:* Draft 2 sentences explaining why graph reasoning beats pure vector search for structured industrial data.
*   **Add quick-look graph summary to UI**
    *   *Micro-tasks:* Expose the top 5 most connected nodes via API.
*   **Output:** Accuracy metrics card in UI

### Day 10: Final submission + presentation day (Documentation)
*   **Write 1-page technical architecture summary**
    *   *Micro-tasks:* Detail the NER pipeline (spaCy + regex), the graph DB (NetworkX), and the entity resolution algorithm.
*   **Document knowledge graph schema**
    *   *Micro-tasks:* Export a Mermaid.js ER diagram of the Node and Edge types.
*   **Write 3-sentence description of India-specific differentiation**
    *   *Micro-tasks:* Emphasize the OISD and PESO regulatory nodes explicitly mapped to equipment.
*   **Add to presentation appendix**
    *   *Micro-tasks:* Send docs to Person 4.
*   **Output:** Technical documentation complete
