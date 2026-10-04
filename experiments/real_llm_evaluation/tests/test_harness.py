import unittest
import hashlib
from experiments.real_llm_evaluation.config import RealLLMEvaluationConfig
from experiments.real_llm_evaluation.runner import ExperimentRunner
from experiments.real_llm_evaluation.evaluator import DetachedCommonEvaluator

class MockBackend:
    def __init__(self, should_fail=False, exception_msg=""):
        self.should_fail = should_fail
        self.exception_msg = exception_msg
        self.call_count = 0
        self.last_query = None
        self.last_evidence = None
        self.last_final_prompt = None

    def generate(self, query=None, evidence=None, arm=None, final_prompt=None):
        self.call_count += 1
        self.last_query = query
        self.last_evidence = evidence
        self.last_final_prompt = final_prompt
        if self.should_fail:
            raise Exception(self.exception_msg)
        return "Mock Response"

class MockVerifier:
    def verify(self, answer, evidence):
        if "Unsupported" in answer:
            return {"support_rate": 0.0, "citation_rate": 0.0, "unsupported_rate": 1.0}
        return {"support_rate": 1.0, "citation_rate": 1.0, "unsupported_rate": 0.0}

class TestExperimentHarness(unittest.TestCase):
    def setUp(self):
        self.config = RealLLMEvaluationConfig()
        self.config.execution_authorized = True
        self.runner = ExperimentRunner(self.config)

    def test_authorization_gate_blocks_startup(self):
        unauthorized_config = RealLLMEvaluationConfig()
        unauthorized_config.execution_authorized = False
        with self.assertRaises(RuntimeError) as context:
            ExperimentRunner(unauthorized_config)
        self.assertIn("NOT AUTHORIZED", str(context.exception))

    def test_authorization_gate_blocks_execution(self):
        # Even if runner is bypassed somehow, execution blocks
        backend = MockBackend()
        self.config.execution_authorized = False
        with self.assertRaises(RuntimeError) as context:
            self.runner.execute_case("CASE_1", "Q", [], "R1", "ARM_A_BASELINE", backend)
        self.assertIn("NOT AUTHORIZED", str(context.exception))
        self.assertEqual(backend.call_count, 0)

    def test_retry_violation_blocks(self):
        bad_config = RealLLMEvaluationConfig()
        bad_config.execution_authorized = True
        bad_config.retry_max_attempts = 3
        with self.assertRaises(RuntimeError) as ctx:
            ExperimentRunner(bad_config)
        self.assertIn("retries enabled", str(ctx.exception))

    def test_fallback_violation_blocks(self):
        bad_config = RealLLMEvaluationConfig()
        bad_config.execution_authorized = True
        bad_config.fallback_enabled = True
        with self.assertRaises(RuntimeError) as ctx:
            ExperimentRunner(bad_config)
        self.assertIn("fallback enabled", str(ctx.exception))

    def test_failover_violation_blocks(self):
        bad_config = RealLLMEvaluationConfig()
        bad_config.execution_authorized = True
        bad_config.failover_enabled = True
        with self.assertRaises(RuntimeError) as ctx:
            ExperimentRunner(bad_config)
        self.assertIn("failover enabled", str(ctx.exception))
        
    def test_imputation_violation_blocks(self):
        bad_config = RealLLMEvaluationConfig()
        bad_config.execution_authorized = True
        bad_config.imputation_enabled = True
        with self.assertRaises(RuntimeError) as ctx:
            ExperimentRunner(bad_config)
        self.assertIn("imputation enabled", str(ctx.exception))

    def test_no_retry_on_401(self):
        backend = MockBackend(should_fail=True, exception_msg="401 Unauthorized")
        result = self.runner.execute_case("CASE_1", "Query", [], "R1", "ARM_A_BASELINE", backend)
        self.assertEqual(result["status"], "PROVIDER_FAILURE")
        self.assertEqual(backend.call_count, 1)

    def test_arm_symmetry_config(self):
        snap_a = self.runner.generate_snapshot("ARM_A_BASELINE")
        snap_b = self.runner.generate_snapshot("ARM_B_ADAPTIVE")
        for key in snap_a:
            if key not in ["arm", "adaptive_control_enabled"]:
                self.assertEqual(snap_a[key], snap_b[key])
        self.assertFalse(snap_a["adaptive_control_enabled"])
        self.assertTrue(snap_b["adaptive_control_enabled"])

    def test_arm_symmetry_instantiated_prompt(self):
        backend_a = MockBackend()
        backend_b = MockBackend()
        
        q = "What is the mechanism of action for metformin?"
        ev = [{"chunk_id": "1", "text": "Metformin inhibits hepatic gluconeogenesis."}]
        
        res_a = self.runner.execute_case("CASE_1", q, ev, "R1", "ARM_A_BASELINE", backend_a)
        res_b = self.runner.execute_case("CASE_1", q, ev, "R1", "ARM_B_ADAPTIVE", backend_b)
        
        self.assertEqual(backend_a.last_query, backend_b.last_query)
        self.assertEqual(backend_a.last_evidence, backend_b.last_evidence)
        
        # Verify final instantiated prompt is identical across arms
        self.assertEqual(backend_a.last_final_prompt, backend_b.last_final_prompt)
        
        # Verify hashes match
        self.assertEqual(res_a["instantiated_prompt_hash"], res_b["instantiated_prompt_hash"])

if __name__ == '__main__':
    unittest.main()
