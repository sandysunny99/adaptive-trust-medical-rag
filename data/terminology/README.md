# Medication terminology

This folder holds offline, versioned medication-name lexicons. The live claim check (`medication_identity_violation`) uses one to recognise the medications a generated statement names. The application loads one lexicon at a time, pinned by `LEXICON_DIR` in `src/adaptive_trust_medical_rag/normalization/medication_lexicon.py`. It never downloads or updates terminology while it is running.

## Current lexicon: `rxnorm_prescribable_2026-10-05/`

- **Source:** the RxNorm Current Prescribable Content subset, published by the U.S. National Library of Medicine (NLM), release 05-Oct-2026. It holds SAB=RXNORM normalised names of active concepts.
  - Subset documentation: <https://www.nlm.nih.gov/research/umls/rxnorm/docs/prescribe.html>
- **How it was obtained:** through NLM's Prescribable RxNorm API (`https://rxnav.nlm.nih.gov/REST/Prescribe/allconcepts.json?tty=…`). The release zip host (`download.nlm.nih.gov`) did not resolve from the build machine. The API reported data version `05-Oct-2026`, the same as the monthly release `RxNorm_full_prescribe_10052026.zip`.
- **Terms:**
  - The subset needs no licence. NLM states that it "provides this subset without any licensing restrictions".
  - RxNav APIs are subject to <https://lhncbc.nlm.nih.gov/RxNav/TermsofService.html>: at most 20 requests per second, and the NLM name and logo may not be used.
  - Attribution, shown in the application footer: "This product uses publicly available data from the U.S. National Library of Medicine (NLM)."
- **Term types:** IN (ingredient), PIN (precise ingredient, for example a salt), MIN (multiple ingredients) and BN (brand name). They are kept distinct. A brand is never treated as its generic, nor a salt as its base.
- **Contents of the folder:**
  - `source/`: the API responses, byte for byte, and `version.json`.
  - `MEDICATION_LEXICON_V1.json`: single-line JSON, so its hash does not depend on line endings.
  - `MANIFEST.json`: release, endpoints, the SHA-256 of every file, counts, terms and scope.
- **Integrity:**
  - The loader refuses the lexicon unless its SHA-256 matches `MANIFEST.json`.
  - `tests/test_medication_lexicon.py` rebuilds the lexicon from `source/` and checks every recorded hash.
  - A missing, altered or malformed lexicon makes every statement fail the medication check. The check never fails open.
- **Scope:** US prescribable and many OTC drugs, active concepts only. It excludes suppressed, obsolete, foreign-only and veterinary-only drugs, and synonyms other than RxNorm's normalised names. For example, "paracetamol" and "metamizole" are absent, while "acetaminophen" and "dipyrone" are present. A name outside the lexicon and outside the drug-name suffixes is not recognised. See `experiments/nli_eval_round6/results/LEXICON_COVERAGE_V1.json`.

## Adopting a new release (manual, reviewed)

1. **Review the terms.** Read NLM's notes for the new monthly release, and confirm that the subset's terms and its source vocabularies (SAB) are unchanged.
2. **Build.** Run `python scripts/build_rxnorm_prescribable_lexicon.py --expect-release <DD-Mon-YYYY>`. It writes a **new** folder and refuses to overwrite an existing one. It stops if the API reports a different release, or if the release changes during the build.
3. **Compare** the counts and entries with the previous release. Re-run `experiments/nli_eval_round6/lexicon_coverage.py`, and review any changes to the RxCUIs in `tests/fixtures/medication_lexicon/INVENTORY_V1.json`. Changes to the inventory need a new inventory version, not an edit to V1.
4. **Point `LEXICON_DIR` at the new folder**, then run the full backend suite, the network-blocked suite and the round-6 replay.
5. **Keep the previous folder** for reproducibility. Delete nothing that a committed result refers to.
