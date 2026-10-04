"""GET /audit/{session_id} route handler."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status

from adaptive_trust_medical_rag.api.schemas import AuditEventItem, AuditResponse

log = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/audit/{session_id}",
    response_model=AuditResponse,
    summary="Retrieve audit log for a session",
    tags=["audit"],
)
async def get_audit(session_id: str, request: Request) -> AuditResponse:
    """
    Return the audit event log for a given session ID.

    **Privacy:** Events contain only query_hash (SHA-256), not raw queries.
    **Security:** Callers must supply a valid session_id they own.

    Returns an empty events list if no events are found for the session.
    """
    if len(session_id) < 8 or len(session_id) > 64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id must be 8-64 characters.",
        )

    audit_store = getattr(request.app.state, "audit_store", None)
    if audit_store is not None:
        try:
            events = await audit_store.get_events(session_id)
        except Exception as exc:
            log.error("Audit retrieval error session=%s: %s", session_id, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve audit log.",
            ) from exc
        items = [AuditEventItem(**e) for e in events]
    else:
        # No live DB: return empty (dev/test mode)
        items = []

    return AuditResponse(
        session_id=session_id,
        event_count=len(items),
        events=items,
    )

from pydantic import BaseModel
import hashlib
import json
import os as std_os


from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class ControlState(BaseModel):
    status: str
    reason: str
    reference: str

class ResearchState(BaseModel):
    dataset_integrity: ControlState
    case_order_integrity: ControlState
    frozen_retrieval: ControlState
    trust_evidence_control: ControlState
    claim_verification: ControlState
    controlled_abstention: ControlState
    prompt_freeze: ControlState
    provider_readiness: ControlState
    researcher_authorization: ControlState
    real_llm_evaluation: ControlState
    medical_evaluation_requests_total: int = 160
    medical_evaluation_requests_executed: int = 0
    protocol: str = "REAL_LLM_EVALUATION_PROTOCOL_V1_2"

@router.get(
    "/research-state",
    response_model=ResearchState,
    summary="Retrieve current research evaluation state",
    tags=["audit"],
)
async def get_research_state() -> ResearchState:
    import json
    import hashlib
    import os as std_os

    state = {}
    
    # Dataset Integrity
    dataset_path = 'experiments/manifests/v3_1_human_cases.json'
    try:
        with open(dataset_path, 'rb') as f:
            raw = f.read()
            h = hashlib.sha256(raw).hexdigest()
            data = json.loads(raw)
            cases = data if isinstance(data, list) else data.get('cases', [])
            
            if len(cases) == 80 and h == "db4013a97bed7d05803abe73cfeb477a3a82e6c75c30f860d76eed655add59dc":
                state['dataset_integrity'] = ControlState(
                    status="PASS",
                    reason="SHA256 and case count match frozen V1.2 dataset",
                    reference=dataset_path
                )
            else:
                state['dataset_integrity'] = ControlState(
                    status="BLOCKED",
                    reason="Dataset hash or count mismatch",
                    reference=dataset_path
                )
                
            # Case Order Integrity
            case_ids = [c.get('case_id') for c in cases if 'case_id' in c]
            if len(case_ids) == 80 and len(set(case_ids)) == 80:
                state['case_order_integrity'] = ControlState(
                    status="PASS",
                    reason="80 unique cases present",
                    reference=dataset_path
                )
            else:
                state['case_order_integrity'] = ControlState(
                    status="BLOCKED",
                    reason="Missing or duplicate cases",
                    reference=dataset_path
                )
    except Exception as e:
        state['dataset_integrity'] = ControlState(status="BLOCKED", reason=str(e), reference=dataset_path)
        state['case_order_integrity'] = ControlState(status="BLOCKED", reason=str(e), reference=dataset_path)

    # Prompt Freeze
    prompt_path = 'experiments/prompts/REAL_LLM_EVALUATION_PROMPT_V1_2.txt'
    try:
        with open(prompt_path, 'rb') as f:
            raw = f.read()
            h = hashlib.sha256(raw).hexdigest()
            if h == "e5aeb4fa105d30f9df23c6d3815a45d4d63c7e83b82ab30e5fbb9f4721e4301c":
                state['prompt_freeze'] = ControlState(
                    status="PASS",
                    reason="SHA256 matches frozen V1.2 prompt",
                    reference=prompt_path
                )
            else:
                state['prompt_freeze'] = ControlState(
                    status="BLOCKED",
                    reason=f"Hash mismatch: {h}",
                    reference=prompt_path
                )
    except Exception as e:
        state['prompt_freeze'] = ControlState(status="BLOCKED", reason=str(e), reference=prompt_path)

    # Frozen Retrieval
    protocol_path = 'REAL_LLM_EVALUATION_PROTOCOL_V1_2.json'
    try:
        with open(protocol_path, 'r') as f:
            proto = json.load(f)
            if proto.get('retrieval', {}).get('artifact_identity') == "FROZEN_HISTORICAL_OUTPUT":
                state['frozen_retrieval'] = ControlState(
                    status="PASS",
                    reason="Protocol confirms FROZEN_HISTORICAL_OUTPUT",
                    reference=protocol_path
                )
            else:
                state['frozen_retrieval'] = ControlState(
                    status="BLOCKED",
                    reason="Protocol retrieval artifact not set to frozen",
                    reference=protocol_path
                )
    except Exception as e:
        state['frozen_retrieval'] = ControlState(status="BLOCKED", reason=str(e), reference=protocol_path)

    # Manifest Controls
    manifest_path = 'experiments/manifests/RESEARCH_READINESS_MANIFEST_V1.json'
    try:
        with open(manifest_path, 'r') as f:
            man = json.load(f)
            for ctrl in ['trust_evidence_control', 'claim_verification', 'controlled_abstention']:
                info = man.get('controls', {}).get(ctrl, {})
                status = info.get('status', 'NOT_VALIDATED')
                state[ctrl] = ControlState(
                    status=status,
                    reason=info.get('notes', 'Missing notes'),
                    reference=info.get('validation_test', manifest_path)
                )
    except Exception as e:
        for ctrl in ['trust_evidence_control', 'claim_verification', 'controlled_abstention']:
            state[ctrl] = ControlState(status="NOT_VALIDATED", reason="Manifest missing or invalid", reference=manifest_path)

    # Provider Readiness
    if std_os.environ.get("GROQ_API_KEY"):
        state['provider_readiness'] = ControlState(
            status="CONFIGURED",
            reason="Credential exists. Connectivity not checked.",
            reference="os.environ"
        )
    else:
        state['provider_readiness'] = ControlState(
            status="NOT_CONFIGURED",
            reason="GROQ_API_KEY environment variable missing",
            reference="os.environ"
        )
        
    state['researcher_authorization'] = ControlState(
        status="PENDING",
        reason="Authorization blocked until all prerequisites pass",
        reference="Manual Researcher Action"
    )
    
    state['real_llm_evaluation'] = ControlState(
        status="NOT_STARTED",
        reason="Experiment has not been started",
        reference="experiments/runs/real-llm-v1_2/"
    )

    return ResearchState(**state)
