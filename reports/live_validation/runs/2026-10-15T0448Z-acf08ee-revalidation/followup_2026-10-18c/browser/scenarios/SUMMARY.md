# A/B/C run summary

Every value below is read from the saved events of this run.

| Scenario | Served by | Embedding | Retrieved | Eligible | Unrelated excluded | Risk | Threshold | Terminal |
|---|---|---|---|---|---|---|---|---|
| B-direct-cloudflare | cloudflare / @cf/meta/llama-3.3-70b-instruct-fp8-fast (reported @cf/meta/llama-3.3-70b-instruct-fp8-fast, stop stop) | real (all-MiniLM-L6-v2) | 14 | 1 | 13 | R2 | 0.6 | abstention  |
| B-direct-nvidia | nvidia / nvidia/nemotron-3-super-120b-a12b (reported nvidia/nemotron-3-super-120b-a12b, stop stop) | real (all-MiniLM-L6-v2) | 14 | 1 | 13 | R2 | 0.6 | abstention  |
| C-context | groq / openai/gpt-oss-120b (reported openai/gpt-oss-120b, stop stop) | real (all-MiniLM-L6-v2) | 14 | 1 | 13 | R2 | 0.6 | abstention  |
| N1-note-policy | groq / openai/gpt-oss-120b (reported openai/gpt-oss-120b, stop stop) | real (all-MiniLM-L6-v2) | 14 | 1 | 13 | R2 | 0.6 | abstention  |
| N2-note-injection | no model called (stopped before the generating stage) | None (None) | None | None | None | None | None | error INPUT_REJECTED |

## B-direct-cloudflare

- Requests: POST /api/v1/analyze -> 200
- Patient context sent: `{}`
- Risk basis: a multi-drug interaction question with no approved severe relationship record
- Terminal reason: 8 of 8 generated claims failed post-generation verification. 8 of them could not be matched to a drug relationship because the evidence records carry no relationship identity.
- Removed disclaimers: []
- Model selection sent: `{"mode": "manual", "model_id": "@cf/meta/llama-3.3-70b-instruct-fp8-fast"}`; selected in page: `{"provider": "cloudflare", "model_id": "@cf/meta/llama-3.3-70b-instruct-fp8-fast", "label": "Cloudflare Llama-3.3 70B Instruct (cloudflare)"}`
- Requested model on a provider failure: `null`
- Stream: 20 events recorded in the page, 20 over the network; terminal event captured: True
- RxNorm (name, RxCUI, name source, resolved by, status): [('Simvastatin', '36567', 'rxnorm_exact', 'rxnorm_exact', 'MATCHED'), ('Clarithromycin', '21212', 'rxnorm_exact', 'rxnorm_exact', 'MATCHED')] overall RESOLVED
- Eligible chunks given to the model that name neither drug: none
  - Claim 0: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "The concomitant administration of simvastatin and clarithromycin is contraindicated due to an increased risk of myopathy and rhabdomyolysis. Important risks include myopathy and rhabdomyolysis. Patient context and specific conditions are unknown. Recommendation: Clinician follow-up is necessary to assess patient-specific risks and determine the best course of treatment. Research disclaimer: The information provided is based on the retrieved evidence and should not be considered as medical advice. It is essential to consult the original sources and healthcare professionals for comprehensive guidance."
  - Claim 1: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "simvastatin interacts with clarithromycin; Concomitant administration of strong CYP3A4 inhibitors; Increased risk of myopathy and rhabdomyolysis; severity serious [Source 1]."
  - Claim 2: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "simvastatin can cause myopathy; severity serious [Source 1]."
  - Claim 3: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "simvastatin can cause rhabdomyolysis; severity serious [Source 1]."
  - Claim 4: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Concomitant administration of strong CYP3A4 inhibitors is contraindicated [Source 1]"
  - Claim 5: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Simvastatin is a cholesterol-lowering medication"
  - Claim 6: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Clarithromycin is a strong CYP3A4 inhibitor"
  - Claim 7: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Concomitant administration of simvastatin and clarithromycin is contraindicated due to an increased risk of myopathy and rhabdomyolysis"

## B-direct-nvidia

- Requests: POST /api/v1/analyze -> 200
- Patient context sent: `{}`
- Risk basis: a multi-drug interaction question with no approved severe relationship record
- Terminal reason: 5 of 5 generated claims failed post-generation verification. 5 of them could not be matched to a drug relationship because the evidence records carry no relationship identity.
- Removed disclaimers: []
- Model selection sent: `{"mode": "manual", "model_id": "nvidia/nemotron-3-super-120b-a12b"}`; selected in page: `{"provider": "nvidia", "model_id": "nvidia/nemotron-3-super-120b-a12b", "label": "NVIDIA Nemotron-3 Super 120B (nvidia)"}`
- Requested model on a provider failure: `null`
- Stream: 20 events recorded in the page, 20 over the network; terminal event captured: True
- RxNorm (name, RxCUI, name source, resolved by, status): [('Simvastatin', '36567', 'cache', 'cache', 'MATCHED'), ('Clarithromycin', '21212', 'cache', 'cache', 'MATCHED')] overall RESOLVED
- Eligible chunks given to the model that name neither drug: none
  - Claim 0: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Evidence indicates that simvastatin is contraindicated with clarithromycin due to CYP3A4 inhibition, which increases simvastatin exposure and the risk of myopathy and rhabdomyolysis. No patient-specific information was provided. Clinicians should avoid concomitant use; if alternative therapy is needed, consider a different antibiotic or a statin less dependent on CYP3A4, with appropriate monitoring for muscle toxicity."
  - Claim 1: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "simvastatin interacts with clarithromycin; CYP3A4 inhibition; Increased risk of myopathy and rhabdomyolysis; severity serious [Source 1]."
  - Claim 2: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Concomitant use of simvastatin with clarithromycin is contraindicated due to increased risk of myopathy and rhabdomyolysis [Source 1]"
  - Claim 3: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Simvastatin is contraindicated with clarithromycin due to CYP3A4 inhibition leading to increased risk of myopathy and rhabdomyolysis."
  - Claim 4: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Concomitant use of simvastatin with clarithromycin is contraindicated."

## C-context

- Requests: POST /api/v1/analyze -> 200
- Patient context sent: `{"age": 58, "sex": "male", "known_conditions": ["hyperlipidemia"]}`
- Risk basis: a multi-drug interaction question with no approved severe relationship record
- Terminal reason: 5 of 5 generated claims failed post-generation verification. 5 of them could not be matched to a drug relationship because the evidence records carry no relationship identity.
- Removed disclaimers: []
- Model selection sent: `{"mode": "auto"}`; selected in page: `null`
- Requested model on a provider failure: `null`
- Stream: 20 events recorded in the page, 0 over the network; terminal event captured: True
- RxNorm (name, RxCUI, name source, resolved by, status): [('Simvastatin', '36567', 'cache', 'cache', 'MATCHED'), ('Clarithromycin', '21212', 'cache', 'cache', 'MATCHED')] overall RESOLVED
- Eligible chunks given to the model that name neither drug: none
  - Claim 0: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Simvastatin and clarithromycin have a verified contraindicated interaction due to strong CYP3A4 inhibition, which can markedly increase simvastatin plasma concentrations and raise the risk of myopathy and rhabdomyolysis. The interaction is classified as high severity. No additional adverse reaction, food guidance, or patient‑specific considerations were identified in the provided evidence. Clinicians should avoid co‑prescribing these agents or consider alternative therapies and monitor for muscle toxicity if co‑administration cannot be avoided. This summary is based solely on the supplied evidence and does not replace clinical judgment. [Research Disclaimer]"
  - Claim 1: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "simvastatin interacts with clarithromycin; CYP3A4 inhibition leading to increased simvastatin levels; Increased risk of myopathy and rhabdomyolysis; severity high [Source 1]."
  - Claim 2: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Contraindicated with clarithromycin due to risk of myopathy and rhabdomyolysis [Source 1]"
  - Claim 3: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Simvastatin is contraindicated when co‑administered with clarithromycin because clarithromycin is a strong CYP3A4 inhibitor."
  - Claim 4: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "The interaction can increase the risk of myopathy and rhabdomyolysis."

## N1-note-policy

- Requests: POST /api/v1/analyze -> 200
- Patient context sent: `{}`
- Risk basis: a multi-drug interaction question with no approved severe relationship record
- Terminal reason: 6 of 6 generated claims failed post-generation verification. 6 of them could not be matched to a drug relationship because the evidence records carry no relationship identity.
- Removed disclaimers: []
- Model selection sent: `{"mode": "auto"}`; selected in page: `null`
- Requested model on a provider failure: `null`
- Stream: 20 events recorded in the page, 0 over the network; terminal event captured: True
- RxNorm (name, RxCUI, name source, resolved by, status): [('Simvastatin', '36567', 'cache', 'cache', 'MATCHED'), ('Clarithromycin', '21212', 'cache', 'cache', 'MATCHED')] overall RESOLVED
- Eligible chunks given to the model that name neither drug: none
  - Claim 0: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Evidence confirms a contraindicated interaction between simvastatin and clarithromycin due to CYP3A4 inhibition, leading to increased risk of myopathy and rhabdomyolysis. No patient-specific factors were provided, so the interaction applies generally. Clinicians should avoid coadministration, consider alternative statins not metabolized by CYP3A4, or adjust therapy with close monitoring if use is unavoidable. This summary is based solely on the supplied evidence and does not replace clinical judgment. Always consult current clinical guidelines and resources. [Research Disclaimer]"
  - Claim 1: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "simvastatin interacts with clarithromycin; CYP3A4 inhibition increasing simvastatin exposure; Increased risk of myopathy and rhabdomyolysis; severity serious [Source 1]."
  - Claim 2: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Concomitant administration of strong CYP3A4 inhibitors (e.g., clarithromycin) with simvastatin is contraindicated due to increased risk of myopathy and rhabdomyolysis. [Source 1]"
  - Claim 3: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Simvastatin and clarithromycin have a contraindicated interaction due to CYP3A4 inhibition."
  - Claim 4: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "The interaction increases risk of myopathy and rhabdomyolysis."
  - Claim 5: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Concomitant administration of strong CYP3A4 inhibitors with simvastatin is contraindicated."

## N2-note-injection

- Requests: POST /api/v1/analyze -> 200
- Patient context sent: `{}`
- Risk basis: None
- Terminal reason: The additional instructions did not pass security checks. Remove instructions aimed at the system, markup or personal identifiers and retry.
- Removed disclaimers: None
- Model selection sent: `{"mode": "auto"}`; selected in page: `null`
- Requested model on a provider failure: `null`
- Stream: 2 events recorded in the page, 2 over the network; terminal event captured: True

## Credential-shaped strings

None found.
