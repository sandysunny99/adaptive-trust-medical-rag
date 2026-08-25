# API Adapter Contract Specification

**Specification Version:** `1.0.0`  
**Project:** Adaptive Trust-Aware Medical RAG  

---

## 1. Abstract Base Interface (`EvidenceSourceAdapter`)

Every external evidence adapter must subclass `EvidenceSourceAdapter` and implement 5 core methods:

```python
class EvidenceSourceAdapter(ABC):
    @abstractmethod
    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search external evidence provider for candidate records."""
        ...

    @abstractmethod
    def fetch(self, source_id: str) -> dict[str, Any]:
        """Fetch raw record payload by provider identifier."""
        ...

    @abstractmethod
    def normalize(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize raw provider JSON into standard schema."""
        ...

    @abstractmethod
    def provenance(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Extract request/response provenance & telemetry metadata."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Ping provider endpoint to verify health & availability."""
        ...
```

---

## 2. Normalized Record Schema

All adapters MUST normalize raw API JSON payloads into the standard dictionary schema:

```json
{
  "source_type": "BIOMEDICAL_LITERATURE",
  "provider": "pubmed",
  "source_id": "34289871",
  "title": "Metformin and Glucose Metabolism in Type 2 Diabetes",
  "authors": ["Smith A", "Jones B"],
  "publication_date": "2021-05-15",
  "url": "https://pubmed.ncbi.nlm.nih.gov/34289871/",
  "abstract": "Metformin decreases hepatic glucose production...",
  "full_text_url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8234567/",
  "identifiers": {
    "pmid": "34289871",
    "pmcid": "PMC8234567",
    "doi": "10.1016/j.jaut.2021.102650",
    "rxcui": null
  },
  "provenance": {
    "provider": "pubmed",
    "endpoint": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
    "http_method": "GET",
    "request_started_at": "2026-08-23T18:20:00Z",
    "response_received_at": "2026-08-23T18:20:00.250Z",
    "latency_ms": 250.0,
    "status_code": 200,
    "api_version": "2.0"
  },
  "retrieved_at": "2026-08-23T18:20:00Z",
  "source_updated_at": "2021-05-15T00:00:00Z",
  "raw_response_hash": "a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef"
}
```

---

## 3. Cryptographic Hash Requirements

- **Canonical Serialization:** Raw JSON response payloads must be serialized using `json.dumps(payload, sort_keys=True, separators=(",", ":"))`.
- **SHA-256 Digest:** The SHA-256 digest (`raw_response_hash`) must be a 64-character lowercase hex string (`^[0-9a-f]{64}$`).
