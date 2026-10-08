content = open('tests/e2e/test_v1_3_mock.py').read()
import re
content = re.sub(r'if self\.failure_type:.*', 'if self.failure_type:\n            raise Exception(self.failure_type)', content)
open('tests/e2e/test_v1_3_mock.py', 'w').write(content)
