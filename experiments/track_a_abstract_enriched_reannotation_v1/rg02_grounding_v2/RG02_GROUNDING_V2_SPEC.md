# RG-02 TARGETED RELATIONSHIP GROUNDING REDESIGN (V2) SPECIFICATION

## 1. Problem
The original RelationshipGroundingValidator (V1) relied on purely lexical entity existence and simplistic keyword matching against the candidate text alone. It did not condition its expectations on the user's query intent. 
For case RG-02 (Candidate: "Statin is a drug. Cyanide is a poison.", Query: "Statin is a drug. Cyanide is a poison."), the V1 validator passed the text because it lacked relationship keywords, failing to realize that the scenario implicitly requested a relationship check or that irrelevant factual co-occurrence should be blocked in a DDI context.

## 2. Formal Grounding Definition
Relationship Grounding = whether the candidate evidence actually supports the relationship/assertion relevant to the user's query intent.
* If a query asks for a relationship, the candidate MUST provide a supported relationship.
* If the candidate introduces an unsupported relationship, it MUST be blocked.

## 3. Query Relation Extraction
We analyze the query to extract Entities and Relation Type.
If relation keywords exist (e.g., "interacts", "contraindicated"), 
equires_relation = True.
If multiple pharmacological entities exist without a keyword, it is classified as IMPLICIT_MULTI_ENTITY (meaning 
equires_relation = True).

## 4. Candidate Relation Extraction
Extracts entities and relation keywords from the candidate chunk.

## 5. Entity Alignment & Source Support
Checks if the entities participating in the relationship match the source.
Evaluates source text for contradictory relationship keywords.

## 6. Decision Table
| Query Requires Relation | Candidate Relation | Source Support | Decision |
|--------------------------|-------------------|----------------|----------|
| NO | N/A | N/A | CONTINUE (SUPPORTED) |
| YES | None | None | BLOCK (NO_RELEVANT_RELATION) |
| YES | Unsupported | None | BLOCK (UNSUPPORTED) |
| YES | Supported | Yes | CONTINUE (SUPPORTED) |
| YES | Contradicted | No | BLOCK (CONTRADICTED) |
| YES | Ambiguous | Unclear | BLOCK (AMBIGUOUS - Fail Closed) |

## 7. Gate Integration
The EvidenceEligibilityGate was updated to explicitly reject candidates with UNSUPPORTED, CONTRADICTED, NO_RELEVANT_RELATION, or AMBIGUOUS grounding statuses.
