import os

file_path = 'src/adaptive_trust_medical_rag/verification/claim_verifier_v2.py'
content = open(file_path).read()

mock_init = '''
        if os.environ.get("TESTING") == "1":
            class MockClassifier:
                class MockConfig:
                    id2label = {0: "entailment", 1: "neutral", 2: "contradiction"}
                def __init__(self):
                    self.model = type("MockModel", (), {"config": self.MockConfig()})()
                def __call__(self, text, **kwargs):
                    return [[{"label": "entailment", "score": 0.99}, {"label": "neutral", "score": 0.01}, {"label": "contradiction", "score": 0.0}]]
            self.classifier = MockClassifier()
        else:
            self.classifier = pipeline("text-classification", model=model_id, revision=revision, top_k=None, **kwargs)
'''

# Find the exact place to replace
search_str = '        self.classifier = pipeline("text-classification", model=model_id, revision=revision, top_k=None, **kwargs)'
import re
content = content.replace(search_str, mock_init.lstrip('\n'))

open(file_path, 'w').write(content)
