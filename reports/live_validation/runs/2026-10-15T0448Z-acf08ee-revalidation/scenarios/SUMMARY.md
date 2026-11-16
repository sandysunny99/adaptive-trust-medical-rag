# A/B/C run summary

Every value below is read from the saved events of this run.

| Scenario | Served by | Embedding | Retrieved | Eligible | Unrelated excluded | Risk | Threshold | Terminal |
|---|---|---|---|---|---|---|---|---|
| A-image | groq / openai/gpt-oss-120b (reported openai/gpt-oss-120b, stop stop) | real (all-MiniLM-L6-v2) | 14 | 1 | 13 | R2 | 0.6 | abstention  |
| B-direct-cloudflare | cloudflare / @cf/meta/llama-3.3-70b-instruct-fp8-fast (reported @cf/meta/llama-3.3-70b-instruct-fp8-fast, stop stop) | real (all-MiniLM-L6-v2) | 14 | 1 | 13 | R2 | 0.6 | abstention  |
| B-direct-nvidia | no model called | real (all-MiniLM-L6-v2) | 14 | None | 13 | R2 | 0.6 | error LLM_ERROR |
| C-context | groq / openai/gpt-oss-120b (reported openai/gpt-oss-120b, stop stop) | real (all-MiniLM-L6-v2) | 14 | 1 | 13 | R2 | 0.6 | abstention  |
| N1-note-policy | groq / openai/gpt-oss-120b (reported openai/gpt-oss-120b, stop stop) | real (all-MiniLM-L6-v2) | 14 | 1 | 13 | R2 | 0.6 | abstention  |
| N2-note-injection | no model called (stopped before the generating stage) | None (None) | None | None | None | None | None | error INPUT_REJECTED |

## A-image

- Requests: POST /api/v1/analyze/prescription -> 200, POST /api/v1/analyze/9870b408-1f9e-4e09-b418-6549b330599d/confirm -> 200
- Patient context sent: `null`
- Risk basis: a multi-drug interaction question with no approved severe relationship record
- Terminal reason: 6 of 6 generated claims failed post-generation verification. 6 of them could not be matched to a drug relationship because the evidence records carry no relationship identity.
- Removed disclaimers: []
- Model selection sent: `null`; selected in page: `null`
- Requested model on a provider failure: `null`
- Stream: 24 events recorded in the page, 24 over the network; terminal event captured: True
- Vision provider/model: nvidia_vision / meta/llama-3.2-11b-vision-instruct
- Confirmation (200): `{"confirmed_medications": [{"name": "Simvastatin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Simvastatin"}, {"name": "Clarithromycin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Clarithromycin"}]}`
- RxNorm (name, RxCUI, name source, resolved by, status): [('Simvastatin', '36567', 'VISION', 'rxnorm_exact', 'MATCHED'), ('Clarithromycin', '21212', 'VISION', 'rxnorm_exact', 'MATCHED')] overall RESOLVED
- Eligible chunks given to the model that name neither drug: none
  - Claim 0: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Evidence confirms a contraindicated interaction between simvastatin and clarithromycin due to CYP3A4 inhibition, which can raise simvastatin levels and increase the risk of myopathy and rhabdomyolysis. No additional adverse reactions, food‑related guidance, or patient‑specific considerations were identified in the provided evidence. Clinicians should avoid co‑prescribing these agents or select alternative therapies. This information is provided for educational purposes and should not replace professional medical advice."
  - Claim 1: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "simvastatin interacts with clarithromycin; CYP3A4 inhibition leading to increased simvastatin exposure; Increased risk of myopathy and rhabdomyolysis [Source 1]."
  - Claim 2: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Concomitant use of clarithromycin with simvastatin is contraindicated due to risk of myopathy and rhabdomyolysis. [Source 1]"
  - Claim 3: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Simvastatin and clarithromycin have a contraindicated interaction due to CYP3A4 inhibition."
  - Claim 4: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "The interaction increases risk of myopathy and rhabdomyolysis."
  - Claim 5: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "No adverse reaction, food guidance, or patient‑specific factors were found in the evidence."

## B-direct-cloudflare

- Requests: POST /api/v1/analyze -> 200
- Patient context sent: `{}`
- Risk basis: a multi-drug interaction question with no approved severe relationship record
- Terminal reason: 8 of 8 generated claims failed post-generation verification. 8 of them could not be matched to a drug relationship because the evidence records carry no relationship identity.
- Removed disclaimers: []
- Model selection sent: `{"mode": "manual", "model_id": "@cf/meta/llama-3.3-70b-instruct-fp8-fast"}`; selected in page: `{"provider": "cloudflare", "model_id": "@cf/meta/llama-3.3-70b-instruct-fp8-fast", "label": "Cloudflare Llama-3.3 70B Instruct (cloudflare)"}`
- Requested model on a provider failure: `null`
- Stream: 20 events recorded in the page, 20 over the network; terminal event captured: True
- RxNorm (name, RxCUI, name source, resolved by, status): [('Simvastatin', '36567', 'cache', 'cache', 'MATCHED'), ('Clarithromycin', '21212', 'cache', 'cache', 'MATCHED')] overall RESOLVED
- Eligible chunks given to the model that name neither drug: none
  - Claim 0: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "The concomitant administration of simvastatin and clarithromycin is contraindicated due to an increased risk of myopathy and rhabdomyolysis. Important risks include myopathy and rhabdomyolysis. There is insufficient information to determine patient-specific limitations. Clinician follow-up is recommended to discuss alternative treatment options. The evidence provided does not include information on patient context, and therefore, no patient-specific considerations can be made. In conclusion, the combination of simvastatin and clarithromycin poses significant risks and should be avoided. Mandatory research disclaimer: This analysis is based on the provided evidence and should not be considered as medical advice. A healthcare professional should be consulted for proper evaluation and treatment."
  - Claim 1: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "simvastatin interacts with clarithromycin; Concomitant administration contraindication; Increased risk of myopathy and rhabdomyolysis; severity serious [Source 1]."
  - Claim 2: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "simvastatin can cause myopathy; severity serious [Source 1]."
  - Claim 3: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "simvastatin can cause rhabdomyolysis; severity serious [Source 1]."
  - Claim 4: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Concomitant administration of simvastatin and clarithromycin is contraindicated [Source 1]"
  - Claim 5: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Simvastatin is a cholesterol-lowering medication"
  - Claim 6: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Concomitant administration of simvastatin and clarithromycin is contraindicated due to increased risk of myopathy and rhabdomyolysis"
  - Claim 7: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Clarithromycin is a strong CYP3A4 inhibitor"

## B-direct-nvidia

- Requests: POST /api/v1/analyze -> 200
- Patient context sent: `{}`
- Risk basis: a multi-drug interaction question with no approved severe relationship record
- Terminal reason: nvidia timeout: 
- Removed disclaimers: None
- Model selection sent: `{"mode": "manual", "model_id": "nvidia/nemotron-3-super-120b-a12b"}`; selected in page: `{"provider": "nvidia", "model_id": "nvidia/nemotron-3-super-120b-a12b", "label": "NVIDIA Nemotron-3 Super 120B (nvidia)"}`
- Requested model on a provider failure: `{"mode": "manual", "provider": "nvidia", "model_id": "nvidia/nemotron-3-super-120b-a12b"}`
- Stream: 16 events recorded in the page, 16 over the network; terminal event captured: True
- RxNorm (name, RxCUI, name source, resolved by, status): [('Simvastatin', '36567', 'cache', 'cache', 'MATCHED'), ('Clarithromycin', '21212', 'cache', 'cache', 'MATCHED')] overall RESOLVED

## C-context

- Requests: POST /api/v1/analyze -> 200
- Patient context sent: `{"age": 58, "sex": "male", "known_conditions": ["hyperlipidemia"]}`
- Risk basis: a multi-drug interaction question with no approved severe relationship record
- Terminal reason: 6 of 6 generated claims failed post-generation verification. 6 of them could not be matched to a drug relationship because the evidence records carry no relationship identity.
- Removed disclaimers: []
- Model selection sent: `{"mode": "auto"}`; selected in page: `null`
- Requested model on a provider failure: `null`
- Stream: 20 events recorded in the page, 20 over the network; terminal event captured: True
- RxNorm (name, RxCUI, name source, resolved by, status): [('Simvastatin', '36567', 'cache', 'cache', 'MATCHED'), ('Clarithromycin', '21212', 'cache', 'cache', 'MATCHED')] overall RESOLVED
- Eligible chunks given to the model that name neither drug: none
  - Claim 0: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Simvastatin and clarithromycin have a verified contraindicated interaction due to CYP3A4 inhibition, increasing the risk of myopathy and rhabdomyolysis. No additional adverse reaction, food guidance, or patient‑specific considerations were identified in the provided evidence. Clinician should avoid co‑administration or consider alternative therapy and monitor for muscle toxicity if combination cannot be avoided. This information is provided for educational purposes and should not replace professional medical advice."
  - Claim 1: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "simvastatin interacts with clarithromycin; CYP3A4 inhibition leading to increased simvastatin exposure; Increased risk of myopathy and rhabdomyolysis [Source 1]."
  - Claim 2: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Contraindicated with clarithromycin due to risk of myopathy and rhabdomyolysis [Source 1]"
  - Claim 3: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Simvastatin and clarithromycin have a contraindicated interaction due to CYP3A4 inhibition."
  - Claim 4: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "The interaction increases risk of myopathy and rhabdomyolysis."
  - Claim 5: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "No adverse reactions, food guidance, or patient‑specific considerations were found in the evidence."

## N1-note-policy

- Requests: POST /api/v1/analyze -> 200
- Patient context sent: `{}`
- Risk basis: a multi-drug interaction question with no approved severe relationship record
- Terminal reason: 6 of 6 generated claims failed post-generation verification. 6 of them could not be matched to a drug relationship because the evidence records carry no relationship identity.
- Removed disclaimers: []
- Model selection sent: `{"mode": "auto"}`; selected in page: `null`
- Requested model on a provider failure: `null`
- Stream: 20 events recorded in the page, 20 over the network; terminal event captured: True
- RxNorm (name, RxCUI, name source, resolved by, status): [('Simvastatin', '36567', 'cache', 'cache', 'MATCHED'), ('Clarithromycin', '21212', 'cache', 'cache', 'MATCHED')] overall RESOLVED
- Eligible chunks given to the model that name neither drug: none
  - Claim 0: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Evidence from Source 1 confirms a contraindicated interaction between simvastatin and clarithromycin due to CYP3A4 inhibition, leading to increased risk of myopathy and rhabdomyolysis (serious severity). No patient-specific factors were provided, so individual risk cannot be further assessed. Clinicians should avoid co‑administration of these drugs and consider alternative therapies or dose adjustments if combination is unavoidable. This summary is based solely on the supplied evidence and does not replace professional clinical judgment. Research disclaimer: The information provided reflects the current evidence and should not be used as a substitute for individualized medical advice."
  - Claim 1: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "simvastatin interacts with clarithromycin; CYP3A4 inhibition leading to increased simvastatin exposure; Increased risk of myopathy and rhabdomyolysis; severity serious [Source 1]."
  - Claim 2: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Concomitant administration of clarithromycin with simvastatin is contraindicated due to increased risk of myopathy and rhabdomyolysis. [Source 1]"
  - Claim 3: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "Simvastatin and clarithromycin have a contraindicated interaction due to CYP3A4 inhibition."
  - Claim 4: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "The interaction increases risk of myopathy and rhabdomyolysis."
  - Claim 5: UNSUPPORTED / identity UNAVAILABLE (Source canonical identity not available): "The severity of the interaction is serious."

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
