import json
import hashlib
import time
import os
import requests

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

class LLMProviderAdapter:
    def __init__(self, execution_mode, model, structured_output_method="JSON_OBJECT"):
        self.execution_mode = execution_mode
        self.model = model
        self.structured_output_method = structured_output_method
        
        if execution_mode == "DIRECT_GROQ":
            self.gateway = "NONE"
            self.provider = "GROQ"
            self.env_key = "GROQ_API_KEY"
            self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        elif execution_mode == "DIRECT_CLOUDFLARE":
            self.gateway = "NONE"
            self.provider = "CLOUDFLARE"
            self.env_key = "CLOUDFLARE_API_KEY"
            cf_acct = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "MISSING_ACCOUNT_ID")
            self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_acct}/ai/v1/chat/completions"
        elif execution_mode == "DIRECT_HUGGINGFACE":
            self.gateway = "NONE"
            self.provider = "HUGGINGFACE"
            self.env_key = "HUGGINGFACE_API_KEY"
            self.base_url = f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions"
        elif execution_mode == "FREELLMAPI_GATEWAY":
            self.gateway = "FREELLMAPI"
            self.provider = "UNKNOWN_PENDING_RESPONSE" 
            self.env_key = "FREELLMAPI_API_KEY"
            self.base_url = os.environ.get("FREELLMAPI_BASE_URL", "https://api.freellmapi.com/v1/chat/completions")
        else:
            raise ValueError(f"Unknown execution mode: {execution_mode}")
            
    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
        
    def _validate_schema(self, data, schema):
        if HAS_JSONSCHEMA:
            try:
                jsonschema.validate(instance=data, schema=schema)
                return True
            except jsonschema.exceptions.ValidationError as e:
                raise ValueError(f"Schema validation failed: {e.message}")
        else:
            def validate_node(node, s_node, path):
                if "type" in s_node:
                    expected = s_node["type"]
                    if expected == "object":
                        if not isinstance(node, dict): raise ValueError(f"{path} must be object")
                        for req in s_node.get("required", []):
                            if req not in node: raise ValueError(f"Missing required {path}.{req}")
                        for k, v in node.items():
                            if k in s_node.get("properties", {}):
                                validate_node(v, s_node["properties"][k], f"{path}.{k}")
                    elif expected == "array":
                        if not isinstance(node, list): raise ValueError(f"{path} must be array")
                        for i, item in enumerate(node):
                            validate_node(item, s_node.get("items", {}), f"{path}[{i}]")
                    elif expected == "string":
                        if not isinstance(node, str) and not (s_node.get("nullable", False) and node is None):
                            raise ValueError(f"{path} must be string")
                    elif expected == "integer":
                        if not isinstance(node, int) and not (s_node.get("nullable", False) and node is None):
                            raise ValueError(f"{path} must be integer")
                    
                    if "enum" in s_node:
                        if node not in s_node["enum"] and not (s_node.get("nullable", False) and node is None):
                            raise ValueError(f"{path} must be one of {s_node['enum']}")
            
            validate_node(data, schema, "root")
            return True

    def generate_structured(self, system_prompt, user_prompt, schema, generation_config):
        evidence_text = generation_config.get("evidence_text", "")
        temperature = generation_config.get("temperature", 0.0)
        top_p = generation_config.get("top_p", 0.1)
        max_tokens = generation_config.get("max_tokens", 2048)
        seed = generation_config.get("seed", 42)
        timeout = generation_config.get("timeout", 120)
        
        start_time = time.time()
        sys_hash = self._hash(system_prompt)
        usr_hash = self._hash(user_prompt)
        ev_hash = self._hash(evidence_text)
        
        canon_schema = json.dumps(schema, sort_keys=True, separators=(',', ':'))
        
        result = {
            "success": False,
            "provider": self.provider,
            "gateway": self.gateway,
            "model": self.model,
            "model_revision": "UNKNOWN",
            "request_id": "UNKNOWN",
            "latency_ms": 0,
            "retry_count": 0,
            "fallback_attempts": "0",
            "routing_changed": False,
            "prompt_hash": sys_hash,
            "schema_hash": self._hash(canon_schema),
            "response_sha256": None,
            "parsed_output": None,
            "error_type": None,
            "error_message": None,
            "system_prompt_sha256": sys_hash,
            "user_prompt_sha256": usr_hash,
            "evidence_sha256": ev_hash,
            "evidence_character_count": len(evidence_text),
            "structured_output_method": self.structured_output_method
        }
        
        if self.execution_mode == "DIRECT_CLOUDFLARE" and "MISSING_ACCOUNT_ID" in self.base_url:
            result["error_type"] = "CONFIGURATION_ERROR"
            result["error_message"] = "CLOUDFLARE_ACCOUNT_ID environment variable is missing"
            result["latency_ms"] = int((time.time() - start_time) * 1000)
            return result

        api_key = os.environ.get(self.env_key)
        if not api_key:
            result["error_type"] = "AUTHENTICATION_ERROR"
            result["error_message"] = "MISSING_PROVIDER_CREDENTIAL"
            result["latency_ms"] = int((time.time() - start_time) * 1000)
            return result

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{user_prompt}\\n\\nEvidence:\\n{evidence_text}"}
            ],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens
        }
        
        if self.structured_output_method == "NATIVE_JSON_SCHEMA":
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "semantic_adjudication",
                    "strict": True,
                    "schema": schema
                }
            }
        elif self.structured_output_method == "JSON_OBJECT":
            payload["response_format"] = {"type": "json_object"}
            
        if seed is not None: payload["seed"] = seed
        
        max_retries = 3
        raw_text = None
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(self.base_url, headers=headers, json=payload, timeout=timeout)
                
                if self.gateway == "FREELLMAPI":
                    resolved_provider = response.headers.get("X-Routed-Via", "UNKNOWN")
                    fallbacks = response.headers.get("X-Fallback-Attempts", "0")
                    result["provider"] = resolved_provider
                    result["fallback_attempts"] = fallbacks
                    result["request_id"] = response.headers.get("x-request-id", "UNKNOWN")
                    if fallbacks != "0" or resolved_provider == "UNKNOWN":
                        result["routing_changed"] = True
                
                if response.status_code == 400:
                    result["error_type"] = "INVALID_REQUEST"
                    result["error_message"] = response.text
                    break
                elif response.status_code in (401, 403):
                    result["error_type"] = "AUTHENTICATION_ERROR"
                    result["error_message"] = "Provider rejected credentials"
                    break
                elif response.status_code == 404:
                    result["error_type"] = "MODEL_NOT_FOUND"
                    result["error_message"] = "The requested model was not found"
                    break
                elif response.status_code == 429:
                    raise requests.exceptions.RequestException("RATE_LIMIT")
                    
                response.raise_for_status()
                
                data = response.json()
                raw_text = data["choices"][0]["message"]["content"]
                result["response_sha256"] = self._hash(raw_text)
                break
                
            except requests.exceptions.Timeout as e:
                result["retry_count"] = attempt
                result["error_type"] = "TIMEOUT"
                result["error_message"] = str(e)
                if attempt == max_retries: break
                time.sleep(2 ** attempt)
            except requests.exceptions.RequestException as e:
                result["retry_count"] = attempt
                err_str = str(e).lower()
                if "rate_limit" in err_str or "429" in err_str:
                    result["error_type"] = "RATE_LIMIT"
                else:
                    result["error_type"] = "CONNECTION_ERROR"
                result["error_message"] = str(e)
                if attempt == max_retries: break
                time.sleep(2 ** attempt)
            except Exception as e:
                result["retry_count"] = attempt
                result["error_type"] = "PROVIDER_ERROR"
                result["error_message"] = str(e)
                if attempt == max_retries: break
                time.sleep(2 ** attempt)
        
        if raw_text:
            try:
                parsed = json.loads(raw_text)
                self._validate_schema(parsed, schema)
                
                # INTEGRATION: ENFORCE LABEL-GRADE CONSISTENCY
                label = parsed.get("proposed_label")
                grade = parsed.get("proposed_grade")
                valid_mappings = {
                    "RELEVANT": 2,
                    "PARTIALLY_RELEVANT": 1,
                    "IRRELEVANT": 0,
                    "INSUFFICIENT_INFORMATION": 0,
                    "AMBIGUOUS": None
                }
                if label in valid_mappings:
                    if grade != valid_mappings[label]:
                        result["error_type"] = "SEMANTIC_SCHEMA_CONSISTENCY_FAILED"
                        result["error_message"] = f"Label '{label}' requires grade '{valid_mappings[label]}', got '{grade}'."
                        result["success"] = False
                        result["latency_ms"] = int((time.time() - start_time) * 1000)
                        return result

                # INTEGRATION: ENFORCE EXACT SPAN VALIDATION
                best_span = parsed.get("best_supporting_span", "")
                if label in ["IRRELEVANT", "INSUFFICIENT_INFORMATION", "AMBIGUOUS"] and best_span == "":
                    pass # Valid empty span for non-relevant
                elif best_span:
                    if evidence_text.find(best_span) < 0:
                        result["error_type"] = "SPAN_VALIDATION_FAILED"
                        result["error_message"] = "best_supporting_span not found exactly in evidence"
                        result["success"] = False
                        result["latency_ms"] = int((time.time() - start_time) * 1000)
                        return result
                elif label in ["RELEVANT", "PARTIALLY_RELEVANT"] and not best_span:
                    result["error_type"] = "SPAN_VALIDATION_FAILED"
                    result["error_message"] = "best_supporting_span required for relevant labels"
                    result["success"] = False
                    result["latency_ms"] = int((time.time() - start_time) * 1000)
                    return result
                    
                claims = parsed.get("evidence_claims", [])
                for claim in claims:
                    span = claim.get("evidence_span", "")
                    if span and evidence_text.find(span) < 0:
                        result["error_type"] = "SPAN_VALIDATION_FAILED"
                        result["error_message"] = f"evidence_claim span '{span}' not found in evidence"
                        result["success"] = False
                        result["latency_ms"] = int((time.time() - start_time) * 1000)
                        return result
                        
                result["parsed_output"] = parsed
                result["success"] = True
                result["error_type"] = None
                result["error_message"] = None
                
            except json.JSONDecodeError as e:
                result["error_type"] = "MALFORMED_JSON"
                result["error_message"] = str(e)
            except ValueError as e:
                result["error_type"] = "SCHEMA_VALIDATION_FAILED"
                result["error_message"] = str(e)
                
        result["latency_ms"] = int((time.time() - start_time) * 1000)
        return result
