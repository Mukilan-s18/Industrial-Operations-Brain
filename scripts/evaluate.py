"""
Day 6: RAG Evaluation Run
Runs benchmark questions against the full corpus and measures accuracy and latency.
"""
import time
import csv
import json
import os
from src.agent import build_rca_graph

# Mock questions dataset (since questions.json was missing)
QUESTIONS = [
    {"q": "What is the pressure limit for HV-204?", "expected": "120 PSI"},
    {"q": "failures related to p-101", "expected": "Seal Leak"},
    {"q": "What is the torque specification for P-101 housing bolts?", "expected": "45 Nm"}
]

def run_evaluation():
    graph = build_rca_graph()
    results = []
    
    print("Starting Day 6 Evaluation Benchmark...")
    for item in QUESTIONS:
        query = item['q']
        print(f"\nEvaluating: '{query}'")
        
        start_time = time.time()
        final_state = graph.invoke({"original_query": query, "query": ""})
        latency = time.time() - start_time
        
        answer = final_state.get("final_answer", "")
        
        # Simple string-match grading for automation
        passed = item['expected'].lower() in answer.lower()
        
        print(f"  Latency: {latency:.2f}s")
        print(f"  Passed: {passed}")
        print(f"  Answer: {answer}")
        
        results.append({
            "query": query,
            "answer": answer,
            "expected": item['expected'],
            "pass": passed,
            "latency": latency
        })
        
    # Write to CSV
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results_day6.csv"))
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["query", "answer", "expected", "pass", "latency"])
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\nEvaluation complete. Results saved to {csv_path}")
    
if __name__ == "__main__":
    run_evaluation()
