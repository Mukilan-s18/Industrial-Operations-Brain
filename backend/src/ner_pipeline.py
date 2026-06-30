import os
import re
import yaml
import spacy
from spacy.pipeline import EntityRuler
from rapidfuzz import fuzz
from typing import List, Dict, Any, Tuple
from backend.src.schema import ExtractedEntity

class NERPipeline:
    def __init__(self, spacy_model: str = "en_core_web_sm", config_path: str = None):
        self.nlp = spacy.load(spacy_model)
        
        # Load config dynamically
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "graph_config.yaml")
            
        self.config = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f) or {}
                
        # Configure EntityRuler for custom industrial NER
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        
        # Define industrial regex and phrase patterns from config
        patterns = self.config.get("spacy_patterns", [])
        ruler.add_patterns(patterns)
        
        # Manual overrides and blocklist from config
        self.blocklist = self.config.get("blocklist", {})
        self.manual_mappings = self.config.get("manual_mappings", {})
        
        # Track established entities in this run to perform alias matching
        self.resolved_cache = {} # text -> resolved_id

    def normalize_text(self, text: str) -> str:
        """Helper to clean up strings for matching."""
        # Trim and normalize spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def resolve_alias(self, raw_text: str, label: str, existing_ids: List[str], threshold: float = 90.0) -> str:
        """
        Resolves entity name to standard ID using:
        1. Manual mapping dictionary
        2. Blocklist check
        3. Fuzzy string matching using rapidfuzz (above threshold)
        """
        normalized = self.normalize_text(raw_text)
        
        # 1. Check manual overrides first
        if normalized in self.manual_mappings:
            return self.manual_mappings[normalized]
            
        # 2. Check if we already resolved this exact text in this run
        if normalized in self.resolved_cache:
            return self.resolved_cache[normalized]
            
        # 3. For equipment, let's normalize formats (e.g. Pump P-101 -> P-101, P101 -> P-101)
        if label == "EQUIPMENT":
            match = re.search(r'([A-Z])[- ]?(\d{3,4})', normalized, re.IGNORECASE)
            if match:
                prefix = match.group(1).upper()
                digits = match.group(2)
                resolved_id = f"{prefix}-{digits}"
                self.resolved_cache[normalized] = resolved_id
                return resolved_id

        # 4. Use rapidfuzz to match against existing entities of the same label
        best_match = None
        best_score = 0.0
        
        for ext_id in existing_ids:
            # Check blocklist override
            if ext_id in self.blocklist and normalized in self.blocklist[ext_id]:
                continue
            if normalized in self.blocklist and ext_id in self.blocklist[normalized]:
                continue
                
            score = fuzz.ratio(normalized.lower(), ext_id.lower())
            if score > best_score:
                best_score = score
                best_match = ext_id
                
        if best_score >= threshold and best_match:
            self.resolved_cache[normalized] = best_match
            return best_match
            
        # Default fallback is the normalized text itself
        self.resolved_cache[normalized] = normalized
        return normalized

    def extract_entities(self, text: str, existing_ids: List[str] = None) -> List[ExtractedEntity]:
        if existing_ids is None:
            existing_ids = []
            
        doc = self.nlp(text)
        extracted = []
        
        # Temporary storage for parameter values to match them to parameters if nearby
        param_values = []
        spacy_ents = list(doc.ents)
        
        # We also manually extract Dates using standard spaCy or regex
        # Date regex: YYYY-MM-DD or standard months
        date_pattern = re.compile(r'\b\d{4}-\d{2}-\d{2}\b')
        for match in date_pattern.finditer(text):
            span_start, span_end = match.span()
            # Check if already in spacy_ents to avoid overlap
            overlap = any(e.start_char < span_end and e.end_char > span_start for e in spacy_ents)
            if not overlap:
                # Add date
                extracted.append(ExtractedEntity(
                    id=match.group(0),
                    label="DATE",
                    span_start=span_start,
                    span_end=span_end,
                    text=match.group(0),
                    properties={}
                ))

        for ent in spacy_ents:
            # For PERSON, DATE, ORG from standard spacy
            label = ent.label_
            text_str = ent.text
            
            # Map standard spaCy labels to our target ontology labels
            if label == "PERSON":
                resolved_id = text_str
            elif label == "DATE":
                resolved_id = text_str
                label = "DATE"
            elif label in ["EQUIPMENT", "REGULATION", "FAILURE_MODE", "PARAMETER"]:
                resolved_id = self.resolve_alias(text_str, label, existing_ids)
            elif label == "PARAMETER_VALUE":
                # Save parameter values to link to parameter names later
                param_values.append((ent.start_char, ent.end_char, text_str))
                continue # Do not add value as a top-level node unless linked
            elif label == "ORG" and text_str in ["PESO", "OISD"]:
                label = "REGULATION"
                resolved_id = self.resolve_alias(text_str, label, existing_ids)
            else:
                # Keep other labels if they might match regex
                continue
                
            extracted.append(ExtractedEntity(
                id=resolved_id,
                label=label,
                span_start=ent.start_char,
                span_end=ent.end_char,
                text=text_str,
                properties={}
            ))
            
            # Update existing_ids to ensure alias resolution works incrementally
            if resolved_id not in existing_ids:
                existing_ids.append(resolved_id)
                
        # Link parameter values to nearby parameter names (co-occurrence in sentence)
        for val_start, val_end, val_text in param_values:
            # Find the closest parameter entity in the document
            closest_param = None
            min_dist = 999999
            for ext in extracted:
                if ext.label == "PARAMETER":
                    # Calculate distance
                    dist = min(abs(ext.span_start - val_end), abs(val_start - ext.span_end))
                    if dist < min_dist and dist < 50: # max 50 chars away
                        min_dist = dist
                        closest_param = ext
            if closest_param:
                # Assign value to parameter node's properties
                closest_param.properties["value"] = val_text
                
        return extracted

    def evaluate_accuracy(self, labeled_sentences_path: str = None) -> Dict[str, Any]:
        """
        Loads the labeled sentences, extracts entities, and calculates precision,
        recall, and F1 score.
        """
        import json
        if labeled_sentences_path is None:
            labeled_sentences_path = os.path.join(os.path.dirname(__file__), "..", "data", "labeled_sentences.json")
            
        if not os.path.exists(labeled_sentences_path):
            return {
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "true_positives": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "details": []
            }
            
        with open(labeled_sentences_path, "r") as f:
            labeled_data = json.load(f)
            
        tps = 0
        fps = 0
        fns = 0
        details = []
        
        for item in labeled_data:
            sentence = item["sentence"]
            gt_ents = item["entities"] # list of dict: {"text": "...", "label": "..."}
            
            # Reset cache for evaluation to ensure pure sentence-level resolution
            self.resolved_cache = {}
            
            extracted = self.extract_entities(sentence)
            
            gt_set = set((gt["text"], gt["label"]) for gt in gt_ents)
            ext_set = set((ent.id, ent.label) for ent in extracted)
            
            tp_set = gt_set.intersection(ext_set)
            fp_set = ext_set - gt_set
            fn_set = gt_set - ext_set
            
            tps += len(tp_set)
            fps += len(fp_set)
            fns += len(fn_set)
            
            details.append({
                "sentence": sentence,
                "ground_truth": [{"text": t, "label": l} for t, l in gt_set],
                "extracted": [{"text": t, "label": l} for t, l in ext_set],
                "true_positives": [{"text": t, "label": l} for t, l in tp_set],
                "false_positives": [{"text": t, "label": l} for t, l in fp_set],
                "false_negatives": [{"text": t, "label": l} for t, l in fn_set]
            })
            
        precision = tps / (tps + fps) if (tps + fps) > 0 else 0.0
        recall = tps / (tps + fns) if (tps + fns) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "true_positives": tps,
            "false_positives": fps,
            "false_negatives": fns,
            "details": details
        }
