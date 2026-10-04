# PRE-COMMIT REGISTRY DECISION

1. **What exactly is TRACK_A_CANONICAL_REGISTRY_V2.json?**
It is a reservation lifecycle registry, tracking reservation state independently from the main canonical annotation state.

2. **Why does it contain 530 PID entries?**
It maps every known PID to a reservation lifecycle status.

3. **What are all actual reservation_status values?**
{"COMMITTED": 141, "UNRESERVED": 389}

4. **Which exact 141 PIDs explain the unexplained count?**
See `TRACK_A_REGISTRY_141_UNACCOUNTED_PIDS.json`. The intersection with canonical committed is 141.

5. **Do those 141 correspond exactly to canonical committed records?**
Intersection: 141, Canonical Only: 0, Registry Only: 0.

6. **Semantic distinction:**
`annotation_status` = Human/LLM scientific decision lifecycle
`commit_status` = Persistence lifecycle
`reservation_status` = Operational workflow / batch distribution lifecycle

7. **Registry type:**
It is a reservation state machine.

8. **Window 01 requirements:**
Window 01 PIDs currently hold reservation_status = 'UNRESERVED' in the registry.

9. **Is Window 01 safe?**
Since intersection is 141 out of 141, it implies Window 01 can be committed, provided we know how to handle the registry transition for those 10 PIDs.

Decision: REGISTRY_VALID_FOR_WINDOW01
