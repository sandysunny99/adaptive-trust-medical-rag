import os

def instantiate_prompt(template_content: str, **kwargs) -> str:
    """
    Safely instantiates a frozen prompt template by exclusively replacing
    declared placeholders. Preserves literal JSON braces exactly.
    """
    declared_placeholders = {
        "query",
        "patient_context",
        "risk_tier",
        "evidence_block"
    }
    
    # Check for missing values
    missing = declared_placeholders - set(kwargs.keys())
    if missing:
        raise ValueError(f"Missing required placeholders: {missing}")
        
    # Check for unexpected values
    extra = set(kwargs.keys()) - declared_placeholders
    if extra:
        raise ValueError(f"Unexpected extra placeholders provided: {extra}")
        
    # Perform exact string replacement for each declared placeholder
    instantiated = template_content
    for key in declared_placeholders:
        placeholder = f"{{{key}}}"
        if placeholder not in template_content:
            # If a declared placeholder isn't found, that's fine if the template 
            # deliberately omitted it, but our V1.2 template requires all of them.
            raise ValueError(f"Placeholder {placeholder} not found in template.")
        
        val = str(kwargs[key])
        instantiated = instantiated.replace(placeholder, val)
        
    return instantiated
