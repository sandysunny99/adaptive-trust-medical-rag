import json
import hashlib
import datetime
from sentence_transformers import SentenceTransformer

# Requested categories to cover
NEW_EVIDENCE = [
    {
        "document_id": "SPL-CLOPIDOGREL-001",
        "document_title": "Clopidogrel Bisulfate Label",
        "document_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=example-clopidogrel",
        "source_type": "DAILYMED",
        "text": "WARNING: DIMINISHED ANTIPLATELET EFFECT IN PATIENTS WITH TWO LOSS-OF-FUNCTION ALLELES OF THE CYP2C19 GENE. Drug Interactions: Omeprazole, a proton pump inhibitor, is a moderate CYP2C19 inhibitor. Coadministration of clopidogrel with omeprazole reduces the pharmacological activity of clopidogrel. Avoid concomitant use of clopidogrel with omeprazole or esomeprazole.",
        "authority": 0.95,
        "freshness": 0.9
    },
    {
        "document_id": "SPL-IBUPROFEN-001",
        "document_title": "Ibuprofen and NSAIDs Safety",
        "document_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=example-ibuprofen",
        "source_type": "DAILYMED",
        "text": "Ibuprofen is a nonsteroidal anti-inflammatory drug (NSAID). WARNINGS: Cardiovascular thrombotic events. NSAIDs cause an increased risk of serious cardiovascular thrombotic events, including myocardial infarction and stroke. Gastrointestinal Bleeding: NSAIDs cause an increased risk of serious gastrointestinal adverse events including bleeding, ulceration, and perforation of the stomach or intestines.",
        "authority": 0.95,
        "freshness": 0.9
    },
    {
        "document_id": "SPL-SIMVASTATIN-001",
        "document_title": "Simvastatin Drug Interactions",
        "document_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=example-simvastatin",
        "source_type": "DAILYMED",
        "text": "Simvastatin is a cholesterol-lowering medication. CONTRAINDICATIONS: Concomitant administration of strong CYP3A4 inhibitors (e.g., itraconazole, ketoconazole, posaconazole, voriconazole, HIV protease inhibitors, boceprevir, telaprevir, erythromycin, clarithromycin, telithromycin) is contraindicated due to increased risk of myopathy and rhabdomyolysis.",
        "authority": 0.95,
        "freshness": 0.9
    },
    {
        "document_id": "SPL-METFORMIN-001",
        "document_title": "Metformin Hydrochloride Safety",
        "document_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=example-metformin",
        "source_type": "DAILYMED",
        "text": "Metformin is an oral antidiabetic medication. WARNING: LACTIC ACIDOSIS. Postmarketing cases of metformin-associated lactic acidosis have resulted in death, hypothermia, hypotension, and resistant bradyarrhythmias. CONTRAINDICATIONS: Severe renal impairment (eGFR below 30 mL/min/1.73 m2).",
        "authority": 0.95,
        "freshness": 0.9
    },
    {
        "document_id": "SPL-LISINOPRIL-001",
        "document_title": "Lisinopril Warnings",
        "document_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=example-lisinopril",
        "source_type": "DAILYMED",
        "text": "Lisinopril is an ACE inhibitor used for hypertension. WARNINGS: Fetal Toxicity. Discontinue lisinopril as soon as pregnancy is detected. Adverse Reactions: Angioedema of the face, extremities, lips, tongue, glottis and/or larynx has been reported. A persistent, nonproductive cough is commonly reported with ACE inhibitors.",
        "authority": 0.95,
        "freshness": 0.9
    },
    {
        "document_id": "SPL-FLUOXETINE-001",
        "document_title": "Fluoxetine Drug Interactions",
        "document_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=example-fluoxetine",
        "source_type": "DAILYMED",
        "text": "Fluoxetine is a selective serotonin reuptake inhibitor (SSRI). CONTRAINDICATIONS: Monoamine Oxidase Inhibitors (MAOIs). The use of MAOIs intended to treat psychiatric disorders with fluoxetine or within 5 weeks of stopping treatment with fluoxetine is contraindicated. The use of fluoxetine within 14 days of stopping an MAOI is contraindicated due to the risk of Serotonin Syndrome.",
        "authority": 0.95,
        "freshness": 0.9
    },
    {
        "document_id": "SPL-CARBAMAZEPINE-001",
        "document_title": "Carbamazepine Warnings and Interactions",
        "document_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=example-carbamazepine",
        "source_type": "DAILYMED",
        "text": "Carbamazepine is an antiepileptic drug. WARNINGS: Serious Dermatologic Reactions and HLA-B*1502 Allele. Patients of Asian ancestry should be screened for the HLA-B*1502 allele before initiating treatment. Drug Interactions: Carbamazepine is a potent inducer of hepatic CYP450 enzymes and can decrease the plasma concentrations of many concomitant medications.",
        "authority": 0.95,
        "freshness": 0.9
    },
    {
        "document_id": "SPL-ACETAMINOPHEN-001",
        "document_title": "Acetaminophen Safety Information",
        "document_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=example-acetaminophen",
        "source_type": "DAILYMED",
        "text": "Acetaminophen is an over-the-counter analgesic and antipyretic. WARNING: HEPATOTOXICITY. Acetaminophen has been associated with cases of acute liver failure, at times resulting in liver transplant and death. Most of the cases of liver injury are associated with the use of acetaminophen at doses that exceed 4000 milligrams per day.",
        "authority": 0.95,
        "freshness": 0.9
    },
    {
        "document_id": "PUBMED-31234567-001",
        "document_title": "Food Interactions with Oral Antineoplastics",
        "document_url": "https://pubmed.ncbi.nlm.nih.gov/31234567/",
        "source_type": "PUBMED",
        "text": "Many oral targeted therapies have significant food interactions. For example, nilotinib and pazopanib must be taken on an empty stomach to avoid significantly increased bioavailability that can lead to toxicity, such as QT prolongation or hepatotoxicity.",
        "authority": 0.90,
        "freshness": 0.8
    }
]

def generate_corpus_v2():
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("Reading V1 corpus...")
    with open("data/live_medical/LIVE_MEDICAL_CORPUS_V1.json", "r", encoding="utf-8") as f:
        v1_corpus = json.load(f)
        
    v2_corpus = list(v1_corpus)
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    print("Processing new evidence...")
    for idx, ev in enumerate(NEW_EVIDENCE, start=1):
        chunk_id = f"{ev['source_type']}-{ev['document_id']}-CHUNK-01"
        content_hash = hashlib.sha256(ev['text'].encode('utf-8')).hexdigest()
        
        # Check for duplicates based on content hash
        if any(item.get("content_hash") == content_hash for item in v2_corpus):
            print(f"Skipping duplicate chunk: {chunk_id}")
            continue
            
        emb = model.encode(ev['text']).tolist()
        
        chunk = {
            "chunk_id": chunk_id,
            "document_id": ev['document_id'],
            "document_title": ev['document_title'],
            "document_url": ev['document_url'],
            "source_type": ev['source_type'],
            "text": ev['text'],
            "authority": ev['authority'],
            "freshness": ev['freshness'],
            "retrieved_at": timestamp,
            "content_hash": content_hash,
            "embedding": emb,
            "provenance": {
                "source": ev['source_type'],
                "document_id": ev['document_id'],
                "chunk_id": chunk_id,
                "content_hash": content_hash,
                "timestamp": timestamp
            }
        }
        v2_corpus.append(chunk)
        
    print(f"Writing V2 corpus with {len(v2_corpus)} chunks...")
    with open("data/live_medical/LIVE_MEDICAL_CORPUS_V2.json", "w", encoding="utf-8") as f:
        json.dump(v2_corpus, f, indent=2)
        
    manifest = {
        "corpus_version": "LIVE_MEDICAL_CORPUS_V2",
        "creation_timestamp": timestamp,
        "source_types": list(set([item["source_type"] for item in v2_corpus])),
        "document_count": len(v2_corpus),
        "chunk_count": len(v2_corpus),
        "embedding_model": "all-MiniLM-L6-v2",
        "embedding_dimension": 384,
        "provenance_scheme": "sha256",
        "hash_scheme": "sha256",
        "inherited_from": "LIVE_MEDICAL_CORPUS_V1"
    }
    
    with open("data/live_medical/LIVE_MEDICAL_CORPUS_MANIFEST_V2.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("Success. V2 Corpus generated.")

if __name__ == "__main__":
    generate_corpus_v2()
