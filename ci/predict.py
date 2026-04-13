from ci.fix_templates import get_template_for_signature

def predict_fix(signature, memory):
    """
    Predicts a fix based on historical success or template matching.
    Returns: (patch_cmd, confidence)
    """
    # 1. Check historical memory for exact signature matches that succeeded
    for entry in reversed(memory):
        if entry["signature"] == signature and entry.get("success"):
            return entry["patch"], 0.95 # very high confidence

    # 2. Check for partial matches in memory
    for entry in reversed(memory):
        if entry["signature"] in signature and entry.get("success"):
            return entry["patch"], 0.85 # high confidence

    # 3. Fallback to predefined templates
    template = get_template_for_signature(signature)
    if template and template.get("cmd"):
        return template["cmd"], 0.8 # solid template confidence

    return None, 0.0
