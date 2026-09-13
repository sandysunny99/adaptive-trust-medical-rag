import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

FROZEN_DATASET_HASH = "af71c70d36081b1b68316b5ff8636969c8b964c9655f752b41112694ebc02c48"
EXPECTED_CASE_COUNT = 200
REQUIRED_MODEL = "gemini-3.1-pro-preview"

class PreflightError(Exception):
    pass

class ExecutionError(Exception):
    pass

class Phase15Runner:
    def __init__(self, dataset_path: Path, output_dir: Path):
        self.dataset_path = dataset_path
        self.output_dir = output_dir
        self.cases = []
        self.run_id = f"phase15_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        self.run_dir = self.output_dir / self.run_id
        
    def _compute_file_hash(self, path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest().lower()

    def preflight_check(self) -> Dict[str, Any]:
        logging.info("Starting Phase 15 Preflight Check...")
        
        if not self.dataset_path.exists():
            raise PreflightError(f"Dataset not found at {self.dataset_path}")
            
        dataset_hash = self._compute_file_hash(self.dataset_path)
        if dataset_hash != FROZEN_DATASET_HASH:
            raise PreflightError(f"Dataset hash mismatch. Expected {FROZEN_DATASET_HASH}, got {dataset_hash}")
            
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        if len(lines) != EXPECTED_CASE_COUNT:
            raise PreflightError(f"Case count mismatch. Expected {EXPECTED_CASE_COUNT}, got {len(lines)}")
            
        case_ids = set()
        for i, line in enumerate(lines):
            try:
                case = json.loads(line)
            except json.JSONDecodeError as e:
                raise PreflightError(f"Malformed JSON on line {i+1}: {e}")
                
            cid = case.get("case_id")
            if not cid:
                raise PreflightError(f"Missing case_id on line {i+1}")
            if cid in case_ids:
                raise PreflightError(f"Duplicate case_id found: {cid}")
            case_ids.add(cid)
            self.cases.append(case)
            
        # Write Preflight Manifest
        self.run_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "run_id": self.run_id,
            "dataset_hash": dataset_hash,
            "expected_cases": EXPECTED_CASE_COUNT,
            "model_identifier": REQUIRED_MODEL,
            "provider": "google",
            "execution_mode": "PREFLIGHT",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "PREFLIGHT_PASS"
        }
        
        with open(self.run_dir / "run_manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            
        logging.info("Preflight check passed successfully.")
        return manifest

    def execute(self, require_execute_flag: bool = False, execute_flag_passed: bool = False):
        if require_execute_flag and not execute_flag_passed:
            logging.info("HARD STOP: Preflight complete. Execution requires --execute flag.")
            return

        logging.info("Execution requested. Validating runtime requirements...")
        
        if not os.environ.get("GEMINI_API_KEY"):
            raise ExecutionError("Missing GEMINI_API_KEY in environment.")
            
        logging.info("API Key found. Commencing paired execution...")
        self.run_paired_evaluation()

    def run_paired_evaluation(self):
        # This will contain the actual calls to the AdaptiveTrustRAGOrchestrator
        # for both BASELINE (gates off) and HARDENED (gates on).
        # Currently, this throws an error to explicitly prevent unauthorized execution.
        raise NotImplementedError("Live execution logic is scaffolded but deliberately blocked pending execution authorization.")

def main():
    parser = argparse.ArgumentParser(description="Phase 15 Canonical Execution Runner")
    parser.add_argument("--dataset", type=str, default="experiments/phase15/phase15_cases.jsonl")
    parser.add_argument("--output", type=str, default="experiments/phase15/runs")
    parser.add_argument("--execute", action="store_true", help="Authorize actual model execution")
    args = parser.parse_args()
    
    dataset_path = Path(args.dataset)
    output_dir = Path(args.output)
    
    runner = Phase15Runner(dataset_path, output_dir)
    
    try:
        runner.preflight_check()
        runner.execute(require_execute_flag=True, execute_flag_passed=args.execute)
    except PreflightError as e:
        logging.error(f"PREFLIGHT FAILED: {e}")
        sys.exit(1)
    except ExecutionError as e:
        logging.error(f"EXECUTION BLOCKED: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    main()
