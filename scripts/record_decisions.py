import json
from pathlib import Path
import hashlib

# 1. Record decisions for the 6 escalations in their respective JSON files
decisions = {
    "v3.1h-001": {"41225655": ("NOT_RELEVANT", "The document concerns etanercept and cerebrovascular function in elderly rheumatoid arthritis patients and does not provide evidence about metformin inhibition of hepatic gluconeogenesis.", "HIGH", "DISAGREE")},
    "v3.1h-002": {"42677606": ("NOT_RELEVANT", "The document concerns copper-induced oxidative stress in chicken hepatocytes and does not provide evidence about the clearance pathway of lisinopril.", "HIGH", "DISAGREE")},
    "v3.1h-022": {"42653173": ("NOT_RELEVANT", "The document concerns acute drug toxicity in analgesic-psychotropic polypharmacy and does not provide evidence about the specific CYP2C9 interaction between fluconazole and warfarin.", "HIGH", "DISAGREE")},
    "v3.1h-046": {"42662112": ("NO_EVIDENCE", "The document concerns renoprotective effects of antidiabetic drugs in patients with type 2 diabetes and is potentially relevant to medication safety and renal function, but the available title-only source does not establish the mechanisms of idiosyncratic drug-induced liver injury.", "LOW", "DISAGREE")},
    "v3.1h-066": {
        "41397500": ("NOT_RELEVANT", "The document concerns QT prolongation associated with antipsychotic and antidepressant use and does not provide evidence about metformin contraindication in severe renal disease.", "HIGH", "DISAGREE"),
        "42658230": ("NOT_RELEVANT", "The document concerns supratherapeutic digoxin levels in children with cardiac disease and does not provide evidence about metformin contraindication in severe renal disease.", "HIGH", "DISAGREE")
    }
}

out_dir = Path("experiments/annotations/v3_1_human/pilot/false_negative_screen")

for cid, docs in decisions.items():
    json_path = out_dir / f"{cid}_screen.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for did, (label, reason, conf, agree) in docs.items():
            data["human_final_decisions"][did] = {
                "human_final_label": label,
                "human_annotation_reason": reason,
                "human_confidence": conf,
                "human_agreement": agree
            }
            
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

print("Recorded human decisions for the 6 initial escalations.")

# 2. Fix the screening script seed reproducibility issue
script_path = Path("scripts/run_screening.py")
if script_path.exists():
    content = script_path.read_text(encoding="utf-8")
    content = content.replace("import random", "import random\nimport hashlib")
    content = content.replace("42 + hash(cid)", "42 + int(hashlib.md5(cid.encode()).hexdigest(), 16) % (10**8)")
    script_path.write_text(content, encoding="utf-8")
    print("Fixed reproducibility issue in run_screening.py.")
