# TRACK_A_LOCAL_LLM_READINESS_V1

## Local Execution Capability
* **PyTorch Availability**: PRESENT (2.14.0+cpu)
* **CUDA/GPU Availability**: ABSENT (False)
* **Ollama Installation**: ABSENT
* **llama.cpp Installation**: ABSENT (Not detected in path or bindings)
* **Transformers Module**: PRESENT

## Cached HuggingFace Models
The environment contains several cached models, but all are encoder-only models used for the retrieval/embedding pipeline. There are no generative LLMs available.
* BAAI/bge-small-en-v1.5 (Embedding)
* cambridgeltl/SapBERT-from-PubMedBERT-fulltext (Entity Normalization)
* cross-encoder/ms-marco-MiniLM-L-6-v2 (Re-ranking)
* astino/gliner2.5-base-v1 (NER)
* 
cbi/MedCPT-Cross-Encoder (Re-ranking)
* pritamdeka/PubMedBERT-MNLI-MedNLI (NLI / Contradiction Detection)
* pritamdeka/S-PubMedBert-MS-MARCO (Embedding)

## Status
**NO_LOCAL_LLM_CAPABILITY**
Running a meaningful generative model (e.g., Llama 3 8B, Mistral 7B) requires either a GPU (CUDA) or a highly optimized CPU framework like llama.cpp/Ollama which are absent. Standard HuggingFace 	ransformers on CPU without quantized GGUFs would be computationally prohibitive for 50 records * 2 passes.
