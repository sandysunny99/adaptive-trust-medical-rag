import os
import json
import pytest
import hashlib

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from prompt_instantiator import instantiate_prompt


PROMPT_PATH = "experiments/prompts/REAL_LLM_EVALUATION_PROMPT_V1_2.txt"

def load_prompt():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()

def test_safe_instantiation_no_keyerror():
    template = load_prompt()
    kwargs = {
        "query": "Is Warfarin safe?",
        "patient_context": "None",
        "risk_tier": "R1",
        "evidence_block": "Warfarin interacts with Aspirin."
    }
    # This should not raise KeyError
    instantiated = instantiate_prompt(template, **kwargs)
    
    assert "Is Warfarin safe?" in instantiated
    assert "Warfarin interacts with Aspirin." in instantiated
    
    # JSON literal braces must be preserved
    assert '{\n  "conclusion"' in instantiated
    assert '"claims_for_verification": [' in instantiated

def test_missing_placeholder():
    template = load_prompt()
    kwargs = {
        "query": "Is Warfarin safe?",
        "patient_context": "None",
        # missing risk_tier
        "evidence_block": "Warfarin interacts with Aspirin."
    }
    with pytest.raises(ValueError, match="Missing required placeholders"):
        instantiate_prompt(template, **kwargs)

def test_extra_placeholder():
    template = load_prompt()
    kwargs = {
        "query": "Is Warfarin safe?",
        "patient_context": "None",
        "risk_tier": "R1",
        "evidence_block": "Warfarin interacts with Aspirin.",
        "extra_val": "Should fail"
    }
    with pytest.raises(ValueError, match="Unexpected extra placeholders"):
        instantiate_prompt(template, **kwargs)

def test_cross_case_isolation():
    template = load_prompt()
    case_a = {
        "query": "Case A Query",
        "patient_context": "Case A Context",
        "risk_tier": "R0",
        "evidence_block": "Case A Evidence"
    }
    case_b = {
        "query": "Case B Query",
        "patient_context": "Case B Context",
        "risk_tier": "R3",
        "evidence_block": "Case B Evidence"
    }
    
    result_a1 = instantiate_prompt(template, **case_a)
    result_b = instantiate_prompt(template, **case_b)
    result_a2 = instantiate_prompt(template, **case_a)
    
    assert result_a1 == result_a2
    assert "Case B" not in result_a1
    assert "Case A" not in result_b

def test_reproducibility():
    template = load_prompt()
    kwargs = {
        "query": "Is Warfarin safe?",
        "patient_context": "None",
        "risk_tier": "R1",
        "evidence_block": "Warfarin interacts with Aspirin."
    }
    res1 = instantiate_prompt(template, **kwargs)
    res2 = instantiate_prompt(template, **kwargs)
    
    assert res1 == res2
    assert hashlib.sha256(res1.encode('utf-8')).hexdigest() == hashlib.sha256(res2.encode('utf-8')).hexdigest()

def test_arm_symmetry():
    # Demonstrates that the instantiation engine is deterministic and applies identical
    # base templating rules, while leaving the protocol-level arm definition untouched.
    # The actual V1.2 arms vary only by the post/pre gates, not by prompt differences!
    # So both arms receive the same instantiated prompt template for the same case.
    template = load_prompt()
    kwargs = {
        "query": "Is Warfarin safe?",
        "patient_context": "None",
        "risk_tier": "R1",
        "evidence_block": "Warfarin interacts with Aspirin."
    }
    arm_a_prompt = instantiate_prompt(template, **kwargs)
    arm_b_prompt = instantiate_prompt(template, **kwargs)
    assert arm_a_prompt == arm_b_prompt

if __name__ == "__main__":
    pytest.main([__file__])
