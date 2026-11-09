# Medication Analysis Output Schema

## Structured Response

```json
{
  "request_id": "string (UUID)",
  "input_mode": "prescription_image | direct_drugs | multiple_drugs",
  "processing_time_ms": 4200,
  
  "medications": [
    {
      "raw_text": "Amoxicillin 500mg",
      "canonical_name": "amoxicillin",
      "rxcui": "723",
      "brand_name": "Amoxil",
      "formulation": "Tablet",
      "strength": "500 mg",
      "frequency": "1-0-1",
      "route": "Oral",
      "confidence": 0.94,
      "source": "rxnorm_exact",
      "status": "MATCHED"
    }
  ],
  
  "patient_context": {
    "age": 65,
    "sex": "male",
    "known_allergies": ["penicillin"],
    "known_conditions": ["type_2_diabetes"],
    "current_medications": ["lisinopril"],
    "factors_used": ["age", "known_allergies"],
    "factors_missing": ["kidney_impairment"]
  },
  
  "drug_by_drug_summary": [
    {
      "drug": "amoxicillin",
      "rxcui": "723",
      "common_reactions": ["Diarrhea", "Nausea", "Rash"],
      "serious_reactions": ["Anaphylaxis", "C. difficile colitis"],
      "warnings": ["Cross-reactivity in penicillin-allergic patients"],
      "contraindications": ["Known penicillin hypersensitivity"],
      "evidence_status": "VERIFIED",
      "sources": ["DailyMed", "PubMed"]
    }
  ],
  
  "interactions": [
    {
      "drug_a": "amoxicillin",
      "drug_b": "metformin",
      "rxcui_a": "723",
      "rxcui_b": "6809",
      "interaction_detected": false,
      "interaction_type": null,
      "potential_effect": null,
      "severity": null,
      "evidence_status": "NOT_ESTABLISHED",
      "relationship_status": "UNAVAILABLE",
      "sources": []
    }
  ],
  
  "adverse_reactions": [
    {
      "drug": "amoxicillin",
      "reaction": "Diarrhea",
      "severity": "common",
      "evidence_level": "VERIFIED",
      "frequency": null,
      "source": "DailyMed FDA Label"
    }
  ],
  
  "warnings": [
    "ALLERGY ALERT: Patient reports penicillin allergy. Amoxicillin is a penicillin antibiotic. [Source: DailyMed]"
  ],
  
  "food_guidance": [
    {
      "drug": "amoxicillin",
      "administration": "May be taken with or without food",
      "food_relationship": "WITH_OR_WITHOUT",
      "timing": null,
      "food_interactions": [],
      "evidence_status": "VERIFIED",
      "source": "DailyMed FDA Label"
    }
  ],
  
  "patient_considerations": [
    {
      "factor": "Penicillin allergy",
      "provided": true,
      "evidence_found": true,
      "consideration": "Amoxicillin is a penicillin antibiotic. Cross-reactivity risk in penicillin-allergic patients.",
      "evidence_status": "VERIFIED",
      "source": "DailyMed"
    },
    {
      "factor": "Kidney impairment",
      "provided": false,
      "evidence_found": false,
      "consideration": "Kidney function is relevant to evaluating amoxicillin dosing, but no kidney status was provided. Patient-specific guidance is therefore limited.",
      "evidence_status": "LIMITED",
      "source": null
    }
  ],
  
  "trust": {
    "overall_score": 0.78,
    "threshold": 0.75,
    "risk_class": "R2",
    "is_eligible": true,
    "factors": {
      "source_authority": 0.85,
      "query_relevance": 0.72,
      "evidence_quality": 0.80,
      "freshness": 0.76,
      "consistency": 0.81,
      "entity_match": 0.90,
      "population_match": null,
      "anti_poisoning": 1.00,
      "anti_injection": 1.00
    },
    "missing_factors": ["population_match"]
  },
  
  "security": {
    "injection_status": "ALLOW",
    "poisoning_status": "ALLOW",
    "injection_markers": [],
    "poisoning_reason": null
  },
  
  "claims": [
    {
      "claim_id": 1,
      "text": "Amoxicillin may cause cross-reactivity in penicillin-allergic patients.",
      "support_state": "SUPPORTED",
      "entailment": 0.92,
      "contradiction": 0.03,
      "citation_present": true,
      "citation_resolves": true,
      "best_evidence_chunk": "CHK-00428",
      "canonical_identity_status": "MATCH"
    }
  ],
  
  "evidence": [
    {
      "chunk_id": "CHK-00428",
      "document_id": "DOC-FDA-AMX",
      "source_type": "PRIMARY_REGULATORY",
      "source_name": "DailyMed",
      "title": "FDA Label: Amoxicillin",
      "text": "Serious and occasionally fatal hypersensitivity reactions...",
      "pmid": null,
      "doi": null,
      "url": "https://dailymed.nlm.nih.gov/...",
      "source_authority": 1.00,
      "trust_score": 0.85,
      "freshness": 0.92,
      "retrieval_method": "hybrid-rrf",
      "provenance_status": "VERIFIED"
    }
  ],
  
  "provenance": [
    {
      "level": "source",
      "id": "dailymed",
      "label": "DailyMed / FDA"
    },
    {
      "level": "document",
      "id": "DOC-FDA-AMX",
      "label": "FDA Label: Amoxicillin"
    },
    {
      "level": "chunk",
      "id": "CHK-00428",
      "label": "Warnings and Precautions Section"
    },
    {
      "level": "claim",
      "id": "C1",
      "label": "Cross-reactivity in penicillin-allergic patients"
    }
  ],
  
  "conclusion": "3 medicines identified. 1 verified allergy concern. Patient-specific assessment limited: kidney function not provided.",
  "gate_decision": "release",
  "abstention_reason": null,
  "disclaimer": "RESEARCH OUTPUT ONLY. Not reviewed by clinicians. Not for clinical use. Evidence-grounded response from a research testbed."
}
```

## Abstention Response

```json
{
  "request_id": "uuid",
  "input_mode": "direct_drugs",
  "medications": [...],
  "gate_decision": "abstain",
  "abstention_reason": "Evidence was insufficient to safely produce a supported answer.",
  "abstention_stage": "evidence_eligibility",
  "trust": {
    "overall_score": 0.46,
    "threshold": 0.75,
    "is_eligible": false,
    "missing_factors": ["freshness", "population_match"]
  },
  "conclusion": null,
  "evidence": [],
  "disclaimer": "..."
}
```
