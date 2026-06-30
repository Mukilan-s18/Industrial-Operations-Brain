import pytest
from src.ner_pipeline import NERPipeline

@pytest.fixture(scope="module")
def pipeline():
    return NERPipeline()

def test_equipment_extraction(pipeline):
    text = "Technician checked Pump P-101 and Compressor C-201."
    entities = pipeline.extract_entities(text)
    
    eq_ents = [e for e in entities if e.label == "EQUIPMENT"]
    assert len(eq_ents) == 2
    assert eq_ents[0].id == "P-101"
    assert eq_ents[1].id == "C-201"

def test_alias_resolution(pipeline):
    # Test normalization and resolving "Pump P101" to "P-101"
    text1 = "Pump P101 shows high vibration."
    entities1 = pipeline.extract_entities(text1)
    eq1 = [e for e in entities1 if e.label == "EQUIPMENT"]
    assert len(eq1) == 1
    assert eq1[0].id == "P-101"
    
    # Test rapidfuzz fallback / matching
    existing = ["P-101"]
    resolved = pipeline.resolve_alias("Pump P-101", "EQUIPMENT", existing)
    assert resolved == "P-101"
    
    # Test blocklist: P-101 should NOT merge with P-102 even if similar
    resolved_blocked = pipeline.resolve_alias("Pump P-102", "EQUIPMENT", ["P-101"])
    assert resolved_blocked != "P-101"
    assert resolved_blocked == "P-102"

def test_regulation_and_failure_modes(pipeline):
    text = "Under OISD-118, all pumps with a seal leak failure must be shut down."
    entities = pipeline.extract_entities(text)
    
    reg_ents = [e for e in entities if e.label == "REGULATION"]
    fail_ents = [e for e in entities if e.label == "FAILURE_MODE"]
    
    assert len(reg_ents) == 1
    assert reg_ents[0].id == "OISD-118"
    
    assert len(fail_ents) == 1
    assert fail_ents[0].id == "seal leak"

def test_parameter_value_association(pipeline):
    text = "The bearing temperature reached 82 C on the unit."
    entities = pipeline.extract_entities(text)
    
    param_ents = [e for e in entities if e.label == "PARAMETER"]
    assert len(param_ents) == 1
    assert param_ents[0].id == "bearing temperature"
    # The parameter value should be linked to the parameter entity properties
    assert param_ents[0].properties.get("value") == "82 C"
