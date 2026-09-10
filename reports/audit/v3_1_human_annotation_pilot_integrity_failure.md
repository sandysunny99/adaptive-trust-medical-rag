# V3.1 Human Annotation Pilot Integrity Failure

**Status:**
INVALID HUMAN ANNOTATION EVIDENCE

**Reason:**
The submitted annotation decisions were generated programmatically from a hard-coded annotation dictionary in `scripts/do_pilot_annotation.py` rather than entered by an independent human reviewer.

**Impact:**
The resulting JSON cannot be used as independently curated ground truth because it violates the core rule against programmatic relevance generation.

**Decision:**
V3.1 confirmation remains blocked. The generated files have been preserved but renamed with `INVALID_AS_HUMAN_ANNOTATION` to prevent accidental usage.
