"""Tests for drug entity normalization pipeline — no live API calls."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from adaptive_trust_medical_rag.normalization.drug_normalizer import (
    DrugEntity,
    DrugNormalizer,
    RxNormClient,
)
from adaptive_trust_medical_rag.normalization.entity_cache import EntityCache

# ─────────────────────────────────────────────────────────────────────────────
# EntityCache tests
# ─────────────────────────────────────────────────────────────────────────────


def test_entity_cache_lookup_case_insensitive() -> None:
    cache = EntityCache({"Warfarin": {"generic_name": "warfarin", "rxcui": "11289"}})
    result = cache.lookup("WARFARIN")
    assert result is not None
    assert result["rxcui"] == "11289"


def test_entity_cache_lookup_miss_returns_none() -> None:
    cache = EntityCache({})
    assert cache.lookup("unknowndrug") is None


def test_entity_cache_store_and_retrieve() -> None:
    cache = EntityCache({})
    entity = DrugEntity(
        raw_text="Coumadin",
        generic_name="warfarin",
        rxcui="11289",
        brand_name="Coumadin",
        confidence=1.0,
        source="cache",
    )
    cache.store("Coumadin", entity)
    result = cache.lookup("coumadin")
    assert result is not None
    assert result["generic_name"] == "warfarin"


def test_entity_cache_len() -> None:
    cache = EntityCache({"a": {}, "b": {}, "c": {}})
    assert len(cache) == 3


def test_entity_cache_missing_file_returns_empty(tmp_path: Path) -> None:
    non_existent = tmp_path / "no_such_file.json"
    cache = EntityCache.from_file(non_existent)
    assert len(cache) == 0


def test_entity_cache_loads_default_cache() -> None:
    """Default cache file at data/drug_entity_cache.json must exist and have entries."""
    cache = EntityCache.load_default()
    assert len(cache) >= 20, "Default cache should have at least 20 entries"


# ─────────────────────────────────────────────────────────────────────────────
# DrugEntity tests
# ─────────────────────────────────────────────────────────────────────────────


def test_drug_entity_fields() -> None:
    entity = DrugEntity(
        raw_text="warfarin",
        generic_name="warfarin",
        rxcui="11289",
        brand_name="Coumadin",
        formulation=None,
        confidence=1.0,
        source="cache",
    )
    assert entity.rxcui == "11289"
    assert entity.generic_name == "warfarin"
    assert entity.confidence == 1.0


def test_drug_entity_unresolved_defaults() -> None:
    entity = DrugEntity(raw_text="unknowndrug123")
    assert entity.rxcui is None
    assert entity.generic_name is None
    assert entity.confidence == 0.0
    assert entity.source == "unresolved"


# ─────────────────────────────────────────────────────────────────────────────
# DrugNormalizer — cache-hit tests (no API)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_normalizer_cache_hit_warfarin() -> None:
    cache = EntityCache.load_default()
    normalizer = DrugNormalizer(cache=cache, use_api=False)
    entity = await normalizer.normalize("warfarin")
    assert entity.rxcui == "11289"
    assert entity.generic_name == "warfarin"
    assert entity.confidence == 1.0
    assert entity.source == "cache"


@pytest.mark.asyncio
async def test_normalizer_brand_name_coumadin() -> None:
    cache = EntityCache.load_default()
    normalizer = DrugNormalizer(cache=cache, use_api=False)
    entity = await normalizer.normalize("Coumadin")
    assert entity.rxcui == "11289"
    assert entity.generic_name == "warfarin"
    assert entity.brand_name == "Coumadin"


@pytest.mark.asyncio
async def test_normalizer_salt_disambiguation() -> None:
    """Metoprolol tartrate and succinate must resolve to different RxCUIs."""
    cache = EntityCache.load_default()
    normalizer = DrugNormalizer(cache=cache, use_api=False)
    tartrate = await normalizer.normalize("metoprolol tartrate")
    succinate = await normalizer.normalize("metoprolol succinate")
    assert tartrate.rxcui != succinate.rxcui
    assert tartrate.formulation == "tartrate"
    assert succinate.formulation == "succinate"


@pytest.mark.asyncio
async def test_normalizer_unresolved_returns_zero_confidence() -> None:
    cache = EntityCache({})
    normalizer = DrugNormalizer(cache=cache, use_api=False)
    entity = await normalizer.normalize("XYZ_NONEXISTENT_DRUG")
    assert entity.confidence == 0.0
    assert entity.source == "unresolved"
    assert entity.rxcui is None


@pytest.mark.asyncio
async def test_normalizer_formulation_extraction() -> None:
    """Formulation keyword must be detected even when not in cache."""
    cache = EntityCache({})
    normalizer = DrugNormalizer(cache=cache, use_api=False)
    entity = await normalizer.normalize("furosemide sodium")
    assert entity.formulation == "sodium"


# ─────────────────────────────────────────────────────────────────────────────
# DrugNormalizer — mocked RxNorm API tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_normalizer_rxnorm_exact_fallback() -> None:
    """When cache misses, exact RxNorm hit should return confidence=1.0."""
    cache = EntityCache({})  # empty cache → forces API call
    mock_client = AsyncMock(spec=RxNormClient)
    mock_client.get_rxcui_exact.return_value = "99999"
    mock_client.get_generic_name.return_value = "testdrug"

    normalizer = DrugNormalizer(cache=cache, rxnorm_client=mock_client, use_api=True)
    entity = await normalizer.normalize("testdrug")

    assert entity.rxcui == "99999"
    assert entity.generic_name == "testdrug"
    assert entity.confidence == 1.0
    assert entity.source == "rxnorm_exact"


@pytest.mark.asyncio
async def test_normalizer_rxnorm_approximate_fallback() -> None:
    """When exact lookup fails, approximate match returns confidence=0.8."""
    cache = EntityCache({})
    mock_client = AsyncMock(spec=RxNormClient)
    mock_client.get_rxcui_exact.return_value = None  # exact fails
    mock_client.get_rxcui_approximate.return_value = ("88888", "approximatedrug")
    mock_client.get_generic_name.return_value = "approximatedrug"

    normalizer = DrugNormalizer(cache=cache, rxnorm_client=mock_client, use_api=True)
    entity = await normalizer.normalize("approxdrug")

    assert entity.rxcui == "88888"
    assert entity.confidence == 0.8
    assert entity.source == "rxnorm_approx"


@pytest.mark.asyncio
async def test_normalizer_batch_normalize() -> None:
    cache = EntityCache.load_default()
    normalizer = DrugNormalizer(cache=cache, use_api=False)
    drugs = ["warfarin", "ibuprofen", "aspirin"]
    results = await normalizer.normalize_batch(drugs)
    assert len(results) == 3
    assert all(e.rxcui is not None for e in results)
