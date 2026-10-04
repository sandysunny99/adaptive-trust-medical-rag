"""Cognee readiness probe for Phase 4 of the Final Gate 5 Readiness Validation."""
import asyncio
import json
import os
import sys
import time
import hashlib

os.environ["PYTHONIOENCODING"] = "utf-8"

OUT_DIR = "experiments/track_a_abstract_enriched_reannotation_v1/gate5_final_readiness_v3"
DATASET_NAME = "gate5_readiness_v3_cognee"

QUERIES = [
    ("POS-01", "statin therapy is common"),
    ("POS-02", "Does statin interact with aspirin?"),
    ("RG-02",  "Statin is a drug. Cyanide is a poison."),
]

EVIDENCE_TEXTS = [
    {
        "id": "doc-fda-metformin",
        "text": "Metformin decreases hepatic glucose production, decreases intestinal absorption of glucose, and improves insulin sensitivity by increasing peripheral glucose uptake and utilization.",
    },
    {
        "id": "doc-guideline-warfarin-aspirin",
        "text": "Co-administration of warfarin and aspirin significantly increases the risk of major gastrointestinal and intracranial bleeding. Combination therapy requires close INR monitoring and risk-benefit evaluation.",
    },
]


async def run():
    import cognee
    from cognee.infrastructure.databases.relational import get_relational_engine
    
    print("Cognee readiness probe starting...")
    
    # Fresh dataset
    print(f"Adding evidence to dataset '{DATASET_NAME}'...")
    for doc in EVIDENCE_TEXTS:
        await cognee.add(
            doc["text"],
            dataset_name=DATASET_NAME,
        )
    
    print("Running cognify...")
    await cognee.cognify()
    
    print("Searching...")
    results = []
    for case_id, query in QUERIES:
        t0 = time.monotonic()
        try:
            raw = await cognee.search(query, cognee.SearchType.CHUNKS)
            dt = time.monotonic() - t0
            
            flat = []
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict) and "search_result" in item:
                        flat.extend(item["search_result"])
                    elif isinstance(item, dict):
                        flat.append(item)
                    else:
                        flat.append({"text": str(item)})
            
            entry = {
                "case": case_id,
                "query": query,
                "dataset_name": DATASET_NAME,
                "search_type": "CHUNKS",
                "raw_result_count": len(flat),
                "candidates": [{
                    "text_preview": str(r.get("text", ""))[:120] if isinstance(r, dict) else str(r)[:120],
                    "score": r.get("score") if isinstance(r, dict) else None,
                    "document_name": r.get("document_name") if isinstance(r, dict) else None,
                } for r in flat[:5]],
                "latency_s": round(dt, 3),
                "error": None,
                "evidence_source": "runtime_capture"
            }
        except Exception as e:
            entry = {
                "case": case_id,
                "query": query,
                "dataset_name": DATASET_NAME,
                "search_type": "CHUNKS",
                "raw_result_count": 0,
                "candidates": [],
                "latency_s": None,
                "error": str(e),
                "evidence_source": "runtime_capture"
            }
        
        results.append(entry)
        print(f"  {case_id}: {entry['raw_result_count']} results, error={entry['error']}")
    
    outpath = os.path.join(OUT_DIR, "COGNEE_FINAL_READINESS_RUNTIME.jsonl")
    with open(outpath, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, default=str) + "\n")
    
    print("Done")


if __name__ == "__main__":
    asyncio.run(run())
