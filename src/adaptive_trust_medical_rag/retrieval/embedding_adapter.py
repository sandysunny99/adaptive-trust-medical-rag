from abc import ABC, abstractmethod


class EmbeddingModel(ABC):
    @abstractmethod
    def encode(self, texts: list[str]) -> list[list[float]]:
        pass

    def encode_query(self, text: str) -> list[float]:
        return self.encode([text])[0]

    def encode_document(self, text: str) -> list[float]:
        return self.encode([text])[0]

    def encode_documents(self, texts: list[str]) -> list[list[float]]:
        return self.encode(texts)
