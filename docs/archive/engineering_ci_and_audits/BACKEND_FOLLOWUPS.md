# Backend follow-ups found during the UI redesign

Found on 2026-10-13 while verifying branch `ui/3d-redesign`. **None of these are fixed on that branch**;
the backend is unchanged. Inputs were synthetic drug names only.
Line numbers refer to the working-tree copies of `live_application.py` and `live_schemas.py`, which
include uncommitted backend changes at the time of writing.

## Reproduction

Backend: `uv run uvicorn adaptive_trust_medical_rag.api.app:app --app-dir src --host 127.0.0.1 --port 8000`

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"input_mode":"direct_drugs","drug_names":["Metformin","Amoxicillin"],"patient_context":null,"llm_selection":{"mode":"auto"},"additional_instructions":null}'
# -> {"request_id":"75946f99-7931-4131-af23-4fbc21471709","stream_url":"/api/v1/stream/75946f99-…"}

curl -s -N http://127.0.0.1:8000/api/v1/stream/75946f99-7931-4131-af23-4fbc21471709
```

The stream emitted `rxnorm`, `retrieval`, `security`, `trust`, 17 × `stage_update`, `answer` and `complete`.
The model was `nvidia/nemotron-3-super-120b-a12b` (auto mode); `gate_decision` was `release`. The same
pattern repeated in two further runs through the UI the same day.

## (a) 13 of 14 evidence items match neither query drug

`rxnorm` resolved both drugs correctly: metformin (RxCUI 6809) and amoxicillin (RxCUI 723).

`retrieval` → `{"evidence_count": 14, "sources": ["OPENFDA", "PUBMED", "DAILYMED"]}`

`answer.evidence[]`, in order (`document_id` | start of `text`):

| # | document_id | Subject of the text |
|---|---|---|
| 1 | SPL-METFORMIN-001 | Metformin (lactic acidosis, renal contraindication) |
| 2 | FDA-AE-9991 | Aspirin |
| 3 | SPL-WARFARIN-001 | Warfarin + NSAIDs |
| 4 | SPL-LISINOPRIL-001 | Lisinopril |
| 5 | SPL-CARBAMAZEPINE-001 | Carbamazepine |
| 6 | SPL-IBUPROFEN-001 | Ibuprofen |
| 7 | PUBMED-31234567-001 | Oral targeted therapies (nilotinib, pazopanib) |
| 8 | SPL-CLOPIDOGREL-001 | Clopidogrel + omeprazole |
| 9 | SPL-ACETAMINOPHEN-001 | Acetaminophen |
| 10 | SPL-SIMVASTATIN-001 | Simvastatin |
| 11 | SPL-LISINOPRIL-002 | Lisinopril |
| 12 | SPL-FLUOXETINE-001 | Fluoxetine |
| 13 | PMID-31234567 | ACE inhibitors + potassium |
| 14 | SPL-ATORVASTATIN-005 | Atorvastatin |

Every item has `provenance_status: "RETRIEVED"` and trust scores of 0.85 to 0.94. No item concerns
amoxicillin. Meanwhile `answer.trust.factors.entity_match` is **1.0** and `consistency` is 1.0.

Why this matters: AGENTS.md §2.3 ("Never attribute evidence about Drug A to Drug B") and the Evidence
Eligibility Gate in `rag-integrity.md` expect entity match to be checked before evidence reaches the LLM
context. Here 13 off-target chunks pass the gate with a perfect entity-match factor. The previous UI
labelled this list "Verified Evidence"; the redesign shows `document_id` tags so the mismatch is visible,
but the filtering belongs in the backend.

Also note: evidence items carry no drug/entity field (keys: `chunk_id, document_id, freshness,
provenance_status, retrieval_method, source_authority, source_name, source_type, text, title,
trust_score`). Adding the matched RxCUI or canonical name per item would let the UI show it directly.

## (b) R0 risk tier despite fatal lactic-acidosis content

`trust` event and `answer.trust`:

```json
{"overall_score": 0.9375, "threshold": 0.3, "risk_class": "R0", "is_eligible": true,
 "factors": {"source_authority": 0.95, "query_relevance": 0.85, "evidence_quality": 0.95, "freshness": 0.9,
             "consistency": 1.0, "entity_match": 1.0, "population_match": 0.8, "anti_poisoning": 1.0, "anti_injection": 1.0},
 "missing_factors": []}
```

The answer's conclusion begins: "Metformin carries a risk of lactic acidosis, which can be fatal, and is
contraindicated in patients with severe renal impairment …".

Observations in `src/adaptive_trust_medical_rag/services/live_application.py` (read, not changed):

- Line 437: `risk_tier = classify_query_risk(" ".join([m["raw_text"] for m in medications]))`. The tier is
  computed from the drug names alone ("Metformin Amoxicillin"), before retrieval or generation, so
  boxed-warning or fatal-outcome content cannot raise it.
- Lines 438–441: thresholds are set for R0, R2 and R3; R1 relies on the 0.45 default.
- Line 739: the `answer` payload sets `"is_eligible": True` as a literal rather than from the trust result.

Under `medical-safety.md` §3, a question whose evidence includes fatal outcomes or contraindications
arguably belongs in R2/R3 (threshold 0.60/0.75 with verified high-authority evidence).

## (c) SSE `answer` payload drops the default disclaimer

`AnalyzeResponse.disclaimer` in `src/adaptive_trust_medical_rag/api/live_schemas.py` (line 256) defaults to
"RESEARCH OUTPUT ONLY. Not reviewed by clinicians. Not for clinical use. Evidence-grounded response from a
research testbed."

The live pipeline builds `response_data` as a plain dict (`live_application.py`, from line 724) and emits
it with `_sse("answer", response_data)` (line 764) without going through `AnalyzeResponse`. The captured
`answer` keys are:

```
abstention_reason, adverse_reactions, claims, conclusion, evidence, food_guidance, gate_decision,
input_mode, interactions, medications, patient_considerations, patient_context_used,
processing_time_ms, provenance, request_id, security, trust, used_model, warnings
```

There is no `disclaimer` key. The frontend now falls back to a fixed constant with the same text
(`frontend/src/constants/disclaimer.ts`), but the backend should include the field (or validate the
payload through `AnalyzeResponse`) so every client gets it.

## Related, frontend: JSON export includes `patient_context_used`

Not a backend bug, but it comes from the same payload: `answer.patient_context_used` echoes the full
patient context. `frontend/src/services/exportService.ts` `exportAsJson()` clears `patient_context` but not
`patient_context_used`, so a JSON export from History contains the patient context by default. Verified
with synthetic input (age 60, condition `SYNTHETIC-CONDITION-TEST`): the Markdown export excluded it, the
JSON export included it. Saved History entries in IndexedDB also keep it (storage, not export).
