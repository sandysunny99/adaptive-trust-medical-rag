import unittest
from experiments.real_llm_evaluation.config import RealLLMEvaluationConfig
from experiments.real_llm_evaluation.runner import ExperimentRunner
from experiments.real_llm_evaluation.evaluator import DetachedCommonEvaluator

class MockBackend:
    def __init__(self, should_fail=False, exception_msg=""):
        self.should_fail = should_fail
        self.exception_msg = exception_msg
        self.call_count = 0

    def generate(self):
        self.call_count += 1
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
        self.runner = ExperimentRunner(self.config)
        self.evaluator = DetachedCommonEvaluator(MockVerifier())

    def test_no_retry_on_401(self):
        backend = MockBackend(should_fail=True, exception_msg="401 Unauthorized")
        result = self.runner.execute_case("CASE_1", "ARM_A_BASELINE", backend)
        self.assertEqual(result["status"], "PROVIDER_FAILURE")
        self.assertEqual(backend.call_count, 1)

    def test_no_retry_on_429(self):
        backend = MockBackend(should_fail=True, exception_msg="429 Too Many Requests")
        result = self.runner.execute_case("CASE_2", "ARM_A_BASELINE", backend)
        self.assertEqual(result["status"], "PROVIDER_FAILURE")
        self.assertEqual(backend.call_count, 1)

    def test_no_retry_on_timeout(self):
        backend = MockBackend(should_fail=True, exception_msg="Timeout")
        result = self.runner.execute_case("CASE_3", "ARM_A_BASELINE", backend)
        self.assertEqual(result["status"], "PROVIDER_FAILURE")
        self.assertEqual(backend.call_count, 1)

    def test_arm_symmetry(self):
        snap_a = self.runner.generate_snapshot("ARM_A_BASELINE")
        snap_b = self.runner.generate_snapshot("ARM_B_ADAPTIVE")
        
        # Only adaptive_control_enabled and arm name should differ
        for key in snap_a:
            if key not in ["arm", "adaptive_control_enabled"]:
                self.assertEqual(snap_a[key], snap_b[key])
        
        self.assertFalse(snap_a["adaptive_control_enabled"])
        self.assertTrue(snap_b["adaptive_control_enabled"])

    def test_common_evaluator_symmetry(self):
        res_a = self.evaluator.evaluate_output("Good response", [])
        res_b = self.evaluator.evaluate_output("Good response", [])
        self.assertEqual(res_a.claim_support_rate, res_b.claim_support_rate)
        
        res_bad = self.evaluator.evaluate_output("Unsupported claim", [])
        self.assertEqual(res_bad.unsupported_answer_rate, 1.0)
