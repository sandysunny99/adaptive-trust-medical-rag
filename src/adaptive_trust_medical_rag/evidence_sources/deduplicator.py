"""Multi-Source Evidence Deduplicator

Project: Adaptive Trust-Aware Medical RAG
Component: EvidenceDeduplicator

Deduplicates evidence candidates across PMID -> PMCID -> DOI -> NCT ID -> RxCUI -> Title/Year
and generates unique canonical document identifiers.
"""

from __future__ import annotations

import re
from typing import Any


class EvidenceDeduplicator:
    """Deduplicates evidence records from multiple external providers."""

    def deduplicate(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Deduplicate records list and assign canonical document IDs."""
        seen_keys: set[str] = set()
        deduped: list[dict[str, Any]] = []

        for rec in records:
            canon_id, key = self._extract_dedup_key(rec)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            rec_copy = dict(rec)
            rec_copy["canonical_document_id"] = canon_id
            deduped.append(rec_copy)

        return deduped

    def _extract_dedup_key(self, rec: dict[str, Any]) -> tuple[str, str]:
        """Extract canonical ID and unique deduplication key."""
        ids = rec.get("identifiers", {})
        pmid = ids.get("pmid")
        pmcid = ids.get("pmcid")
        doi = ids.get("doi")
        rxcui = ids.get("rxcui")
        nct_id = ids.get("nct_id")

        if pmid:
            return f"MED-PMID-{pmid}", f"pmid:{pmid}"
        if pmcid:
            return f"PMC-{pmcid}", f"pmcid:{pmcid}"
        if doi:
            clean_doi = doi.replace("/", "_")
            return f"DOI-{clean_doi}", f"doi:{doi.lower()}"
        if nct_id:
            return f"NCT-{nct_id}", f"nct:{nct_id}"
        if rxcui:
            return f"RXCUI-{rxcui}", f"rxcui:{rxcui}"

        title = rec.get("title", "")
        clean_title = re.sub(r"[^\w\s]", "", title.lower()).strip()
        pub_year = str(rec.get("publication_date", ""))[:4]
        fallback_key = f"title:{clean_title}:{pub_year}"
        return f"DOC-{hash(fallback_key) & 0xFFFFFFFF:08x}", fallback_key
