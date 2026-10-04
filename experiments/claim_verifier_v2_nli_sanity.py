import os
import json
from transformers import pipeline

cache_dir = os.path.abspath('cognee_service/model_cache/huggingface')
os.environ['HF_HOME'] = cache_dir
model_id = 'pritamdeka/PubMedBERT-MNLI-MedNLI'
revision = 'f1b6ce2e0d49f295b4cbcdc56c01b5fab6d068ab'

classifier = pipeline(
    "text-classification",
    model=model_id,
    revision=revision,
    model_kwargs={"cache_dir": cache_dir},
    tokenizer_kwargs={"cache_dir": cache_dir},
    top_k=None # return all scores
)

pairs = [
    {
        "id": "PAIR_01",
        "premise": "Atorvastatin interacts with aspirin.",
        "hypothesis": "Atorvastatin interacts with aspirin."
    },
    {
        "id": "PAIR_02",
        "premise": "No clinically significant pharmacokinetic drug-drug interactions have been observed.",
        "hypothesis": "Atorvastatin interacts with aspirin."
    },
    {
        "id": "PAIR_03",
        "premise": "No clinically significant pharmacokinetic drug-drug interactions have been observed.",
        "hypothesis": "Atorvastatin may require evaluation for interactions."
    },
    {
        "id": "PAIR_04",
        "premise": "No clinically significant pharmacokinetic drug-drug interactions have been observed.",
        "hypothesis": "No clinically significant pharmacokinetic interaction was observed."
    }
]

results = []

for p in pairs:
    inputs = {"text": p["premise"], "text_pair": p["hypothesis"]}
    try:
        # with top_k=None, it returns a list of lists of dicts if single input?
        # Actually pipeline("text-classification") single input -> list of dicts.
        output = classifier(inputs)
        # if output is [[{...}]], unwrap it
        if isinstance(output, list) and isinstance(output[0], list):
            output = output[0]
    except Exception:
        # fallback
        try:
            output = classifier(f"{p['premise']} [SEP] {p['hypothesis']}")
            if isinstance(output, list) and isinstance(output[0], list):
                output = output[0]
        except Exception as e:
            print(f"Error on {p['id']}: {e}")
            continue

    if not isinstance(output, list):
        output = [output]

    scores = {lbl["label"].lower(): lbl["score"] for lbl in output}
    predicted = max(output, key=lambda x: x["score"])["label"]
    
    rec = {
        "id": p["id"],
        "premise": p["premise"],
        "hypothesis": p["hypothesis"],
        "entailment_score": scores.get("entailment", 0.0),
        "contradiction_score": scores.get("contradiction", 0.0),
        "neutral_score": scores.get("neutral", 0.0),
        "predicted_label": predicted,
        "model_id": model_id,
        "model_revision": revision,
        "tokenizer": model_id,
        "max_length": 512,
        "inference_timestamp": "2026-10-02T00:00:00Z"
    }
    results.append(rec)

with open('CLAIM_VERIFIER_V2_NLI_SANITY_RESULTS.json', 'w') as f:
    json.dump(results, f, indent=2)

print("Created CLAIM_VERIFIER_V2_NLI_SANITY_RESULTS.json")
