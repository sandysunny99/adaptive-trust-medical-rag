# CLAIM_VERIFIER_V2_MODEL_SELECTION_PROPOSAL

## Overview
The V2 Claim Verifier requires a Natural Language Inference (NLI) model to perform semantic entailment, contradiction, and neutral assessments. 

## Current Environment Audit
An inspection of the local Hugging Face cache (`cognee_service/model_cache/`) and the project manifests revealed that no appropriate NLI model is currently approved or provisioned. 
- The existing models are `BAAI/bge-small-en-v1.5` (an embedding model) and `fastino/gliner2.5-base-v1` (an NER model). 
- Neither model is capable of outputting the `entailment`, `contradiction`, and `neutral` logits required by the V2 semantic contract.

## Proposed NLI Model
To fulfill the requirements of the V2 verifier, I propose the following model:

- **Candidate Model:** `MoritzLaurer/DeBERTa-v3-base-mnli-fever-docnli-ling-2c` (or a similar DeBERTa-based NLI cross-encoder).
- **Exact Revision:** `main` (hash must be locked upon download approval).
- **Task Type:** Zero-shot classification / Natural Language Inference (Cross-Encoder).
- **Expected Labels:** `entailment`, `contradiction`, `neutral`.
- **Licensing:** MIT / Apache 2.0 (Compatible with research usage).
- **Model Size:** ~350MB (Base), lightweight enough for rapid local inference.
- **Required Dependencies:** `transformers`, `torch` (already available in the environment).

*Alternatively, if a purely medical NLI model is preferred:*
- **Candidate Model:** `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext` fine-tuned on MedNLI.

## Access & Integration
The model will be downloaded directly to the offline Hugging Face cache. The ClaimVerifier V2 logic will wrap this model using the `transformers` pipeline (`text-classification` / `zero-shot-classification`) or `sentence-transformers` CrossEncoder class, preserving the exact probability distribution for thresholding.

## Request for Authorization
In accordance with the strict project model-provenance requirements, I am halting implementation. Please authorize the download and integration of a specific NLI model so that `ClaimVerifierV2` can be built and evaluated.
