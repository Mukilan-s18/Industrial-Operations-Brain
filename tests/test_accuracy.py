import pytest
from src.ner_pipeline import NERPipeline

def test_ner_pipeline_accuracy():
    """
    Evaluates the NER pipeline against the 10 labeled sentences.
    Asserts that the F1 score is >= 0.85 to satisfy accuracy standards.
    """
    pipeline = NERPipeline()
    report = pipeline.evaluate_accuracy()
    
    print("\n=== NER Accuracy Evaluation Report ===")
    print(f"Precision      : {report['precision']:.4f}")
    print(f"Recall         : {report['recall']:.4f}")
    print(f"F1 Score       : {report['f1_score']:.4f}")
    print(f"True Positives : {report['true_positives']}")
    print(f"False Positives: {report['false_positives']}")
    print(f"False Negatives: {report['false_negatives']}")
    print("=======================================")
    
    assert report["true_positives"] > 0
    assert report["f1_score"] >= 0.85
