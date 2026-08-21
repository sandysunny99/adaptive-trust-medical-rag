"""
Tests for Phase 16 - Synthetic Dataset Generator & Loader.

Covers: generate_dataset (dev/val), PHI verification, save/load
        round-trip, fixture integrity, query type distribution,
        risk tier coverage, leakage prevention.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adaptive_trust_medical_rag.evaluation.dataset_generator import (
    generate_dataset,
    load_dataset,
    save_dataset,
    verify_no_phi,
)
from adaptive_trust_medical_rag.evaluation.evaluator import (
    DatasetSplit,
    EvalDataset,
    QueryType,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path("tests/fixtures")
DEV_FIXTURE = FIXTURES_DIR / "dev_dataset_v1.jsonl"
VAL_FIXTURE = FIXTURES_DIR / "val_dataset_v1.jsonl"


class TestGenerateDatasetDev:
    """Tests for generate_dataset(DatasetSplit.dev)."""

    def test_returns_100_cases(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        assert len(ds.cases) == 100

    def test_all_cases_in_dev_split(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        assert all(c.split == DatasetSplit.dev for c in ds.cases)

    def test_has_factual_cases(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        assert any(c.query_type == QueryType.factual for c in ds.cases)

    def test_has_injection_cases(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        assert any(c.query_type == QueryType.injection for c in ds.cases)

    def test_has_unanswerable_cases(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        assert any(c.query_type == QueryType.unanswerable for c in ds.cases)

    def test_has_ambiguous_cases(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        assert any(c.query_type == QueryType.ambiguous for c in ds.cases)

    def test_injection_cases_expect_abstain(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        injections = [c for c in ds.cases if c.query_type == QueryType.injection]
        assert all(c.expected_abstain for c in injections)

    def test_unanswerable_cases_expect_abstain(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        unanswerable = [c for c in ds.cases if c.query_type == QueryType.unanswerable]
        assert all(c.expected_abstain for c in unanswerable)

    def test_covers_all_risk_tiers(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        tiers = {c.risk_tier for c in ds.cases}
        for tier in ["R0", "R1", "R2", "R3"]:
            assert tier in tiers, f"Missing risk tier {tier}"

    def test_factual_cases_have_drug_names(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        factual = [c for c in ds.cases if c.query_type == QueryType.factual]
        assert all(len(c.expected_drugs) > 0 for c in factual)

    def test_case_ids_unique(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        ids = [c.case_id for c in ds.cases]
        assert len(ids) == len(set(ids))

    def test_deterministic_same_seed(self) -> None:
        ds1 = generate_dataset(DatasetSplit.dev, seed=42)
        ds2 = generate_dataset(DatasetSplit.dev, seed=42)
        ids1 = sorted(c.case_id for c in ds1.cases)
        ids2 = sorted(c.case_id for c in ds2.cases)
        assert ids1 == ids2

    def test_different_seeds_different_order(self) -> None:
        ds1 = generate_dataset(DatasetSplit.dev, seed=1)
        ds2 = generate_dataset(DatasetSplit.dev, seed=99)
        # Same case IDs (content same), but different order
        ids1 = [c.case_id for c in ds1.cases]
        ids2 = [c.case_id for c in ds2.cases]
        assert ids1 != ids2  # order should differ

    def test_name_contains_dev(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        assert "dev" in ds.name

    def test_version_set(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        assert ds.version != ""

    def test_r3_cases_are_r3_tier(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        # R3 queries should be classified as R3 risk tier
        r3_cases = [c for c in ds.cases if c.risk_tier == "R3"]
        assert len(r3_cases) > 0

    def test_no_test_split_cases(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        assert all(c.split != DatasetSplit.test for c in ds.cases)


class TestGenerateDatasetVal:
    """Tests for generate_dataset(DatasetSplit.val)."""

    def test_returns_200_cases(self) -> None:
        ds = generate_dataset(DatasetSplit.val)
        assert len(ds.cases) == 200

    def test_all_cases_in_val_split(self) -> None:
        ds = generate_dataset(DatasetSplit.val)
        assert all(c.split == DatasetSplit.val for c in ds.cases)

    def test_val_larger_than_dev(self) -> None:
        dev = generate_dataset(DatasetSplit.dev)
        val = generate_dataset(DatasetSplit.val)
        assert len(val.cases) > len(dev.cases)

    def test_name_contains_val(self) -> None:
        ds = generate_dataset(DatasetSplit.val)
        assert "val" in ds.name


class TestGenerateDatasetErrors:
    def test_smoke_split_raises(self) -> None:
        with pytest.raises(ValueError, match="smoke"):
            generate_dataset(DatasetSplit.smoke)

    def test_test_split_raises(self) -> None:
        with pytest.raises(ValueError):
            generate_dataset(DatasetSplit.test)


class TestVerifyNoPhi:
    def test_dev_dataset_zero_violations(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        assert verify_no_phi(ds) == []

    def test_val_dataset_zero_violations(self) -> None:
        ds = generate_dataset(DatasetSplit.val)
        assert verify_no_phi(ds) == []

    def test_detects_ssn_pattern(self) -> None:
        from adaptive_trust_medical_rag.evaluation.evaluator import EvalCase
        bad_case = EvalCase(
            case_id="test001",
            query="Patient SSN: 123-45-6789",
            split=DatasetSplit.dev,
            query_type=QueryType.factual,
        )
        ds = EvalDataset(name="bad", cases=[bad_case])
        violations = verify_no_phi(ds)
        assert len(violations) > 0

    def test_clean_dataset_no_violations(self) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        violations = verify_no_phi(ds)
        assert violations == [], f"PHI detected: {violations}"


class TestSaveLoadRoundTrip:
    def test_save_creates_file(self, tmp_path: Path) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        out = tmp_path / "test_dev.jsonl"
        save_dataset(ds, out)
        assert out.exists()

    def test_load_returns_same_count(self, tmp_path: Path) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        out = tmp_path / "test_dev.jsonl"
        save_dataset(ds, out)
        loaded = load_dataset(out)
        assert len(loaded.cases) == len(ds.cases)

    def test_load_preserves_case_ids(self, tmp_path: Path) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        out = tmp_path / "test_dev.jsonl"
        save_dataset(ds, out)
        loaded = load_dataset(out)
        orig_ids = sorted(c.case_id for c in ds.cases)
        load_ids = sorted(c.case_id for c in loaded.cases)
        assert orig_ids == load_ids

    def test_load_preserves_query_text(self, tmp_path: Path) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        out = tmp_path / "test_dev.jsonl"
        save_dataset(ds, out)
        loaded = load_dataset(out)
        orig_q = {c.case_id: c.query for c in ds.cases}
        load_q = {c.case_id: c.query for c in loaded.cases}
        assert orig_q == load_q

    def test_load_preserves_expected_abstain(self, tmp_path: Path) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        out = tmp_path / "test_dev.jsonl"
        save_dataset(ds, out)
        loaded = load_dataset(out)
        orig = {c.case_id: c.expected_abstain for c in ds.cases}
        load_map = {c.case_id: c.expected_abstain for c in loaded.cases}
        assert orig == load_map

    def test_load_preserves_risk_tier(self, tmp_path: Path) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        out = tmp_path / "test_dev.jsonl"
        save_dataset(ds, out)
        loaded = load_dataset(out)
        orig = {c.case_id: c.risk_tier for c in ds.cases}
        load_map = {c.case_id: c.risk_tier for c in loaded.cases}
        assert orig == load_map

    def test_load_preserves_expected_drugs(self, tmp_path: Path) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        out = tmp_path / "test_dev.jsonl"
        save_dataset(ds, out)
        loaded = load_dataset(out)
        orig = {c.case_id: sorted(c.expected_drugs) for c in ds.cases}
        load_map = {c.case_id: sorted(c.expected_drugs) for c in loaded.cases}
        assert orig == load_map

    def test_load_preserves_name(self, tmp_path: Path) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        out = tmp_path / "test_dev.jsonl"
        save_dataset(ds, out)
        loaded = load_dataset(out)
        assert loaded.name == ds.name

    def test_load_nonexistent_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_dataset(tmp_path / "ghost.jsonl")

    def test_file_is_valid_jsonl(self, tmp_path: Path) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        out = tmp_path / "test_dev.jsonl"
        save_dataset(ds, out)
        lines = out.read_text().strip().split("\n")
        for line in lines:
            json.loads(line)  # raises on invalid JSON

    def test_meta_header_present(self, tmp_path: Path) -> None:
        ds = generate_dataset(DatasetSplit.dev)
        out = tmp_path / "test_dev.jsonl"
        save_dataset(ds, out)
        first_line = out.read_text().split("\n")[0]
        meta = json.loads(first_line)
        assert meta.get("_meta") is True
        assert meta["n_cases"] == len(ds.cases)


class TestFrozenFixtures:
    """Verify the committed fixture files have expected properties."""

    def test_dev_fixture_exists(self) -> None:
        assert DEV_FIXTURE.exists(), "tests/fixtures/dev_dataset_v1.jsonl missing"

    def test_val_fixture_exists(self) -> None:
        assert VAL_FIXTURE.exists(), "tests/fixtures/val_dataset_v1.jsonl missing"

    def test_dev_fixture_loads_100_cases(self) -> None:
        ds = load_dataset(DEV_FIXTURE)
        assert len(ds.cases) == 100

    def test_val_fixture_loads_200_cases(self) -> None:
        ds = load_dataset(VAL_FIXTURE)
        assert len(ds.cases) == 200

    def test_dev_fixture_phi_free(self) -> None:
        ds = load_dataset(DEV_FIXTURE)
        assert verify_no_phi(ds) == []

    def test_val_fixture_phi_free(self) -> None:
        ds = load_dataset(VAL_FIXTURE)
        assert verify_no_phi(ds) == []

    def test_dev_no_test_split_leakage(self) -> None:
        dev = load_dataset(DEV_FIXTURE)
        dev_ids = {c.case_id for c in dev.cases}
        # No overlap with smoke (make_smoke_dataset)
        from adaptive_trust_medical_rag.evaluation.evaluator import make_smoke_dataset
        smoke = make_smoke_dataset()
        smoke_ids = {c.case_id for c in smoke.cases}
        assert dev_ids.isdisjoint(smoke_ids), "Dev/smoke overlap detected!"

    def test_dev_val_no_overlap(self) -> None:
        dev = load_dataset(DEV_FIXTURE)
        val = load_dataset(VAL_FIXTURE)
        dev_ids = {c.case_id for c in dev.cases}
        val_ids = {c.case_id for c in val.cases}
        assert dev_ids.isdisjoint(val_ids), "Dev/val case_id overlap!"
