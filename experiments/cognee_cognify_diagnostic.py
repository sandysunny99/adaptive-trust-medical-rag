"""
COGNEE COGNIFY ROOT-CAUSE DIAGNOSTIC
=====================================
Minimal isolated test to determine why cognify() fails to create a searchable graph.
Does NOT modify the security pipeline. Does NOT run Full Gate 5.
"""
import json, os, sys, hashlib, asyncio, traceback
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath("src"))
os.environ["HF_HOME"] = os.path.abspath("cognee_service/model_cache/huggingface")

OUT_DIR = os.path.abspath("experiments/track_a_abstract_enriched_reannotation_v1/cognee_infrastructure_diagnostic_v1")
os.makedirs(OUT_DIR, exist_ok=True)

DATASET_NAME = "gate5_cognify_diag_v1"
RESULTS = {"timestamp": datetime.now(timezone.utc).isoformat(), "phases": {}}

def log_phase(name, data):
    RESULTS["phases"][name] = data
    print(f"[DIAG] Phase: {name}")
    for k, v in data.items():
        if isinstance(v, str) and len(v) > 200:
            print(f"  {k}: {v[:200]}...")
        else:
            print(f"  {k}: {v}")

async def main():
    import cognee
    
    # ============================
    # PHASE 1: Environment Capture
    # ============================
    env_info = {
        "cognee_version": getattr(cognee, "__version__", "unknown"),
        "python_version": sys.version,
        "platform": sys.platform,
        "HF_HOME": os.environ.get("HF_HOME", "NOT_SET"),
        "cognee_system_dir": "UNKNOWN",
    }
    
    # Find cognee system directory
    import cognee.shared
    cognee_pkg_dir = os.path.dirname(os.path.dirname(cognee.shared.__file__))
    system_dir = os.path.join(cognee_pkg_dir, ".cognee_system", "databases")
    env_info["cognee_system_dir"] = system_dir
    env_info["cognee_system_exists"] = os.path.exists(system_dir)
    
    log_phase("environment", env_info)
    
    # ============================
    # PHASE 2: Model Check
    # ============================
    model_info = {}
    try:
        fastembed_cache = os.path.join(os.environ.get("TEMP", "/tmp"), "fastembed_cache")
        bge_path = os.path.join(fastembed_cache, "models--BAAI--bge-small-en-v1.5")
        model_info["fastembed_cache"] = fastembed_cache
        model_info["bge_model_exists"] = os.path.exists(bge_path)
        if os.path.exists(bge_path):
            model_info["bge_model_files"] = os.listdir(bge_path)
    except Exception as e:
        model_info["error"] = str(e)
    
    # Check GLiNER
    try:
        hf_home = os.environ.get("HF_HOME", "")
        gliner_path = os.path.join(hf_home, "hub", "models--fastino--gliner2.5-base-v1")
        model_info["gliner_path"] = gliner_path
        model_info["gliner_exists"] = os.path.exists(gliner_path)
    except Exception as e:
        model_info["gliner_check_error"] = str(e)
    
    log_phase("model_check", model_info)
    
    # ============================
    # PHASE 3: Clean Add (NO PRUNE_SYSTEM)
    # ============================
    add_info = {}
    try:
        from cognee.tasks.ingestion.data_item import DataItem
        
        doc_a_text = "Statin interacts with aspirin causing increased bleeding risk."
        doc_b_text = "Cyanide is a poison that inhibits cytochrome c oxidase."
        
        doc_a_hash = hashlib.sha256(doc_a_text.encode()).hexdigest()
        doc_b_hash = hashlib.sha256(doc_b_text.encode()).hexdigest()
        
        data_items = [
            DataItem(
                data=doc_a_text,
                label="diag_doc_a",
                external_metadata={
                    "canonical_document_id": "diag_doc_a",
                    "canonical_chunk_id": "diag_doc_a_chunk_0",
                    "content_hash": doc_a_hash,
                    "trust_class": "TRUSTED",
                }
            ),
            DataItem(
                data=doc_b_text,
                label="diag_doc_b",
                external_metadata={
                    "canonical_document_id": "diag_doc_b",
                    "canonical_chunk_id": "diag_doc_b_chunk_0",
                    "content_hash": doc_b_hash,
                    "trust_class": "UNTRUSTED_CONTROL",
                }
            ),
        ]
        
        print("[DIAG] Calling cognee.add()...")
        add_result = await cognee.add(data_items, dataset_name=DATASET_NAME)
        add_info["add_success"] = True
        add_info["add_result_type"] = str(type(add_result))
        add_info["add_result"] = str(add_result)[:500] if add_result else "None"
        
    except Exception as e:
        add_info["add_success"] = False
        add_info["add_error"] = str(e)
        add_info["add_traceback"] = traceback.format_exc()
    
    log_phase("cognee_add", add_info)
    
    if not add_info.get("add_success"):
        log_phase("ABORT", {"reason": "cognee.add() failed, cannot proceed to cognify"})
        save_results()
        return
    
    # ============================
    # PHASE 4: Cognify with FULL error capture
    # ============================
    cognify_info = {}
    try:
        print("[DIAG] Calling cognee.cognify() - NOT catching exceptions...")
        import time
        t0 = time.time()
        cognify_result = await cognee.cognify()
        t1 = time.time()
        
        cognify_info["cognify_success"] = True
        cognify_info["cognify_duration_s"] = round(t1 - t0, 2)
        cognify_info["cognify_result_type"] = str(type(cognify_result))
        cognify_info["cognify_result"] = str(cognify_result)[:1000] if cognify_result else "None"
        
    except Exception as e:
        cognify_info["cognify_success"] = False
        cognify_info["cognify_error_type"] = type(e).__name__
        cognify_info["cognify_error"] = str(e)
        cognify_info["cognify_traceback"] = traceback.format_exc()
    
    log_phase("cognify", cognify_info)
    
    # ============================
    # PHASE 5: Search immediately after cognify
    # ============================
    search_info = {}
    for query in ["statin", "aspirin", "cyanide", "Statin interacts with aspirin"]:
        try:
            print(f"[DIAG] Searching: '{query}'...")
            results = await cognee.search(query, cognee.SearchType.CHUNKS, datasets=[DATASET_NAME])
            
            flat = []
            if results:
                for d in results:
                    if isinstance(d, dict) and "search_result" in d:
                        flat.extend(d["search_result"])
                    else:
                        flat.append(d)
            
            search_info[query] = {
                "success": True,
                "raw_result_count": len(results) if results else 0,
                "flat_count": len(flat),
                "items": []
            }
            
            for item in flat[:5]:  # First 5 only
                if isinstance(item, dict):
                    search_info[query]["items"].append({
                        "id": item.get("id", "UNKNOWN"),
                        "text": (item.get("text", "")[:100] + "...") if len(item.get("text", "")) > 100 else item.get("text", ""),
                        "score": item.get("score"),
                        "external_metadata": item.get("external_metadata"),
                    })
                else:
                    search_info[query]["items"].append({
                        "type": type(item).__name__,
                        "repr": str(item)[:200]
                    })
                    
        except Exception as e:
            search_info[query] = {
                "success": False,
                "error_type": type(e).__name__,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    log_phase("search", search_info)
    
    # ============================
    # PHASE 6: Alternative search without dataset filter
    # ============================
    alt_search_info = {}
    try:
        print("[DIAG] Searching WITHOUT dataset filter...")
        results = await cognee.search("statin", cognee.SearchType.CHUNKS)
        
        flat = []
        if results:
            for d in results:
                if isinstance(d, dict) and "search_result" in d:
                    flat.extend(d["search_result"])
                else:
                    flat.append(d)
        
        alt_search_info["no_dataset_filter"] = {
            "success": True,
            "raw_count": len(results) if results else 0,
            "flat_count": len(flat),
            "items": [str(item)[:200] for item in flat[:5]]
        }
    except Exception as e:
        alt_search_info["no_dataset_filter"] = {
            "success": False,
            "error_type": type(e).__name__,
            "error": str(e)
        }
    
    # Also try INSIGHTS search type
    try:
        print("[DIAG] Searching with INSIGHTS type...")
        results = await cognee.search("statin", cognee.SearchType.INSIGHTS, datasets=[DATASET_NAME])
        flat = []
        if results:
            for d in results:
                if isinstance(d, dict) and "search_result" in d:
                    flat.extend(d["search_result"])
                else:
                    flat.append(d)
        alt_search_info["insights_search"] = {
            "success": True,
            "raw_count": len(results) if results else 0,
            "flat_count": len(flat),
            "items": [str(item)[:200] for item in flat[:5]]
        }
    except Exception as e:
        alt_search_info["insights_search"] = {
            "success": False,
            "error_type": type(e).__name__,
            "error": str(e)
        }
    
    log_phase("alternative_search", alt_search_info)
    
    # ============================
    # PHASE 7: Dataset State Inspection
    # ============================
    dataset_info = {}
    try:
        # Try to inspect dataset via Cognee internals
        from cognee.modules.data.methods import get_datasets
        datasets = await get_datasets()
        dataset_info["all_datasets"] = []
        for ds in datasets:
            ds_info = {
                "name": getattr(ds, "name", str(ds)),
                "id": str(getattr(ds, "id", "unknown")),
            }
            dataset_info["all_datasets"].append(ds_info)
    except Exception as e:
        dataset_info["datasets_error"] = str(e)
    
    log_phase("dataset_state", dataset_info)
    
    # ============================
    # PHASE 8: Cognify Return Value Analysis
    # ============================
    cognify_analysis = {}
    try:
        # Read the cognify source to understand return semantics
        import cognee.api.v1.cognify.cognify as cognify_module
        cognify_source = os.path.abspath(cognify_module.__file__)
        cognify_analysis["cognify_source_path"] = cognify_source
        with open(cognify_source, "r") as f:
            lines = f.readlines()
        cognify_analysis["cognify_source_lines"] = len(lines)
        # Find the main cognify function
        for i, line in enumerate(lines):
            if "async def cognify" in line or "def cognify" in line:
                cognify_analysis[f"cognify_def_line_{i+1}"] = line.strip()
    except Exception as e:
        cognify_analysis["error"] = str(e)
    
    log_phase("cognify_analysis", cognify_analysis)
    
    # ============================
    # SUMMARY
    # ============================
    add_ok = add_info.get("add_success", False)
    cognify_ok = cognify_info.get("cognify_success", False)
    any_search_ok = any(
        v.get("success") and v.get("flat_count", 0) > 0 
        for v in search_info.values() if isinstance(v, dict)
    )
    
    if not add_ok:
        status = "COGNEE_ADD_FAILED"
    elif not cognify_ok:
        status = "COGNEE_COGNIFY_FAILED_ROOT_CAUSE_IDENTIFIED"
    elif not any_search_ok:
        status = "COGNEE_COGNIFY_SUCCEEDED_BUT_SEARCH_EMPTY"
    else:
        status = "COGNEE_COGNIFY_REPAIRED_DIAGNOSTIC_SEARCH_PASS"
    
    summary = {
        "status": status,
        "add_success": add_ok,
        "cognify_success": cognify_ok,
        "any_search_returned_candidates": any_search_ok,
        "gate5_status": "FULL_GATE5_FAILED_WITH_LIMITATIONS",
        "gate6_status": "NOT_AUTHORIZED_STOPPED",
    }
    log_phase("summary", summary)
    
    save_results()

def save_results():
    with open(os.path.join(OUT_DIR, "COGNEE_COGNIFY_DIAGNOSTIC_RESULTS.json"), "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)
    print(f"\n[DIAG] Results written to {OUT_DIR}/COGNEE_COGNIFY_DIAGNOSTIC_RESULTS.json")

if __name__ == "__main__":
    asyncio.run(main())
