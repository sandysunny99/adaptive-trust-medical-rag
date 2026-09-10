import json
import hashlib
import re
from pathlib import Path

def word_overlap(query, text):
    q_words = set(re.findall(r'\w+', query.lower()))
    t_words = set(re.findall(r'\w+', text.lower()))
    return len(q_words.intersection(t_words))

def get_evidence_span(text, ents):
    sentences = re.split(r'(?<=[.!?]) +', text)
    rel = [s for s in sentences if ents[0].lower() in s.lower()]
    if rel:
        return " ".join(rel[:2])
    return text[:200]

def main():
    print("Building V3.1 AUTOMATED_ANNOTATION Ground Truth...")
    with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json") as f:
        docs = json.load(f)
        
    cases = []
    
    q_data = [
        # Positive Candidates (60 cases)
        ("How does metformin inhibit hepatic gluconeogenesis?", "Pharmacology", "R1", "MECHANISM", ["metformin", "hepatic"]),
        ("Metformin contraindication in severe renal disease", "Medication_Safety", "R3", "PARAPHRASE", ["metformin", "renal"]),
        ("Concomitant use of warfarin and aspirin bleeding risk", "DDI", "R3", "MULTI_ENTITY", ["warfarin", "aspirin"]),
        ("Warfarin target INR monitoring", "Medication_Safety", "R3", "PARAPHRASE", ["warfarin", "inr"]),
        ("CYP2C9 interaction between fluconazole and warfarin", "DDI", "R3", "CYP_DDI", ["fluconazole", "cyp2c9"]),
        ("Genetic testing for CYP2C9 variants before prescribing", "Medication_Safety", "R2", "SYNONYM", ["cyp2c9", "genetic"]),
        ("Idiosyncratic drug induced liver injury mechanisms", "ADE", "R3", "MECHANISM", ["liver", "injury"]),
        ("Diagnosis of drug induced hepatotoxicity", "Medication_Safety", "R3", "PARAPHRASE", ["hepatotoxicity", "diagnosis"]),
        ("Spironolactone induced hyperkalemia", "ADE", "R3", "SYNONYM", ["spironolactone", "hyperkalemia"]),
        ("Spironolactone and lisinopril combination risks", "DDI", "R3", "MULTI_ENTITY", ["spironolactone", "lisinopril"]),
        ("What is the primary mechanism of action for atorvastatin?", "Pharmacology", "R1", "MECHANISM", ["atorvastatin", "reductase"]),
        ("Atorvastatin causing rhabdomyolysis", "ADE", "R3", "SYNONYM", ["atorvastatin", "rhabdomyolysis"]),
        ("Clearance pathway for lisinopril", "Pharmacology", "R1", "MECHANISM", ["lisinopril", "clearance"]),
        ("Lisinopril dosing in renal impairment GFR < 30", "Medication_Safety", "R3", "PARAPHRASE", ["lisinopril", "renal"]),
        ("CYP enzyme responsible for omeprazole metabolism", "Pharmacology", "R1", "CYP_DDI", ["omeprazole", "cyp2c19"]),
        ("Omeprazole reducing clopidogrel efficacy", "DDI", "R3", "MULTI_ENTITY", ["omeprazole", "clopidogrel"]),
        ("Is levothyroxine absorbed better on an empty stomach?", "Pharmacology", "R1", "MECHANISM", ["levothyroxine", "absorp"]),
        ("Iron sulfate decreasing levothyroxine absorption", "DDI", "R2", "MULTI_ENTITY", ["levothyroxine", "iron"]),
        ("Half-life of citalopram", "Pharmacology", "R1", "MECHANISM", ["citalopram", "half-life"]),
        ("Citalopram and dose dependent QT prolongation", "ADE", "R3", "SYNONYM", ["citalopram", "qt"]),
        ("Mechanism of doxorubicin intercalating DNA", "Pharmacology", "R2", "MECHANISM", ["doxorubicin", "dna"]),
        ("Doxorubicin associated heart failure", "ADE", "R3", "SYNONYM", ["doxorubicin", "heart"]),
        ("Amiodarone distribution in adipose tissue", "Pharmacology", "R1", "MECHANISM", ["amiodarone", "distribution"]),
        ("Amiodarone induced pulmonary fibrosis", "ADE", "R3", "SYNONYM", ["amiodarone", "pulmonary"]),
        ("Isotretinoin mechanism in acne", "Pharmacology", "R1", "MECHANISM", ["isotretinoin", "sebum"]),
        ("Isotretinoin causing severe birth defects", "ADE", "R3", "SYNONYM", ["isotretinoin", "birth"]),
        ("Acetaminophen toxic metabolite NAPQI", "Pharmacology", "R2", "MECHANISM", ["acetaminophen", "napqi"]),
        ("Acetaminophen overdose hepatotoxicity", "ADE", "R3", "SYNONYM", ["acetaminophen", "hepatotoxicity"]),
        ("Digoxin inhibition of Na-K ATPase", "Pharmacology", "R1", "MECHANISM", ["digoxin", "atpase"]),
        ("Monitoring for digoxin toxicity", "Medication_Safety", "R2", "PARAPHRASE", ["digoxin", "monitor"]),
        ("Alendronate bone resorption inhibition", "Pharmacology", "R1", "MECHANISM", ["alendronate", "osteoclast"]),
        ("Alendronate causing esophageal ulceration", "ADE", "R2", "SYNONYM", ["alendronate", "esophag"]),
        ("Pantoprazole proton pump inhibition", "Pharmacology", "R1", "MECHANISM", ["pantoprazole", "pump"]),
        ("Pantoprazole interaction with levothyroxine", "DDI", "R2", "MULTI_ENTITY", ["pantoprazole", "levothyroxine"]),
        ("Fluoxetine active metabolite norfluoxetine", "Pharmacology", "R1", "MECHANISM", ["fluoxetine", "norfluoxetine"]),
        ("Fluoxetine increasing suicidal ideation", "ADE", "R3", "SYNONYM", ["fluoxetine", "suicid"]),
        ("Sertraline serotonin reuptake blockade", "Pharmacology", "R1", "MECHANISM", ["sertraline", "serotonin"]),
        ("Sertraline safety during pregnancy", "Medication_Safety", "R2", "PARAPHRASE", ["sertraline", "pregnan"]),
        ("Gabapentin binding to voltage-gated calcium channels", "Pharmacology", "R1", "MECHANISM", ["gabapentin", "calcium"]),
        ("Gabapentin causing excessive somnolence", "ADE", "R1", "SYNONYM", ["gabapentin", "somnolence"]),
        ("Tramadol mu-opioid receptor affinity", "Pharmacology", "R1", "MECHANISM", ["tramadol", "opioid"]),
        ("Tramadol lowering seizure threshold", "ADE", "R2", "SYNONYM", ["tramadol", "seizure"]),
        ("Celecoxib selective COX-2 inhibition", "Pharmacology", "R1", "MECHANISM", ["celecoxib", "cox-2"]),
        ("Celecoxib and myocardial infarction risk", "ADE", "R3", "MULTI_ENTITY", ["celecoxib", "infarction"]),
        ("Rivaroxaban Factor Xa inhibition", "Pharmacology", "R1", "MECHANISM", ["rivaroxaban", "factor xa"]),
        ("Rivaroxaban associated major bleeding", "ADE", "R3", "SYNONYM", ["rivaroxaban", "bleed"]),
        ("Apixaban pharmacokinetics in renal failure", "Pharmacology", "R1", "MECHANISM", ["apixaban", "pharmacokinetics"]),
        ("Apixaban associated gastrointestinal bleeding", "ADE", "R3", "SYNONYM", ["apixaban", "gastrointestinal"]),
        ("Reversal agent for dabigatran", "Medication_Safety", "R3", "SYNONYM", ["dabigatran", "reversal"]),
        ("Dabigatran causing dyspepsia", "ADE", "R1", "SYNONYM", ["dabigatran", "dyspepsia"]),
        ("Management of severe bleeding on warfarin", "Medication_Safety", "R3", "PARAPHRASE", ["warfarin", "bleed"]),
        ("Renal dosing adjustments for metformin", "Medication_Safety", "R3", "PARAPHRASE", ["metformin", "renal"]),
        ("Clopidogrel and naproxen GI bleeding", "DDI", "R3", "MULTI_ENTITY", ["clopidogrel", "naproxen"]),
        ("What monitoring is required for amiodarone liver toxicity?", "Medication_Safety", "R2", "PARAPHRASE", ["amiodarone", "liver"]),
        ("Isotretinoin and tetracycline pseudotumor cerebri", "DDI", "R3", "MULTI_ENTITY", ["isotretinoin", "tetracycline"]),
        ("Digoxin and macrolide toxicity", "DDI", "R3", "MULTI_ENTITY", ["digoxin", "macrolide"]),
        ("Acetaminophen and warfarin INR prolongation", "DDI", "R3", "MULTI_ENTITY", ["acetaminophen", "inr"]),
        ("Citalopram and omeprazole QT prolongation", "DDI", "R3", "MULTI_ENTITY", ["citalopram", "omeprazole"]),
        ("Spironolactone causing gynecomastia", "ADE", "R1", "SYNONYM", ["spironolactone", "gynecomastia"]),
        ("Lisinopril contraindicated in angioedema", "Medication_Safety", "R3", "SYNONYM", ["lisinopril", "angioedema"]),
        
        # NO EVIDENCE Cases (15 cases) - Drugs not in corpus
        ("Penicillin anaphylaxis management", "Medication_Safety", "R3", "PARAPHRASE", ["penicillin"]),
        ("Amoxicillin and clavulanate dosing", "Pharmacology", "R1", "MECHANISM", ["amoxicillin"]),
        ("Sildenafil contraindication with nitrates", "DDI", "R3", "MULTI_ENTITY", ["sildenafil", "nitrate"]),
        ("Ibuprofen induced gastric ulcer", "ADE", "R2", "SYNONYM", ["ibuprofen", "ulcer"]),
        ("Salbutamol causing tachycardia", "ADE", "R1", "SYNONYM", ["salbutamol", "tachycardia"]),
        ("Omalizumab injection site reaction", "ADE", "R1", "SYNONYM", ["omalizumab"]),
        ("Methotrexate folic acid supplementation", "Medication_Safety", "R2", "PARAPHRASE", ["methotrexate"]),
        ("Lithium toxicity tremor", "ADE", "R2", "SYNONYM", ["lithium", "tremor"]),
        ("Clozapine agranulocytosis monitoring", "Medication_Safety", "R3", "PARAPHRASE", ["clozapine", "agranulocytosis"]),
        ("Valproate induced neural tube defects", "ADE", "R3", "SYNONYM", ["valproate", "neural"]),
        ("Lamotrigine Stevens-Johnson syndrome risk", "ADE", "R3", "MULTI_ENTITY", ["lamotrigine", "stevens"]),
        ("Sumatriptan mechanism for migraines", "Pharmacology", "R1", "MECHANISM", ["sumatriptan", "migraine"]),
        ("Ketamine NMDA antagonism", "Pharmacology", "R1", "MECHANISM", ["ketamine", "nmda"]),
        ("Propofol infusion syndrome", "ADE", "R3", "SYNONYM", ["propofol", "syndrome"]),
        ("Buprenorphine ceiling effect", "Pharmacology", "R1", "MECHANISM", ["buprenorphine", "ceiling"])
    ]
    
    for q, t, rt, d, ents in q_data:
        cases.append({"q": q, "t": t, "rt": rt, "d": d, "ents": ents})

    final_cases = []
    ground_truth = []
    
    for i, c in enumerate(cases):
        q = c["q"]
        
        scored_docs = []
        for doc in docs:
            text = doc.get("abstract", "")
            score = word_overlap(q, text)
            scored_docs.append((doc, text, score))
            
        scored_docs.sort(key=lambda x: x[2], reverse=True)
        
        relevant_docs = []
        expected_doc_ids = []
        
        primary_entity_in_corpus = any(c["ents"][0].lower() in d.get("abstract", "").lower() for d in docs)
        
        if primary_entity_in_corpus:
            # Take top 3 highest word overlap as candidates
            for doc, text, score in scored_docs:
                if c["ents"][0].lower() in text.lower():
                    expected_doc_ids.append(doc["document_id"])
                    authority = "PEER_REVIEWED_PUBMED"
                    span = get_evidence_span(text, c["ents"])
                    span_hash = hashlib.sha256(span.encode('utf-8')).hexdigest()
                    
                    relevant_docs.append({
                        "document_id": doc["document_id"],
                        "chunk_id": f"chunk-{doc['document_id']}-001",
                        "relevance": "DIRECT_SUPPORT",
                        "authority_tier": authority,
                        "evidence_span": span.strip(),
                        "evidence_text_hash": span_hash,
                        "annotation_reason": f"AUTOMATED_ANNOTATION: Top deterministic overlap ({score}) containing primary entity."
                    })
                    if len(expected_doc_ids) >= 3:
                        break
                    
            # Hard negatives: next 5 docs that mention primary drug but not others, or just next 5 docs that mention drug
            c_neg = 0
            for doc, text, score in scored_docs:
                if c["ents"][0].lower() in text.lower() and doc["document_id"] not in expected_doc_ids:
                    relevant_docs.append({
                        "document_id": doc["document_id"],
                        "chunk_id": f"chunk-{doc['document_id']}-001",
                        "relevance": "NOT_RELEVANT",
                        "authority_tier": "PEER_REVIEWED_PUBMED",
                        "evidence_span": "",
                        "evidence_text_hash": "",
                        "annotation_reason": f"AUTOMATED_ANNOTATION HARD NEGATIVE: Mentions {c['ents'][0]} but lower relevance score."
                    })
                    c_neg += 1
                    if c_neg >= 5: break
        
        case_id = f"r3.1-manual-{i+1:03d}"
        
        final_cases.append({
            "case_id": case_id,
            "query": q,
            "claim_type": c["t"],
            "difficulty": c["d"],
            "risk_tier": c["rt"],
            "expected_document_ids": list(set(expected_doc_ids)),
            "expected_chunk_ids": [f"chunk-{d}-001" for d in set(expected_doc_ids)],
            "expected_entity_ids": [c["ents"][0]]
        })
        
        ground_truth.append({
            "case_id": case_id,
            "query": q,
            "claim_type": c["t"],
            "difficulty": c["d"],
            "risk_tier": c["rt"],
            "relevant_documents": relevant_docs
        })
        
    out_dir = Path("experiments/manifests")
    
    with open(out_dir / "retrieval_ground_truth_v3_1_manual.json", "w") as f:
        json.dump(ground_truth, f, indent=2)
        
    with open(out_dir / "retrieval_dataset_v3_1.json", "w") as f:
        json.dump(final_cases, f, indent=2)
        
    positives = sum(1 for c in final_cases if c["expected_document_ids"])
    no_evidence = sum(1 for c in final_cases if not c["expected_document_ids"])
    print(f"Generated AUTOMATED_ANNOTATION V3.1: {len(final_cases)} cases, {positives} positive, {no_evidence} no-evidence.")
    
    manifest = {
        "dataset_version": "v3.1-DIAGNOSTIC",
        "annotation_method": "AUTOMATED_ANNOTATION",
        "benchmark_status": "DIAGNOSTIC_ONLY",
        "corpus_version": "v3.0-real-frozen",
        "document_count": len(docs),
        "case_count": len(final_cases),
        "positive_case_count": positives,
        "no_evidence_case_count": no_evidence,
        "domain_distribution": {},
        "difficulty_distribution": {},
        "risk_distribution": {}
    }
    
    for c in final_cases:
        manifest["domain_distribution"][c["claim_type"]] = manifest["domain_distribution"].get(c["claim_type"], 0) + 1
        manifest["difficulty_distribution"][c["difficulty"]] = manifest["difficulty_distribution"].get(c["difficulty"], 0) + 1
        manifest["risk_distribution"][c["risk_tier"]] = manifest["risk_distribution"].get(c["risk_tier"], 0) + 1
        
    doc_hash = hashlib.sha256(json.dumps(docs, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    case_hash = hashlib.sha256(json.dumps(final_cases, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    gt_hash = hashlib.sha256(json.dumps(ground_truth, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    manifest["corpus_sha256"] = doc_hash
    manifest["dataset_sha256"] = case_hash
    manifest["ground_truth_sha256"] = gt_hash
    
    with open(out_dir / "retrieval_dataset_v3_1_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

if __name__ == "__main__":
    main()