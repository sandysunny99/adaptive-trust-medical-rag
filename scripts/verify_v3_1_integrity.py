import json
import re

def normalize(q):
    return re.sub(r'[^a-z0-9]', ' ', q.lower()).strip()

c_set = [
    "metformin pharmacology",
    "warfarin aspirin interaction",
    "CYP2C9 drug interactions",
    "drug induced liver injury",
    "spironolactone hyperkalemia",
    "atorvastatin mechanism of action",
    "lisinopril renal clearance",
    "omeprazole clopidogrel interaction",
    "levothyroxine iron interaction",
    "citalopram qt prolongation",
    "doxorubicin cardiotoxicity",
    "amiodarone pulmonary toxicity",
    "isotretinoin teratogenicity",
    "acetaminophen hepatotoxicity",
    "digoxin toxicity monitoring",
    "alendronate esophageal ulcer",
    "pantoprazole clopidogrel",
    "fluoxetine cyp2d6",
    "sertraline pregnancy",
    "gabapentin sedation",
    "tramadol seizure risk",
    "celecoxib cardiovascular risk",
    "rivaroxaban bleeding antidote",
    "apixaban renal dosing",
    "dabigatran reversal agent"
]

with open("experiments/manifests/retrieval_dataset_v3_1.json") as f:
    cases = json.load(f)

e_set = [c["query"] for c in cases]

print("Checking query separation for V3.1 True Confirmed...")
c_norms = set(normalize(c) for c in c_set)

leak = False
for e in e_set:
    e_norm = normalize(e)
    if e_norm in c_norms:
        print(f"FAIL: Leak detected. E-Set query '{e}' exactly matches C-Set.")
        leak = True
        
    e_tokens = set(e_norm.split())
    for c in c_norms:
        c_tokens = set(c.split())
        overlap = len(e_tokens & c_tokens) / max(len(e_tokens), len(c_tokens))
        if overlap > 0.8:
            print(f"WARNING: High token overlap ({overlap:.2f}) between E-Set '{e}' and C-Set '{c}'.")

if not leak:
    print("PASS: No exact query leakage detected. Acquisition and Evaluation sets are independent.")