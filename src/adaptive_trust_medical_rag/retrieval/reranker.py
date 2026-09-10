from typing import Protocol

from sentence_transformers import CrossEncoder


class Reranker(Protocol):
    def score(self, query: str, passages: list[str]) -> list[float]:
        ...

class CrossEncoderReranker:
    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.model = CrossEncoder(model_name, device=device)

    def score(self, query: str, passages: list[str]) -> list[float]:
        if not passages:
            return []
        pairs = [(query, p) for p in passages]
        scores = self.model.predict(pairs)
        return scores.tolist()
