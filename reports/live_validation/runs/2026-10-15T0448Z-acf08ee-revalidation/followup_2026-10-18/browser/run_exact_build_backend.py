"""Start the exact-build backend (a worktree's code) with the researcher's environment files.

On 2026-10-15 the app, started from the repository root, loaded `.env.local` then `.env` itself
(api/app.py: load_dotenv(".env.local"); load_dotenv()). An app started from a worktree would not
find them, so this launcher loads the same two files, in the same order and without overriding
anything already set, into this process only, then runs uvicorn on the worktree's code. Nothing
is printed, logged or copied; values never leave this process.

Usage: python run_exact_build_backend.py <repo_root_with_env_files> <worktree> <port>
"""
import os
import sys

repo, worktree, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
assert os.environ.get("TESTING") != "1", "the exact-build app must not run with TESTING=1"

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(repo, ".env.local"), override=False)
load_dotenv(os.path.join(repo, ".env"), override=False)

os.chdir(worktree)
sys.path.insert(0, os.path.join(worktree, "src"))

import uvicorn  # noqa: E402

import adaptive_trust_medical_rag  # noqa: E402

# Proof of which code is served (a path only, no environment values).
print(f"exact-build code: {os.path.dirname(adaptive_trust_medical_rag.__file__)}", flush=True)

uvicorn.run("adaptive_trust_medical_rag.api.app:app", host="127.0.0.1", port=port)
