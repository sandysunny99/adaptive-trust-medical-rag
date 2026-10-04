# MIXED-EVIDENCE AUDIT

When multiple evidence items exist for a single claim:
- If `max_con > max_ent`, it contradicts.
- If `best_ent_chunk != best_con_chunk` (one chunk entails, another contradicts strongly), the system detects tension and assigns `FinalSupportState.AMBIGUOUS`.
- This triggers `GateDecision.abstain`.
- **Conclusion**: The system correctly prioritizes medical safety by preventing a supportive chunk from erasing a contradictory chunk.
