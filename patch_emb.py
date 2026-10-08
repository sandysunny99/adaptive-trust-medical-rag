import os

file_path = 'src/adaptive_trust_medical_rag/services/live_application.py'
content = open(file_path).read()

mock_emb = '''
                    if os.environ.get("TESTING") == "1":
                        class MockSentenceTransformer:
                            def encode(self, texts):
                                import numpy as np
                                return np.random.rand(len(texts), 384)
                        self.model = MockSentenceTransformer()
                    else:
                        from sentence_transformers import SentenceTransformer
                        self.model = SentenceTransformer("all-MiniLM-L6-v2")
'''

search_str = '''                        from sentence_transformers import SentenceTransformer
                        self.model = SentenceTransformer("all-MiniLM-L6-v2")'''
content = content.replace(search_str, mock_emb.lstrip('\n'))

open(file_path, 'w').write(content)
