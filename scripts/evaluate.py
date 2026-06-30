"""
Day 6: RAG Evaluation Benchmark
Loads questions from data/questions.json, runs them through the full LangGraph pipeline,
measures answer accuracy, citation accuracy, and latency, outputs to results_day6.csv.
"""
import time
import csv
import json
import os
import sys

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8")

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from backend.src.agent import build_rca_graph


def load_questions(path: str) -> list[dict]:
    """Load benchmark questions from data/questions.json"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_citation_accuracy(answer: str) -> bool:
    """Check if the answer contains properly formatted citations like [doc_name, Rev X]."""
    import re
    # Match patterns like [sop_101.txt, Rev 4] or [wo_998.txt, Rev 1]
    citation_pattern = r'\[[\w\.\-]+,\s*Rev\s*\w+\]'
    citations = re.findall(citation_pattern, answer)
    return len(citations) > 0


def run_evaluation():
    # Locate questions.json
    questions_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "questions.json"))
    if not os.path.exists(questions_path):
        print(f"[ERROR] {questions_path} not found!")
        sys.exit(1)

    questions = load_questions(questions_path)
    print(f"Loaded {len(questions)} benchmark questions from {questions_path}\n")

    graph = build_rca_graph()
    results = []
    pass_count = 0
    citation_pass_count = 0
    total_latency = 0.0

    print("=" * 70)
    print("DAY 6: RAG EVALUATION BENCHMARK")
    print("=" * 70)

    for item in questions:
        qid = item.get("id", "?")
        query = item["query"]
        expected = item["expected_contains"]
        category = item.get("category", "unknown")

        print(f"\n[Q{qid}] ({category}) {query}")

        start_time = time.time()
        try:
            final_state = graph.invoke({"original_query": query, "query": ""})
            latency = time.time() - start_time

            answer = final_state.get("final_answer", "")
            faithfulness = final_state.get("faithfulness_score", 0.0)
            contradiction = final_state.get("contradiction_detected", False)
            sources = final_state.get("sources", [])

            # Accuracy: does the answer contain the expected substring?
            answer_passed = expected.lower() in answer.lower()
            # Citation accuracy: does the answer have proper [Doc, Rev X] citations?
            citation_passed = check_citation_accuracy(answer)

            if answer_passed:
                pass_count += 1
            if citation_passed:
                citation_pass_count += 1
            total_latency += latency

            print(f"  Latency:       {latency:.2f}s")
            print(f"  Answer Pass:   {'✅' if answer_passed else '❌'} (expected '{expected}')")
            print(f"  Citation Pass: {'✅' if citation_passed else '❌'}")
            print(f"  Faithfulness:  {faithfulness:.3f}")
            print(f"  Contradiction: {contradiction}")
            print(f"  Sources:       {len(sources)} chunks used")
            print(f"  Answer:        {answer[:200]}...")

            results.append({
                "id": qid,
                "query": query,
                "category": category,
                "expected": expected,
                "answer_pass": answer_passed,
                "citation_pass": citation_passed,
                "faithfulness_score": faithfulness,
                "contradiction_detected": contradiction,
                "num_sources": len(sources),
                "latency_sec": round(latency, 2),
                "answer": answer[:500]  # Truncate for CSV readability
            })

        except Exception as e:
            latency = time.time() - start_time
            print(f"  ❌ ERROR: {e}")
            results.append({
                "id": qid,
                "query": query,
                "category": category,
                "expected": expected,
                "answer_pass": False,
                "citation_pass": False,
                "faithfulness_score": 0.0,
                "contradiction_detected": False,
                "num_sources": 0,
                "latency_sec": round(latency, 2),
                "answer": f"ERROR: {str(e)[:200]}"
            })

    # Write results to CSV
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results_day6.csv"))
    fieldnames = [
        "id", "query", "category", "expected", "answer_pass", "citation_pass",
        "faithfulness_score", "contradiction_detected", "num_sources", "latency_sec", "answer"
    ]
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Summary
    total = len(questions)
    avg_latency = total_latency / total if total > 0 else 0

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"  Total Questions:      {total}")
    print(f"  Answer Accuracy:      {pass_count}/{total} ({pass_count/total*100:.0f}%)")
    print(f"  Citation Accuracy:    {citation_pass_count}/{total} ({citation_pass_count/total*100:.0f}%)")
    print(f"  Avg Latency:          {avg_latency:.2f}s")
    print(f"  Target (>80%):        {'✅ PASS' if pass_count/total >= 0.8 else '❌ FAIL'}")
    print(f"  Results saved to:     {csv_path}")
    print("=" * 70)


if __name__ == "__main__":
    run_evaluation()
