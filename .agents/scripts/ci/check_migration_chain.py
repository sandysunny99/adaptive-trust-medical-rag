#!/usr/bin/env python
"""CI: Verify Alembic migration chain has no gaps or cycles."""
import sys

sys.path.insert(0, "src")

from adaptive_trust_medical_rag.database.migration_utils import (
    get_migration_chain,
    verify_migration_chain,
)

errors = verify_migration_chain()
if errors:
    print("FAIL - Migration chain errors:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)

chain = get_migration_chain()
if not chain:
    print("FAIL - Empty migration chain")
    sys.exit(1)

print(f"OK - Migration chain: {chain}")
