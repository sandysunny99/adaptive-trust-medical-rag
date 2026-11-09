# Patient Context Safety Specification

## Core Safety Rule

> **NEVER infer a patient's underlying condition from a prescription image, drug name, age estimate, appearance, OCR output, or LLM reasoning.**

Patient-specific recommendations are based ONLY on explicitly supplied patient context and retrieved evidence.

## Allowed Patient Context Fields

### Basic (Progressive Disclosure)
| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `age` | integer | No | Age-related dosing/safety |
| `sex` | string | No | Sex-specific considerations |
| `known_allergies` | string[] | No | Allergy cross-reactivity |
| `known_conditions` | string[] | No | Condition-specific warnings |
| `current_medications` | string[] | No | Additional DDI detection |

### Advanced (Expandable)
| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `pregnancy_status` | enum | No | Pregnancy category check |
| `breastfeeding` | boolean | No | Lactation safety |
| `kidney_impairment` | enum | No | Renal dosing |
| `liver_impairment` | enum | No | Hepatic considerations |
| `diabetes` | boolean | No | Glucose interaction |
| `hypertension` | boolean | No | CV drug interaction |
| `dietary_restrictions` | string[] | No | Food interaction context |

## Safety Rules

### Rule 1: No Condition Inference
```
❌ PROHIBITED:
  "Since you are taking metformin, you likely have diabetes..."
  "Based on your prescription for lisinopril, your blood pressure..."

✅ ALLOWED:
  "Patient-specific assessment is limited because relevant 
   patient information was not provided."
```

### Rule 2: No Dose Modification
```
❌ PROHIBITED:
  "Take 250mg instead of 500mg due to your kidney condition."
  "Skip the evening dose."
  "Take at 8 AM and 8 PM."

✅ ALLOWED:
  "The retrieved labeling indicates that dose adjustment may be 
   required for patients with renal impairment. Discuss with 
   prescribing clinician."
```

### Rule 3: No Prescription Changes
The system MUST NOT:
- Change dose
- Change frequency
- Change route
- Change duration
- Stop a medication
- Start a new medication
- Substitute another drug

### Rule 4: Evidence-Only Patient Guidance
```
For kidney impairment + Drug A:
  1. Patient provides: "I have kidney disease"
  2. System queries: "Drug A renal considerations"
  3. Retrieved evidence: FDA label says "reduce dose in CrCl < 30"
  4. System displays: "According to the FDA label, [Drug A] requires 
     renal consideration. Discuss with clinician. [Source: DailyMed]"
  5. System does NOT independently calculate a new dose.
```

### Rule 5: Missing Context = Limited Assessment
When patient context is missing for a relevant consideration:
```
"Kidney function is relevant to evaluating this medication, 
 but no kidney status was provided. Patient-specific guidance 
 is therefore limited."
```
This is a successful safety behavior, not an error.

## Food/Administration Safety

### Allowed
- Restate evidence-supported administration guidance
- "The retrieved labeling supports taking this medicine with food."

### Prohibited
- Invent meal plans
- Create personalized dosing schedules
- Convert generic guidance into specific times
- Generate dietary recommendations without evidence

### Missing Evidence
```
"Specific food guidance could not be verified from the 
 retrieved evidence."
```
