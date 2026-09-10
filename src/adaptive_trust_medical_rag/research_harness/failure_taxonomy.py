"""
Research Harness: Failure Taxonomy

Defines a strongly typed classification for system and experimental failures.
"""

import json
from dataclasses import asdict, dataclass
from enum import Enum


class FailureCategory(Enum):
    """Categorizes the nature of a failure."""
    NON_BLOCKING_MECHANICAL = "NON_BLOCKING_MECHANICAL"
    BLOCKING_ANNOTATION = "BLOCKING_ANNOTATION"
    BLOCKING_METHODOLOGICAL = "BLOCKING_METHODOLOGICAL"


class Severity(Enum):
    """Severity level of the failure."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class FailureIssue:
    """Represents a categorized failure issue."""
    issue_id: str
    category: FailureCategory
    severity: Severity
    description: str
    blocking: bool

    def to_dict(self) -> dict:
        d = asdict(self)
        d['category'] = self.category.value
        d['severity'] = self.severity.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'FailureIssue':
        return cls(
            issue_id=data['issue_id'],
            category=FailureCategory(data['category']),
            severity=Severity(data['severity']),
            description=data['description'],
            blocking=data['blocking']
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    def __str__(self) -> str:
        block_str = "BLOCKING" if self.blocking else "NON-BLOCKING"
        return f"[{self.category.name} - {self.severity.name} - {block_str}] {self.description}"
