import re
from pathlib import Path

p = Path('src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py')
c = p.read_text(encoding='utf-8')

# Remove the old step 6.5
old_step_6_5 = '''        # Phase 14: Step 6.5 - Authorization Boundary check for READ_DATA EVIDENCE
        auth_decision = self._auth_boundary.authorize(EntityDomain.EVIDENCE, ActionType.READ_DATA, request_id, security_context.principal)
        security_context.authorization_states.append(auth_decision)
        security_context.add_decision(auth_decision)
        _log("authorization_boundary", {"decision": auth_decision.decision.value, "reason": auth_decision.reason_code})
        
        if auth_decision.decision == SecurityState.UNAUTHORIZED_ACTION_REJECTED:
            return self._abstain(
                session_id=session_id,
                query_hash=query_hash,
                risk_tier=risk_tier,
                reason="Authorization Boundary Blocked Action: READ_DATA on EVIDENCE.",
                audit=audit,
                security_context=security_context
            )'''
c = c.replace(old_step_6_5, '')

# Add new step 7.5 and dummy _execute_tool
new_step_7_5 = '''        # 🚀 Step 7.5: Classify Output (Claim vs Action)
        action_match = re.search(r"\[ACTION:\\s*([A-Z_]+)\\s+ON\\s+([A-Z_]+)\]", raw_answer)
        if action_match:
            action_type_str = action_match.group(1)
            domain_str = action_match.group(2)
            try:
                action_type = ActionType(action_type_str)
                domain = EntityDomain(domain_str)
            except ValueError:
                action_type = ActionType.INVOKE_TOOL
                domain = EntityDomain.SYSTEM
            
            auth_decision = self._auth_boundary.authorize(
                domain=domain,
                action=action_type,
                request_id=request_id,
                principal=security_context.principal
            )
            security_context.authorization_states.append(auth_decision)
            security_context.add_decision(auth_decision)
            
            if auth_decision.decision == SecurityState.UNAUTHORIZED_ACTION_REJECTED:
                return self._abstain(
                    session_id=session_id,
                    query_hash=query_hash,
                    risk_tier=risk_tier,
                    reason=f"Authorization Boundary Blocked Action: {action_type.value} on {domain.value}.",
                    audit=audit,
                    security_context=security_context
                )
            else:
                self._execute_tool(action_type, domain)
                return RAGResponse(
                    session_id=session_id,
                    query_hash=query_hash,
                    risk_tier=risk_tier,
                    status=PipelineStatus.released,
                    answer=f"Tool {action_type.value} executed successfully on {domain.value}.",
                    confidence=1.0,
                    trust_scores=list(trust_scores.values()),
                    retrieved_chunk_ids=[sc.candidate.chunk_id for sc in eligible_candidates],
                    gate_decision="tool_executed",
                    verification_report=None,
                    audit_log=audit,
                    security_events=security_context.cumulative_decisions
                )
'''
c = c.replace('        # 🚀 Step 8: Answer safety gate (post-generation)', new_step_7_5 + '\n        # 🚀 Step 8: Answer safety gate (post-generation)')

helper = '''    def _execute_tool(self, action: ActionType, domain: EntityDomain) -> None:
        """Simulate tool execution for the agent action."""
        pass

    def _abstain('''
c = c.replace('    def _abstain(', helper)

p.write_text(c, encoding='utf-8')
