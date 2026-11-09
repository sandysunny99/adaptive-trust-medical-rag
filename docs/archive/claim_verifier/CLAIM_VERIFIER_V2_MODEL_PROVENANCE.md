# CLAIM_VERIFIER_V2_MODEL_PROVENANCE

## Model Provenance
- **Model ID:** `pritamdeka/PubMedBERT-MNLI-MedNLI`
- **Pinned Revision:** `f1b6ce2e0d49f295b4cbcdc56c01b5fab6d068ab`
- **Model Source:** Hugging Face Model Hub
- **Base Model:** PubMedBERT
- **NLI Training Datasets:** MNLI, MedNLI
- **Reported Task:** 3-class Natural Language Inference (Biomedical/Clinical)
- **Labels:** `entailment`, `contradiction`, `neutral`
- **Model Size:** ~438 MB (SafeTensors)
- **File Format:** `.safetensors`
- **Tokenizer:** PubMedBERT Tokenizer
- **Framework:** PyTorch / Transformers
- **Reported Evaluation Result:** 0.8667 accuracy (on its specific evaluation setup)
- **Project Role:** Dedicated Claim-Evidence semantic NLI verifier (ClaimVerifierV2)
- **Limitations:** Not a "medical truth model" or clinically validated decision-making system. Accuracy is based solely on the MedNLI evaluation benchmark and may struggle with extremely nuanced scope qualifiers without explicit rule-based backing.
- **Access/License Metadata:** Open model (exact license defined by PubMedBERT and the authors' Hugging Face repository).
