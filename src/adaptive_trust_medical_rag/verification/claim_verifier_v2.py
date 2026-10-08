from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum

from transformers import pipeline

from adaptive_trust_medical_rag.verification.canonical_identity import (
    CanonicalMatchStatus,
    CanonicalRelationshipIdentity,
    compare_identity,
    extract_claim_identity,
)

_CITATION_RE = re.compile(r"\[Source\s+(\d+)\]", re.IGNORECASE)

class GateDecision(str, Enum):
    release = "release"
    qualify = "qualify"
    abstain = "abstain"

class FinalSupportState(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNSUPPORTED = "UNSUPPORTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    AMBIGUOUS = "AMBIGUOUS"

class NLIStatus(str, Enum):
    SUCCESS = "SUCCESS"
    INFERENCE_ERROR = "INFERENCE_ERROR"

@dataclass(frozen=True)
class EvidenceChunk:
    chunk_id: str
    text: str
    source_authority: float = 0.8
    citation_index: int = 0
    trust_score: float = 0.0
    missing_factors: list[str] = field(default_factory=list)
    relationship_scope: str | None = None
    relationship_identity: CanonicalRelationshipIdentity | None = None

@dataclass
class AtomicClaim:
    text: str
    parent_sentence: str
    claim_index: int
    citation_ids: list[int] = field(default_factory=list)
    is_critical: bool = False
    drug_entities: list[str] = field(default_factory=list)

@dataclass
class CitationValidation:
    citation_present: bool
    citation_resolves: bool
    citation_supports_claim: bool
    citation_contradicts_claim: bool

@dataclass
class SemanticJudgment:
    claim: AtomicClaim
    entailment: float
    contradiction: float
    neutral: float
    best_entailment_chunk_id: str | None
    best_contradiction_chunk_id: str | None
    best_neutral_chunk_id: str | None
    support_state: FinalSupportState
    citation_validation: CitationValidation
    parent_sentence_state: FinalSupportState
    nli_status: NLIStatus = NLIStatus.SUCCESS
    nli_error: str | None = None
    trust_score: float = 0.0
    missing_factors: list[str] = field(default_factory=list)
    relationship_scope: str | None = None
    canonical_identity_status: str | None = None
    canonical_identity_reason: str | None = None

@dataclass
class VerificationReportV2:
    claims: list[AtomicClaim]
    judgments: list[SemanticJudgment]
    grounding_ratio: float
    decision: GateDecision
    explanation: str

def decompose_into_claims(answer: str) -> list[AtomicClaim]:
    sentence_re = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
    raw_sentences = sentence_re.split(answer.strip())
    claims = []
    clause_re = re.compile(r",\s*(?:and\s+therefore|and|but|therefore|however|because|while)\s+", re.IGNORECASE)

    claim_idx = 0
    for sent in raw_sentences:
        sent = sent.strip()
        if not sent or len(sent) < 10:
            continue

        clauses = clause_re.split(sent)
        for clause in clauses:
            clause = clause.strip()
            if len(clause) < 5:
                continue

            citation_ids = [int(m) for m in _CITATION_RE.findall(clause)]
            if not citation_ids:
                citation_ids = [int(m) for m in _CITATION_RE.findall(sent)]

            claims.append(
                AtomicClaim(
                    text=clause,
                    parent_sentence=sent,
                    claim_index=claim_idx,
                    citation_ids=citation_ids,
                    is_critical=False,
                    drug_entities=[]
                )
            )
            claim_idx += 1
    return claims

class NLIInferenceError(Exception):
    pass

class ClaimVerifierV2:
    def __init__(self, model_id: str = "pritamdeka/PubMedBERT-MNLI-MedNLI", revision: str = "f1b6ce2e0d49f295b4cbcdc56c01b5fab6d068ab", cache_dir: str = None):
        kwargs = {}
        if cache_dir:
            kwargs["model_kwargs"] = {"cache_dir": cache_dir}
            kwargs["tokenizer_kwargs"] = {"cache_dir": cache_dir}
        if os.environ.get("TESTING") == "1":
            class MockClassifier:
                class MockConfig:
                    id2label = {0: "entailment", 1: "neutral", 2: "contradiction"}
                def __init__(self):
                    self.model = type("MockModel", (), {"config": self.MockConfig()})()
                def __call__(self, text, **kwargs):
                    return [[{"label": "entailment", "score": 0.99}, {"label": "neutral", "score": 0.01}, {"label": "contradiction", "score": 0.0}]]
            self.classifier = MockClassifier()
        else:
            self.classifier = pipeline("text-classification", model=model_id, revision=revision, top_k=None, **kwargs)


        self.id2label = self.classifier.model.config.id2label
        self.label_map = {}
        for k, v in self.id2label.items():
            vl = v.lower()
            if "entail" in vl: self.label_map[vl] = "entailment"
            elif "contradict" in vl: self.label_map[vl] = "contradiction"
            elif "neutral" in vl: self.label_map[vl] = "neutral"
            else: self.label_map[vl] = vl

        if not {"entailment", "contradiction", "neutral"}.issubset(set(self.label_map.values())):
            raise RuntimeError(f"Cannot unambiguously map model labels: {self.id2label}")

    def _evaluate_pair(self, premise: str, hypothesis: str) -> dict:
        inputs = {"text": premise, "text_pair": hypothesis}
        try:
            output = self.classifier(inputs)
            if isinstance(output, list) and isinstance(output[0], list):
                output = output[0]
            if not isinstance(output, list):
                output = [output]
        except Exception as e:
            raise NLIInferenceError(f"NLI pair inference failed: {e}")

        scores = {self.label_map[lbl["label"].lower()]: lbl["score"] for lbl in output}
        return scores

    def _scope_protection(self, chunk: EvidenceChunk | None, hypothesis: str) -> bool:
        if not chunk:
            return False
        h_lower = hypothesis.lower()
        p_lower = chunk.text.lower()
        interaction_scope = "clinically significant" in p_lower
        mechanism_scope = "pharmacokinetic" in p_lower
        polarity_neg = "no " in p_lower or "not " in p_lower

        if polarity_neg and interaction_scope and mechanism_scope:
            overclaims = [
                "completely safe", "no interaction of any kind",
                "essentially no interaction", "safe together",
                "no meaningful interaction exists", "no safety concerns",
                "does not interact"
            ]
            if any(oc in h_lower for oc in overclaims) and ("pharmacokinetic" not in h_lower or "clinically significant" not in h_lower):
                return True
        return False

    def _map_to_state(self, max_ent: float, max_con: float, max_neu: float, best_ent_chunk: EvidenceChunk|None, best_con_chunk: EvidenceChunk|None, scope_violated: bool) -> FinalSupportState:
        if scope_violated:
            return FinalSupportState.UNSUPPORTED

        if max_con > 0.4 and max_ent > 0.4:
            if max_con - max_ent >= 0.3:
                return FinalSupportState.CONTRADICTED
            if best_ent_chunk != best_con_chunk:
                return FinalSupportState.AMBIGUOUS
            if abs(max_ent - max_con) < 0.1:
                return FinalSupportState.AMBIGUOUS

        if max_con > max_ent and max_con > max_neu:
            return FinalSupportState.CONTRADICTED

        if max_ent > max_con and max_ent > max_neu:
            return FinalSupportState.SUPPORTED

        if max_neu > 0.7:
            return FinalSupportState.INSUFFICIENT_EVIDENCE

        return FinalSupportState.UNSUPPORTED

    def _determine_parent_state(self, atomic_states: list[FinalSupportState]) -> FinalSupportState:
        if all(s == FinalSupportState.SUPPORTED for s in atomic_states):
            return FinalSupportState.SUPPORTED
        if any(s == FinalSupportState.CONTRADICTED for s in atomic_states):
            return FinalSupportState.CONTRADICTED
        if any(s == FinalSupportState.AMBIGUOUS for s in atomic_states):
            return FinalSupportState.AMBIGUOUS
        if FinalSupportState.SUPPORTED in atomic_states and any(s in (FinalSupportState.UNSUPPORTED, FinalSupportState.INSUFFICIENT_EVIDENCE) for s in atomic_states):
            return FinalSupportState.PARTIALLY_SUPPORTED
        if all(s == FinalSupportState.INSUFFICIENT_EVIDENCE for s in atomic_states):
            return FinalSupportState.INSUFFICIENT_EVIDENCE
        return FinalSupportState.UNSUPPORTED

    def verify(self, answer: str, evidence: list[EvidenceChunk], risk_tier="R1", critical_claim_indices: list[int] = None, drug_rxcui_map: dict[str, str] | None = None) -> VerificationReportV2:
        if critical_claim_indices is None:
            critical_claim_indices = []

        claims = decompose_into_claims(answer)

        for claim in claims:
            if claim.claim_index in critical_claim_indices:
                claim.is_critical = True

        if not claims:
            return VerificationReportV2([], [], 0.0, GateDecision.abstain, "No claims.")

        judgments = []
        for claim in claims:
            max_ent = max_con = max_neu = 0.0
            best_ent_chunk = best_con_chunk = best_neu_chunk = None

            nli_status = NLIStatus.SUCCESS
            nli_errors = []

            citation_present = len(claim.citation_ids) > 0
            cited_chunks = [c for c in evidence if c.citation_index in claim.citation_ids]
            citation_resolves = citation_present and len(cited_chunks) > 0

            chunk_evals = {}
            for chunk in evidence:
                try:
                    scores = self._evaluate_pair(chunk.text, claim.text)
                    chunk_evals[chunk.chunk_id] = scores
                except NLIInferenceError as e:
                    chunk_evals[chunk.chunk_id] = {"entailment": 0.0, "contradiction": 0.0, "neutral": 1.0}
                    nli_status = NLIStatus.INFERENCE_ERROR
                    nli_errors.append(str(e))

                ent = chunk_evals[chunk.chunk_id].get("entailment", 0.0)
                con = chunk_evals[chunk.chunk_id].get("contradiction", 0.0)
                neu = chunk_evals[chunk.chunk_id].get("neutral", 0.0)

                if ent > max_ent:
                    max_ent = ent
                    best_ent_chunk = chunk
                if con > max_con:
                    max_con = con
                    best_con_chunk = chunk
                if neu > max_neu:
                    max_neu = neu
                    best_neu_chunk = chunk

            scope_violated = self._scope_protection(best_ent_chunk, claim.text)
            global_state = self._map_to_state(max_ent, max_con, max_neu, best_ent_chunk, best_con_chunk, scope_violated)

            citation_supports = False
            citation_contradicts = False
            claim_missing_factors = []
            claim_trust_score = 0.0
            claim_relationship_scope = None

            if citation_resolves:
                cit_ent = max([chunk_evals[c.chunk_id].get("entailment", 0.0) for c in cited_chunks])
                cit_con = max([chunk_evals[c.chunk_id].get("contradiction", 0.0) for c in cited_chunks])
                cit_scope_violated = any(self._scope_protection(c, claim.text) for c in cited_chunks)

                if cit_ent > max(cit_con, max([chunk_evals[c.chunk_id].get("neutral", 0.0) for c in cited_chunks])) and not cit_scope_violated:
                    citation_supports = True
                if cit_con > max(cit_ent, max([chunk_evals[c.chunk_id].get("neutral", 0.0) for c in cited_chunks])):
                    citation_contradicts = True

                factors_set = set()
                for c in cited_chunks:
                    factors_set.update(c.missing_factors)
                claim_missing_factors = sorted(list(factors_set))

                claim_trust_score = min([c.trust_score for c in cited_chunks]) if cited_chunks else 0.0
                scopes = [c.relationship_scope for c in cited_chunks if c.relationship_scope]
                if scopes:
                    claim_relationship_scope = scopes[0]

            # Enforce Provenance (P0)
            if citation_present:
                if citation_contradicts:
                    state = FinalSupportState.CONTRADICTED
                elif not citation_resolves:
                    state = FinalSupportState.UNSUPPORTED
                elif not citation_supports:
                    state = FinalSupportState.UNSUPPORTED
                elif claim_relationship_scope in ("NO_RELEVANT_RELATION", "UNSUPPORTED", "CONTRADICTED", "ENTITY_PAIR_MISMATCH", "UNVERIFIABLE"):
                    state = FinalSupportState.UNSUPPORTED
                else:
                    state = global_state
            else:
                state = FinalSupportState.UNSUPPORTED

            # Canonical Relationship Identity Verification
            canonical_id_status = None
            canonical_id_reason = None
            if drug_rxcui_map is not None:
                # Extract source canonical identity from best supporting evidence
                source_identities = [
                    c.relationship_identity for c in (cited_chunks if cited_chunks else evidence)
                    if c.relationship_identity is not None
                ]
                source_identity = source_identities[0] if source_identities else None

                # Extract claim canonical identity
                claim_identity = extract_claim_identity(claim.text, drug_rxcui_map)

                # Deterministic comparison
                id_status, id_reason = compare_identity(source_identity, claim_identity)
                canonical_id_status = id_status.value
                canonical_id_reason = id_reason

                # Canonical identity enforcement: mismatch or ambiguity overrides
                if id_status == CanonicalMatchStatus.MISMATCH:
                    state = FinalSupportState.UNSUPPORTED
                elif id_status == CanonicalMatchStatus.AMBIGUOUS:
                    state = FinalSupportState.UNSUPPORTED
                elif id_status == CanonicalMatchStatus.UNAVAILABLE:
                    state = FinalSupportState.UNSUPPORTED
                # MATCH: state remains as determined by NLI/citation/provenance

            judgments.append(
                SemanticJudgment(
                    claim=claim,
                    entailment=max_ent,
                    contradiction=max_con,
                    neutral=max_neu,
                    best_entailment_chunk_id=best_ent_chunk.chunk_id if best_ent_chunk else None,
                    best_contradiction_chunk_id=best_con_chunk.chunk_id if best_con_chunk else None,
                    best_neutral_chunk_id=best_neu_chunk.chunk_id if best_neu_chunk else None,
                    support_state=state,
                    citation_validation=CitationValidation(
                        citation_present=citation_present,
                        citation_resolves=citation_resolves,
                        citation_supports_claim=citation_supports,
                        citation_contradicts_claim=citation_contradicts
                    ),
                    parent_sentence_state=FinalSupportState.UNSUPPORTED,
                    nli_status=nli_status,
                    nli_error="; ".join(nli_errors) if nli_errors else None,
                    trust_score=claim_trust_score,
                    missing_factors=claim_missing_factors,
                    relationship_scope=claim_relationship_scope,
                    canonical_identity_status=canonical_id_status,
                    canonical_identity_reason=canonical_id_reason
                )
            )

        parent_groupings = {}
        for j in judgments:
            parent_groupings.setdefault(j.claim.parent_sentence, []).append(j)

        for parent, j_list in parent_groupings.items():
            parent_state = self._determine_parent_state([j.support_state for j in j_list])
            for j in j_list:
                j.parent_sentence_state = parent_state

        grounded = sum(1 for j in judgments if j.support_state in (FinalSupportState.SUPPORTED, FinalSupportState.PARTIALLY_SUPPORTED))
        grounding_ratio = grounded / len(claims) if claims else 0.0

        states = [j.support_state for j in judgments]
        is_criticals = [j.claim.is_critical for j in judgments]

        if any(s == FinalSupportState.CONTRADICTED for s in states):
            decision = GateDecision.abstain
        elif any(s == FinalSupportState.AMBIGUOUS for s in states):
            decision = GateDecision.abstain
        elif any(s == FinalSupportState.INSUFFICIENT_EVIDENCE and c for s, c in zip(states, is_criticals)):
            decision = GateDecision.abstain
        elif any(s == FinalSupportState.UNSUPPORTED and c for s, c in zip(states, is_criticals)):
            decision = GateDecision.abstain
        elif all(s == FinalSupportState.SUPPORTED for s in states):
            decision = GateDecision.release
        elif all(s in (FinalSupportState.SUPPORTED, FinalSupportState.PARTIALLY_SUPPORTED) for s in states):
            decision = GateDecision.qualify
        elif any(s in (FinalSupportState.UNSUPPORTED, FinalSupportState.INSUFFICIENT_EVIDENCE) for s in states):
            decision = GateDecision.qualify
        else:
            decision = GateDecision.abstain

        return VerificationReportV2(claims, judgments, grounding_ratio, decision, f"Gate policy matched: {decision.value}")
