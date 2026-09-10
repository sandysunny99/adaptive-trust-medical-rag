import json
import csv
from pathlib import Path

def main():
    print("Preparing V3.1-HUMAN Annotation Package...")
    
    with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json") as f:
        docs = json.load(f)
        
    q_data = [
        # Pharmacology (20)
        ("How does metformin inhibit hepatic gluconeogenesis?", "Pharmacology", "R1", "MECHANISM", ["metformin"]),
        ("Clearance pathway for lisinopril", "Pharmacology", "R1", "MECHANISM", ["lisinopril"]),
        ("CYP enzyme responsible for omeprazole metabolism", "Pharmacology", "R1", "CYP_DDI", ["omeprazole"]),
        ("Is levothyroxine absorbed better on an empty stomach?", "Pharmacology", "R1", "MECHANISM", ["levothyroxine"]),
        ("Half-life of citalopram", "Pharmacology", "R1", "MECHANISM", ["citalopram"]),
        ("Mechanism of doxorubicin intercalating DNA", "Pharmacology", "R2", "MECHANISM", ["doxorubicin"]),
        ("Amiodarone distribution in adipose tissue", "Pharmacology", "R1", "MECHANISM", ["amiodarone"]),
        ("Isotretinoin mechanism in acne", "Pharmacology", "R1", "MECHANISM", ["isotretinoin"]),
        ("Acetaminophen toxic metabolite NAPQI", "Pharmacology", "R2", "MECHANISM", ["acetaminophen"]),
        ("Digoxin inhibition of Na-K ATPase", "Pharmacology", "R1", "MECHANISM", ["digoxin"]),
        ("Alendronate bone resorption inhibition", "Pharmacology", "R1", "MECHANISM", ["alendronate"]),
        ("Pantoprazole proton pump inhibition", "Pharmacology", "R1", "MECHANISM", ["pantoprazole"]),
        ("Fluoxetine active metabolite norfluoxetine", "Pharmacology", "R1", "MECHANISM", ["fluoxetine"]),
        ("Sertraline serotonin reuptake blockade", "Pharmacology", "R1", "MECHANISM", ["sertraline"]),
        ("Gabapentin binding to voltage-gated calcium channels", "Pharmacology", "R1", "MECHANISM", ["gabapentin"]),
        ("Tramadol mu-opioid receptor affinity", "Pharmacology", "R1", "MECHANISM", ["tramadol"]),
        ("Celecoxib selective COX-2 inhibition", "Pharmacology", "R1", "MECHANISM", ["celecoxib"]),
        ("Rivaroxaban Factor Xa inhibition", "Pharmacology", "R1", "MECHANISM", ["rivaroxaban"]),
        ("Apixaban pharmacokinetics in renal failure", "Pharmacology", "R1", "MECHANISM", ["apixaban"]),
        ("What is the primary mechanism of action for atorvastatin?", "Pharmacology", "R1", "MECHANISM", ["atorvastatin"]),
        
        # DDI (25)
        ("Concomitant use of warfarin and aspirin bleeding risk", "DDI", "R3", "MULTI_ENTITY", ["warfarin", "aspirin"]),
        ("CYP2C9 interaction between fluconazole and warfarin", "DDI", "R3", "CYP_DDI", ["fluconazole", "warfarin"]),
        ("Spironolactone and lisinopril combination risks", "DDI", "R3", "MULTI_ENTITY", ["spironolactone", "lisinopril"]),
        ("Omeprazole reducing clopidogrel efficacy", "DDI", "R3", "MULTI_ENTITY", ["omeprazole", "clopidogrel"]),
        ("Iron sulfate decreasing levothyroxine absorption", "DDI", "R2", "MULTI_ENTITY", ["levothyroxine", "iron"]),
        ("Pantoprazole interaction with levothyroxine", "DDI", "R2", "MULTI_ENTITY", ["pantoprazole", "levothyroxine"]),
        ("Celecoxib and myocardial infarction risk with NSAIDs", "DDI", "R3", "MULTI_ENTITY", ["celecoxib", "nsaid"]),
        ("Clopidogrel and naproxen GI bleeding", "DDI", "R3", "MULTI_ENTITY", ["clopidogrel", "naproxen"]),
        ("Isotretinoin and tetracycline pseudotumor cerebri", "DDI", "R3", "MULTI_ENTITY", ["isotretinoin", "tetracycline"]),
        ("Digoxin and macrolide toxicity", "DDI", "R3", "MULTI_ENTITY", ["digoxin", "macrolide"]),
        ("Acetaminophen and warfarin INR prolongation", "DDI", "R3", "MULTI_ENTITY", ["acetaminophen", "warfarin"]),
        ("Citalopram and omeprazole QT prolongation", "DDI", "R3", "MULTI_ENTITY", ["citalopram", "omeprazole"]),
        ("Sildenafil contraindication with nitrates", "DDI", "R3", "MULTI_ENTITY", ["sildenafil", "nitrate"]),
        ("Simvastatin and amlodipine myopathy risk", "DDI", "R3", "MULTI_ENTITY", ["simvastatin", "amlodipine"]),
        ("Dabigatran and verapamil bleeding risk", "DDI", "R3", "MULTI_ENTITY", ["dabigatran", "verapamil"]),
        ("Fluoxetine and MAOI serotonin syndrome", "DDI", "R3", "MULTI_ENTITY", ["fluoxetine", "maoi"]),
        ("Lithium and thiazide diuretic toxicity", "DDI", "R3", "MULTI_ENTITY", ["lithium", "thiazide"]),
        ("Carbamazepine autoinduction and oral contraceptives", "DDI", "R2", "MULTI_ENTITY", ["carbamazepine", "contraceptive"]),
        ("Methotrexate and trimethoprim pancytopenia", "DDI", "R3", "MULTI_ENTITY", ["methotrexate", "trimethoprim"]),
        ("Valproate and lamotrigine rash risk", "DDI", "R3", "MULTI_ENTITY", ["valproate", "lamotrigine"]),
        ("Clarithromycin and colchicine toxicity", "DDI", "R3", "CYP_DDI", ["clarithromycin", "colchicine"]),
        ("Rifampin reducing apixaban efficacy", "DDI", "R3", "CYP_DDI", ["rifampin", "apixaban"]),
        ("St John Wort and sertraline interaction", "DDI", "R2", "MULTI_ENTITY", ["john", "sertraline"]),
        ("Grapefruit juice and atorvastatin interaction", "DDI", "R2", "CYP_DDI", ["grapefruit", "atorvastatin"]),
        ("Verapamil and beta blocker heart block", "DDI", "R3", "MULTI_ENTITY", ["verapamil", "beta"]),

        # ADE (20)
        ("Idiosyncratic drug induced liver injury mechanisms", "ADE", "R3", "MECHANISM", ["liver"]),
        ("Spironolactone induced hyperkalemia", "ADE", "R3", "SYNONYM", ["spironolactone"]),
        ("Atorvastatin causing rhabdomyolysis", "ADE", "R3", "SYNONYM", ["atorvastatin"]),
        ("Citalopram and dose dependent QT prolongation", "ADE", "R3", "SYNONYM", ["citalopram"]),
        ("Doxorubicin associated heart failure", "ADE", "R3", "SYNONYM", ["doxorubicin"]),
        ("Amiodarone induced pulmonary fibrosis", "ADE", "R3", "SYNONYM", ["amiodarone"]),
        ("Isotretinoin causing severe birth defects", "ADE", "R3", "SYNONYM", ["isotretinoin"]),
        ("Acetaminophen overdose hepatotoxicity", "ADE", "R3", "SYNONYM", ["acetaminophen"]),
        ("Alendronate causing esophageal ulceration", "ADE", "R2", "SYNONYM", ["alendronate"]),
        ("Fluoxetine increasing suicidal ideation", "ADE", "R3", "SYNONYM", ["fluoxetine"]),
        ("Gabapentin causing excessive somnolence", "ADE", "R1", "SYNONYM", ["gabapentin"]),
        ("Tramadol lowering seizure threshold", "ADE", "R2", "SYNONYM", ["tramadol"]),
        ("Rivaroxaban associated major bleeding", "ADE", "R3", "SYNONYM", ["rivaroxaban"]),
        ("Apixaban associated gastrointestinal bleeding", "ADE", "R3", "SYNONYM", ["apixaban"]),
        ("Dabigatran causing dyspepsia", "ADE", "R1", "SYNONYM", ["dabigatran"]),
        ("Spironolactone causing gynecomastia", "ADE", "R1", "SYNONYM", ["spironolactone"]),
        ("Ibuprofen induced gastric ulcer", "ADE", "R2", "SYNONYM", ["ibuprofen"]),
        ("Salbutamol causing tachycardia", "ADE", "R1", "SYNONYM", ["salbutamol"]),
        ("Lithium toxicity tremor", "ADE", "R2", "SYNONYM", ["lithium"]),
        ("Valproate induced neural tube defects", "ADE", "R3", "SYNONYM", ["valproate"]),
        
        # Medication Safety (15)
        ("Metformin contraindication in severe renal disease", "Medication_Safety", "R3", "PARAPHRASE", ["metformin"]),
        ("Warfarin target INR monitoring", "Medication_Safety", "R3", "PARAPHRASE", ["warfarin"]),
        ("Genetic testing for CYP2C9 variants before prescribing", "Medication_Safety", "R2", "SYNONYM", ["cyp2c9"]),
        ("Diagnosis of drug induced hepatotoxicity", "Medication_Safety", "R3", "PARAPHRASE", ["hepatotoxicity"]),
        ("Lisinopril dosing in renal impairment GFR < 30", "Medication_Safety", "R3", "PARAPHRASE", ["lisinopril"]),
        ("Monitoring for digoxin toxicity", "Medication_Safety", "R2", "PARAPHRASE", ["digoxin"]),
        ("Sertraline safety during pregnancy", "Medication_Safety", "R2", "PARAPHRASE", ["sertraline"]),
        ("Reversal agent for dabigatran", "Medication_Safety", "R3", "SYNONYM", ["dabigatran"]),
        ("Management of severe bleeding on warfarin", "Medication_Safety", "R3", "PARAPHRASE", ["warfarin"]),
        ("Renal dosing adjustments for metformin", "Medication_Safety", "R3", "PARAPHRASE", ["metformin"]),
        ("What monitoring is required for amiodarone liver toxicity?", "Medication_Safety", "R2", "PARAPHRASE", ["amiodarone"]),
        ("Lisinopril contraindicated in angioedema", "Medication_Safety", "R3", "SYNONYM", ["lisinopril"]),
        ("Penicillin anaphylaxis management", "Medication_Safety", "R3", "PARAPHRASE", ["penicillin"]),
        ("Methotrexate folic acid supplementation", "Medication_Safety", "R2", "PARAPHRASE", ["methotrexate"]),
        ("Clozapine agranulocytosis monitoring", "Medication_Safety", "R3", "PARAPHRASE", ["clozapine"])
    ]
    
    cases = []
    for i, (q, t, rt, d, ents) in enumerate(q_data):
        cases.append({
            "case_id": f"v3.1h-{i+1:03d}",
            "query": q,
            "claim_type": t,
            "risk_tier": rt,
            "difficulty": d,
            "expected_entities": ents,
            "annotation_status": "PENDING"
        })
        
    out_dir = Path("experiments/manifests")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / "v3_1_human_cases.json", "w") as f:
        json.dump(cases, f, indent=2)
        
    print(f"Created {len(cases)} cases for V3.1-HUMAN.")
    
    csv_path = out_dir / "v3_1_human_annotation_template.csv"
    with open(csv_path, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "case_id", "query", "claim_type", "risk_tier", "difficulty", 
            "document_id", "chunk_id", "relevance", "evidence_span", 
            "annotation_reason", "authority_tier", "annotator_id", 
            "review_timestamp", "confidence"
        ])
        
        for c in cases:
            # Candidate Pool Strategy: Simple entity metadata match (allowed by rules)
            candidate_docs = []
            for doc in docs:
                text = doc.get("abstract", "")
                if c["expected_entities"][0].lower() in text.lower():
                    candidate_docs.append(doc["document_id"])
            
            # If no candidates found, emit one row to allow marking NO_EVIDENCE
            if not candidate_docs:
                writer.writerow([
                    c["case_id"], c["query"], c["claim_type"], c["risk_tier"], c["difficulty"],
                    "", "", "NO_EVIDENCE", "", "", "", "", "", ""
                ])
            else:
                for doc_id in candidate_docs[:5]: # Limit to top 5 candidates to reduce burden
                    writer.writerow([
                        c["case_id"], c["query"], c["claim_type"], c["risk_tier"], c["difficulty"],
                        doc_id, f"chunk-{doc_id}-001", "PENDING", "", "", "", "", "", ""
                    ])

    print("Created v3_1_human_annotation_template.csv")

if __name__ == "__main__":
    main()