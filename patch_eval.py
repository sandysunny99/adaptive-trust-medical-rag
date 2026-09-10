import sys
from pathlib import Path

p = Path('src/adaptive_trust_medical_rag/security_evaluation/evaluation_conditions.py')
content = p.read_text(encoding='utf-8')

import re
content = re.sub(
    r'det\.inspect\(case\.payload\)',
    'det.inspect(case.payload, "req1")',
    content
)
content = re.sub(
    r'res\.is_safe',
    'res.decision == "ALLOW"',
    content
)
content = re.sub(
    r'res\.rejected',
    'res.decision == "BLOCK"',
    content
)

content = re.sub(
    r'det\.inspect_provenance\(case\.provenance_fixture\)',
    'det.inspect_provenance(case.provenance_fixture, "c1", "req1")',
    content
)

auth_block_old = '''            try:
                dom = self._DOMAIN_MAP.get(
                    case.target_component, EntityDomain.USER
                )
                act = self._ACTION_MAP.get(
                    case.requested_action, ActionType.READ_DATA
                )
                boundary.authorize(dom, act)
                unauthorized = True
            except PermissionError:
                blocked = True
                detected = True
                reason = "AUTHORIZATION_REJECTED"
                decision = "BLOCKED"'''

auth_block_new = '''            dom = self._DOMAIN_MAP.get(case.target_component, EntityDomain.USER)
            act = self._ACTION_MAP.get(case.requested_action, ActionType.READ_DATA)
            res = boundary.authorize(dom, act, "req1", "USER")
            if res.decision == "UNAUTHORIZED_ACTION_REJECTED":
                blocked = True
                detected = True
                reason = "AUTHORIZATION_REJECTED"
                decision = "BLOCKED"
            else:
                unauthorized = True'''

content = content.replace(auth_block_old, auth_block_new)
p.write_text(content, encoding='utf-8')
