import re
import spacy
from spacy.pipeline import EntityRuler
from rapidfuzz import fuzz
from typing import List, Dict, Any, Tuple
from src.schema import ExtractedEntity

class NERPipeline:
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        self.nlp = spacy.load(spacy_model)
        
        # Configure EntityRuler for custom industrial NER
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        
        # Define industrial regex and phrase patterns
        patterns = [
            # Equipment Patterns
            {"label": "EQUIPMENT", "pattern": [{"TEXT": {"REGEX": "^[A-Z]{1,3}-\\d{3,4}$"}}]}, # P-101, C-201
            {"label": "EQUIPMENT", "pattern": [{"LOWER": "pump"}, {"TEXT": {"REGEX": "^P-?\\d{3,4}$"}}]}, # Pump P-101, Pump P101
            {"label": "EQUIPMENT", "pattern": [{"LOWER": "compressor"}, {"TEXT": {"REGEX": "^C-?\\d{3,4}$"}}]}, # Compressor C-201
            
            # Regulation Patterns
            {"label": "REGULATION", "pattern": [{"TEXT": {"REGEX": "^OISD-\\d{3}$"}}]}, # OISD-118
            {"label": "REGULATION", "pattern": [{"LOWER": "peso"}]}, # PESO
            {"label": "REGULATION", "pattern": [{"LOWER": "factory"}, {"LOWER": "act"}, {"TEXT": {"REGEX": "^\\d{4}$"}, "OP": "?"}]}, # Factory Act 1948
            
            # Failure Mode Patterns
            {"label": "FAILURE_MODE", "pattern": [{"LOWER": "seal"}, {"LOWER": "leak"}]},
            {"label": "FAILURE_MODE", "pattern": [{"LOWER": "bearing"}, {"LOWER": "seizure"}]},
            {"label": "FAILURE_MODE", "pattern": [{"LOWER": "dry"}, {"LOWER": "run"}]},
            {"label": "FAILURE_MODE", "pattern": [{"LOWER": "mechanical"}, {"LOWER": "seal"}, {"LOWER": "degradation"}]},
            {"label": "FAILURE_MODE", "pattern": [{"LOWER": "catastrophic"}, {"LOWER": "failure"}]},
            
            # Parameter Patterns
            {"label": "PARAMETER", "pattern": [{"LOWER": "discharge"}, {"LOWER": "pressure"}]},
            {"label": "PARAMETER", "pattern": [{"LOWER": "bearing"}, {"LOWER": "temperature"}]},
            {"label": "PARAMETER", "pattern": [{"LOWER": "vibration"}, {"LOWER": "level"}]},
            
            # Specific values
            {"label": "PARAMETER_VALUE", "pattern": [{"TEXT": {"REGEX": "^\\d+(\\.\\d+)?$"}}, {"LOWER": {"IN": ["bar", "c", "v", "psi"]}}]}, # 4.5 bar, 82 C
        ]
        
        ruler.add_patterns(patterns)
        
        # Manual override blocklist for alias resolver: {entity_a: [list_of_entities_that_are_NOT_equal]}
        self.blocklist = {
            "P-101": ["P-102", "Pump P-102", "P102"],
            "P-102": ["P-101", "Pump P-101", "P101"],
        }
        
        # Pre-known standard mappings (manual dictionary overrides)
        self.manual_mappings = {
            "Pump P-101": "P-101",
            "Pump P101": "P-101",
            "P101": "P-101",
            "Pump P-102": "P-102",
            "Pump P102": "P-102",
            "P102": "P-102",
            "Compressor C-201": "C-201",
            "C201": "C-201",
            "OISD 118": "OISD-118",
        }
        
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
