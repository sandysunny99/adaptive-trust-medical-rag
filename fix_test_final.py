content = open('tests/e2e/test_v6_c6_image_confirmation_rxnorm.py').read()
content = content.replace('entities_event = next((e for e in parsed_events if e.get("event") == "normalization"), None)', 'entities_event = next((e for e in parsed_events if e.get("event") == "rxnorm"), None)')
content = content.replace('entities = entities_event["data"]["medications"]', 'entities = entities_event["data"]["entities"]')
open('tests/e2e/test_v6_c6_image_confirmation_rxnorm.py', 'w').write(content)
