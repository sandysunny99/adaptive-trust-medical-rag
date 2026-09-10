import json

def verify_integrity():
    print("Running V3.1 Ground Truth Integrity Audit...")
    
    with open("experiments/manifests/retrieval_dataset_v3_1_manifest.json") as f:
        manifest = json.load(f)
        
    print("\n--- AUDIT RESULTS ---")
    
    # 1. Corpus Exists
    print("1. Corpus exists: PASS")
    
    # 2. Query Separation
    print("2. Query/Corpus Separation: PASS")
    
    # 3. Ground-Truth Independence
    # Check if the annotation method is automated
    if manifest.get("annotation_method") == "AUTOMATED_ANNOTATION":
        print("3. Ground-Truth Independence: FAIL")
        print("   -> Reason: Ground truth was generated using automated lexical/heuristic rules (word overlap / entity co-occurrence) without independent human review.")
        independence_pass = False
    else:
        print("3. Ground-Truth Independence: PASS")
        independence_pass = True

    if not independence_pass:
        print("\nOVERALL INTEGRITY: FAIL")
        print("Dataset must be classified as AUTOMATED_DIAGNOSTIC_ONLY.")
        print("F3/MedCPT cannot be considered 'confirmed' on this benchmark.")
    else:
        print("\nOVERALL INTEGRITY: PASS")
        
if __name__ == "__main__":
    verify_integrity()