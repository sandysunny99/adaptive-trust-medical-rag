content = open('tests/e2e/test_v6_c6_image_confirmation_rxnorm.py').read()
content = content.replace('parsed_events = extract_sse_events(lines)', 'parsed_events = extract_sse_events(lines)\n        print("PARSED:", parsed_events)')
open('tests/e2e/test_v6_c6_image_confirmation_rxnorm.py', 'w').write(content)
