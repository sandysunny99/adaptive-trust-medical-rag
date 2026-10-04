import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate

class RelationshipGroundingStatus(Enum):
    SUPPORTED = "RELATIONSHIP_SUPPORTED"
    UNSUPPORTED = "RELATIONSHIP_UNSUPPORTED"
    CONTRADICTED = "RELATIONSHIP_CONTRADICTED"
    NO_RELEVANT_RELATION = "NO_RELEVANT_RELATION"
    AMBIGUOUS = "RELATIONSHIP_AMBIGUOUS"
    UNVERIFIABLE = "RELATIONSHIP_UNVERIFIABLE"
    MISSING_PROVENANCE = "RELATIONSHIP_PROVENANCE_MISSING"
    ENTITY_PAIR_MISMATCH = "ENTITY_PAIR_MISMATCH"
    BOUNDED_NEGATIVE = "RELATIONSHIP_BOUNDED_NEGATIVE"

@dataclass
class GroundingDecision:
    status: RelationshipGroundingStatus
    reason: str
    query_relation: Optional[Dict] = None
    candidate_relations: Optional[List[Dict]] = None
    source_relations: Optional[List[Dict]] = None
    entity_alignment: Optional[Dict] = None
    validator_version: str = "V2_POLARITY"

class RelationshipGroundingValidatorV2:
    """
    V2 Validator: Structured, query-conditioned grounding with explicit polarity.
    """
    
    def __init__(self, registry_store: dict[str, dict]):
        self.registry_store = registry_store

    def _extract_entities(self, text: str) -> List[str]:
        pattern = re.compile(r"\b(?:[A-Za-z]+)?(?:mab|nib|olol|pril|sartan|statin|mycin|cillin|cycline|azole|warfarin|metformin|aspirin|insulin|heparin|cyanide|ibuprofen)\b", re.IGNORECASE)
        return list(set([d.lower() for d in pattern.findall(text)]))

    def _extract_relations(self, text: str) -> List[Dict]:
        relations = []
        text_lower = text.lower()
        
        # Default properties
        rel_type = "NONE"
        polarity = "POSITIVE"
        scope = "GENERAL"
        mech = "GENERAL"
        ev_state = "OBSERVED"
        
        is_negated = False
        is_positive = False

        # Check bounded negations first
        if "no clinically significant pharmacokinetic" in text_lower and "interaction" in text_lower:
            rel_type = "INTERACTS_WITH"
            polarity = "NEGATED"
            scope = "CLINICALLY_SIGNIFICANT"
            mech = "PHARMACOKINETIC"
            ev_state = "OBSERVED_ABSENCE"
            is_negated = True
        elif "no clinically significant interaction" in text_lower or "no clinically significant" in text_lower and "interaction" in text_lower:
            rel_type = "INTERACTS_WITH"
            polarity = "NEGATED"
            scope = "CLINICALLY_SIGNIFICANT"
            ev_state = "OBSERVED_ABSENCE"
            is_negated = True
        elif "does not interact" in text_lower or "no interaction" in text_lower or "do not interact" in text_lower or "has not been observed to interact" in text_lower or "no evidence of interaction" in text_lower:
            rel_type = "INTERACTS_WITH"
            polarity = "NEGATED"
            ev_state = "OBSERVED_ABSENCE"
            is_negated = True

        # Check positive relations
        if any(k in text_lower for k in ["interacts with", "interacts", "contraindicat"]) and not is_negated:
            rel_type = "INTERACTS_WITH"
            is_positive = True
        elif any(k in text_lower for k in ["cause", "associat"]):
            rel_type = "ASSOCIATED_WITH"
            is_positive = True
        elif any(k in text_lower for k in ["risk"]):
            rel_type = "INCREASES_RISK"
            is_positive = True
        elif any(k in text_lower for k in ["inhibit"]):
            rel_type = "INHIBITS"
            is_positive = True
        
        # If it matches positive keywords AND negative keywords, but the positive isn't just a substring
        # Let's do a strict check for AMBIGUOUS:
        if ("interacts with" in text_lower or "causes" in text_lower) and ("no interaction" in text_lower or "does not interact" in text_lower):
            rel_type = "INTERACTS_WITH"
            polarity = "AMBIGUOUS"
            
        if rel_type != "NONE":
            relations.append({
                "relation_type": rel_type,
                "polarity": polarity,
                "scope": scope,
                "mechanism_scope": mech,
                "evidence_state": ev_state
            })
            
        return relations

    def _parse_intent(self, query: str) -> Dict:
        """Determines if the query is asking for a relationship."""
        entities = self._extract_entities(query)
        relations = self._extract_relations(query)
        
        intent = {
            "entities": entities,
            "requires_relation": False,
            "relation_type": "NONE",
            "polarity": "POSITIVE"
        }
        
        if relations:
            intent["requires_relation"] = True
            intent["relation_type"] = relations[0]["relation_type"]
            intent["polarity"] = relations[0]["polarity"]
        elif len(entities) >= 2:
            intent["requires_relation"] = True
            intent["relation_type"] = "UNKNOWN"
            
        return intent

    def _parse_candidate_relations(self, text: str) -> List[Dict]:
        entities = self._extract_entities(text)
        relations = self._extract_relations(text)
        
        if not relations:
            return [{"entities": entities, "relation_type": "NONE", "polarity": "POSITIVE", "scope": "GENERAL", "mechanism_scope": "GENERAL", "evidence_state": "OBSERVED"}]
        
        for r in relations:
            r["entities"] = entities
            
        return relations

    def validate(self, candidate: Candidate, query: Optional[str] = None) -> GroundingDecision:
        prov = candidate.metadata.get("provenance", {})
        if prov.get("status") == "PROVENANCE_PARTIAL":
            return GroundingDecision(RelationshipGroundingStatus.UNVERIFIABLE, "Provenance is partial.")
            
        doc_id = prov.get("document_id") or candidate.document_id
        chunk_id = prov.get("chunk_id") or candidate.chunk_id
        
        if not doc_id:
            return GroundingDecision(RelationshipGroundingStatus.MISSING_PROVENANCE, "No document_id found.")
            
        if doc_id not in self.registry_store:
            return GroundingDecision(RelationshipGroundingStatus.UNVERIFIABLE, f"Document {doc_id} not found.")
            
        source_text = self.registry_store[doc_id].get(chunk_id, {}).get("text", "").lower()
        
        # Determine Query Intent
        query_text = query or ""
        query_intent = self._parse_intent(query_text)
        
        # Determine Candidate Relations
        cand_relations = self._parse_candidate_relations(candidate.text)
        source_relations = self._parse_candidate_relations(source_text)
        
        entity_alignment = {
            "query_entities": query_intent["entities"],
            "candidate_entities": cand_relations[0]["entities"] if cand_relations else [],
            "source_entities": source_relations[0]["entities"] if source_relations else []
        }
        
        # Core Decision Logic
        if not query_intent["requires_relation"]:
            return GroundingDecision(
                status=RelationshipGroundingStatus.SUPPORTED,
                reason="Query does not require a relationship check.",
                query_relation=query_intent,
                candidate_relations=cand_relations,
                source_relations=source_relations,
                entity_alignment=entity_alignment
            )
            
        # Query requires relation
        cand_has_relation = any(r["relation_type"] != "NONE" for r in cand_relations)
        source_has_relation = any(r["relation_type"] != "NONE" for r in source_relations)
        
        if not cand_has_relation:
            return GroundingDecision(
                status=RelationshipGroundingStatus.NO_RELEVANT_RELATION,
                reason="Candidate contains no relationship but query requires a relationship.",
                query_relation=query_intent,
                candidate_relations=cand_relations,
                source_relations=source_relations,
                entity_alignment=entity_alignment
            )
            
        # Endpoint Alignment
        q_ents = set(query_intent["entities"])
        c_ents = set(cand_relations[0]["entities"])
        if not q_ents.issubset(c_ents):
            return GroundingDecision(
                status=RelationshipGroundingStatus.ENTITY_PAIR_MISMATCH,
                reason="Candidate relation endpoints do not match query endpoints.",
                query_relation=query_intent,
                candidate_relations=cand_relations,
                source_relations=source_relations,
                entity_alignment=entity_alignment
            )

        cand_rel = cand_relations[0]
        source_rel = source_relations[0]
        
        if not source_has_relation:
            return GroundingDecision(
                status=RelationshipGroundingStatus.UNSUPPORTED,
                reason="Candidate introduces a relationship absent from source.",
                query_relation=query_intent,
                candidate_relations=cand_relations,
                source_relations=source_relations,
                entity_alignment=entity_alignment
            )
            
        # If both have relation, check entities alignment roughly
        for ce in cand_rel["entities"]:
            if ce not in source_rel["entities"]:
                return GroundingDecision(
                    status=RelationshipGroundingStatus.UNSUPPORTED,
                    reason=f"Entity '{ce}' not in source.",
                    query_relation=query_intent,
                    candidate_relations=cand_relations,
                    source_relations=source_relations,
                    entity_alignment=entity_alignment
                )
                
        # Polarity Comparison
        if cand_rel["polarity"] == "POSITIVE" and source_rel["polarity"] == "NEGATED":
            # The FDA label negated the interaction, but candidate asserts it
            return GroundingDecision(
                status=RelationshipGroundingStatus.CONTRADICTED,
                reason="Candidate asserts positive relation but source is negated.",
                query_relation=query_intent,
                candidate_relations=cand_relations,
                source_relations=source_relations,
                entity_alignment=entity_alignment
            )
            
        if cand_rel["polarity"] == "NEGATED" and source_rel["polarity"] == "POSITIVE":
            return GroundingDecision(
                status=RelationshipGroundingStatus.CONTRADICTED,
                reason="Candidate asserts negated relation but source is positive.",
                query_relation=query_intent,
                candidate_relations=cand_relations,
                source_relations=source_relations,
                entity_alignment=entity_alignment
            )
            
        # If candidate is a negative bounded relation
        if cand_rel["polarity"] == "NEGATED" and source_rel["polarity"] == "NEGATED":
            return GroundingDecision(
                status=RelationshipGroundingStatus.BOUNDED_NEGATIVE,
                reason="Relationship correctly grounded as bounded negative finding.",
                query_relation=query_intent,
                candidate_relations=cand_relations,
                source_relations=source_relations,
                entity_alignment=entity_alignment
            )
            
        # Positive Match
        return GroundingDecision(
            status=RelationshipGroundingStatus.SUPPORTED,
            reason="Relationship supported by source.",
            query_relation=query_intent,
            candidate_relations=cand_relations,
            source_relations=source_relations,
            entity_alignment=entity_alignment
        )
