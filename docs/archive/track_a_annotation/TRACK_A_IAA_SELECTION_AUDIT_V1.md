# TRACK_A_IAA_SELECTION_AUDIT_V1

## Selection Determinism
To ensure the IAA overlap set is 100% reproducible regardless of input file line ordering, the dataset of 530 records was first canonically sorted by `position_id`.

## Selection Parameters
- **Seed**: 42
- **Canonical Sort Key**: `position_id`
- **Selection Algorithm**: `random.sample(records_sorted, 50)`
- **Subset Size**: 50

*Note: The size of 50 is an implementation choice to ensure an adequate statistical sample for Cohen's Kappa, as a specific number was not mandated in the original metric definitions.*