"""Drug entity normalization pipeline.

Resolution order:
    1. Local exact-match cache (brand → generic → RxCUI)
    2. RxNorm REST API exact lookup  (/rxcui.json?name=...)
    3. RxNorm REST API approximate   (/approximateTerm.json?term=...)
    4. Fallback: return unresolved entity with confidence=0.0

Rules enforced (drug-entity-normalization SKILL.md):
    - Never conflate Drug A with Drug B (different RxCUIs).
    - Salt / formulation disambiguation is explicit (Tartrate ≠ Succinate).
    - If only a drug class is resolved (no RxCUI), attribution confidence is
      discounted to 0.5 unless the risk class explicitly permits class-level
      generalisation.

Privacy: no PHI is processed here — only drug name strings.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from adaptive_trust_medical_rag.normalization.entity_cache import EntityCache

logger = logging.getLogger(__name__)

RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"
_REQUEST_TIMEOUT = 5.0  # seconds


# ─────────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class DrugEntity:
    """Normalised drug entity record."""

    raw_text: str
    """Original text extracted from the query or document."""

    generic_name: str | None = None
    """Canonical generic (INN) name resolved from cache or RxNorm."""

    rxcui: str | None = None
    """RxNorm Concept Unique Identifier — primary pharmacological anchor."""

    brand_name: str | None = None
    """Brand/trade name, if supplied in raw_text."""

    atc_code: str | None = None
    """WHO ATC classification code (populated at Phase 10 via enrichment)."""

    formulation: str | None = None
    """Salt, ester, or dosage-form qualifier (e.g., 'tartrate', 'succinate')."""

    confidence: float = 0.0
    """
    Resolution confidence:
        1.0 — exact RxCUI match (cache or API exact)
        0.8 — approximate RxNorm match
        0.5 — drug class only (no specific RxCUI)
        0.0 — unresolved
    """

    source: str = "unresolved"
    """Which resolver produced this: 'cache', 'rxnorm_exact', 'rxnorm_approx', 'unresolved'."""

    metadata: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# RxNorm REST client
# ─────────────────────────────────────────────────────────────────────────────


class RxNormClient:
    """Thin async wrapper around the NLM RxNorm REST API."""

    def __init__(self, timeout: float = _REQUEST_TIMEOUT) -> None:
        self._timeout = timeout

    async def get_rxcui_exact(self, drug_name: str) -> str | None:
        """Query /rxcui.json?name=<drug_name>&search=0 (exact match only)."""
        url = f"{RXNORM_BASE_URL}/rxcui.json"
        params = {"name": drug_name, "search": 0}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                rxcui = data.get("idGroup", {}).get("rxnormId", [])
                return rxcui[0] if rxcui else None
        except httpx.HTTPError as exc:
            logger.warning("RxNorm exact lookup failed for '%s': %s", drug_name, exc)
            return None

    async def get_rxcui_approximate(self, drug_name: str) -> tuple[str | None, str | None]:
        """Query /approximateTerm.json for fuzzy matching.

        Returns (rxcui, matched_name) or (None, None).
        """
        url = f"{RXNORM_BASE_URL}/approximateTerm.json"
        params = {"term": drug_name, "maxEntries": 1}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                candidates = (
                    data.get("approximateGroup", {}).get("candidate", [])
                )
                if candidates:
                    best = candidates[0]
                    return best.get("rxcui"), best.get("name")
                return None, None
        except httpx.HTTPError as exc:
            logger.warning("RxNorm approx lookup failed for '%s': %s", drug_name, exc)
            return None, None

    async def get_generic_name(self, rxcui: str) -> str | None:
        """Resolve generic (INN) name from RxCUI via /rxconcept/{rxcui}/allProperties."""
        url = f"{RXNORM_BASE_URL}/rxcui/{rxcui}/allProperties.json"
        params = {"prop": "Names"}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                props = data.get("propConceptGroup", {}).get("propConcept", [])
                for prop in props:
                    if prop.get("propName") == "RxNorm Name":
                        return prop.get("propValue")
                return None
        except httpx.HTTPError as exc:
            logger.warning("RxNorm name resolution failed for rxcui '%s': %s", rxcui, exc)
            return None


# ─────────────────────────────────────────────────────────────────────────────
# Main normalizer
# ─────────────────────────────────────────────────────────────────────────────


class DrugNormalizer:
    """Orchestrates the 4-step drug entity resolution pipeline.

    Resolution order: local cache → RxNorm exact → RxNorm approximate → fallback.
    """

    def __init__(
        self,
        cache: EntityCache | None = None,
        rxnorm_client: RxNormClient | None = None,
        use_api: bool = True,
    ) -> None:
        self._cache = cache or EntityCache.load_default()
        self._rxnorm = rxnorm_client or RxNormClient()
        self._use_api = use_api

    def _extract_formulation(self, text: str) -> str | None:
        """Detect salt / formulation qualifiers in the drug text string."""
        formulation_keywords = [
            "tartrate",
            "succinate",
            "hydrochloride",
            "hcl",
            "sodium",
            "potassium",
            "phosphate",
            "acetate",
            "sulfate",
            "maleate",
            "besylate",
            "mesylate",
            "fumarate",
            "citrate",
            "gluconate",
        ]
        lower = text.lower()
        for kw in formulation_keywords:
            if kw in lower:
                return kw
        return None

    async def normalize(self, raw_text: str) -> DrugEntity:
        """Resolve a raw drug name string to a DrugEntity."""
        text = raw_text.strip()
        formulation = self._extract_formulation(text)

        # Step 1: Local cache
        cached = self._cache.lookup(text)
        if cached:
            return DrugEntity(
                raw_text=raw_text,
                generic_name=cached.get("generic_name"),
                rxcui=cached.get("rxcui"),
                brand_name=cached.get("brand_name"),
                formulation=formulation or cached.get("formulation"),
                confidence=1.0,
                source="cache",
                metadata={"cache_key": text},
            )

        if not self._use_api:
            return DrugEntity(raw_text=raw_text, formulation=formulation, confidence=0.0)

        # Step 2: RxNorm exact
        rxcui = await self._rxnorm.get_rxcui_exact(text)
        if rxcui:
            generic_name = await self._rxnorm.get_generic_name(rxcui)
            entity = DrugEntity(
                raw_text=raw_text,
                rxcui=rxcui,
                generic_name=generic_name or text,
                formulation=formulation,
                confidence=1.0,
                source="rxnorm_exact",
            )
            self._cache.store(text, entity)
            return entity

        # Step 3: RxNorm approximate
        approx_rxcui, approx_name = await self._rxnorm.get_rxcui_approximate(text)
        if approx_rxcui:
            generic_name = await self._rxnorm.get_generic_name(approx_rxcui)
            entity = DrugEntity(
                raw_text=raw_text,
                rxcui=approx_rxcui,
                generic_name=generic_name or approx_name or text,
                formulation=formulation,
                confidence=0.8,
                source="rxnorm_approx",
                metadata={"matched_name": approx_name},
            )
            self._cache.store(text, entity)
            return entity

        # Step 4: Unresolved fallback
        logger.warning("Could not resolve drug entity: '%s'", text)
        return DrugEntity(raw_text=raw_text, formulation=formulation, confidence=0.0)

    async def normalize_batch(self, texts: list[str]) -> list[DrugEntity]:
        """Resolve multiple drug names concurrently."""
        return list(await asyncio.gather(*[self.normalize(t) for t in texts]))
