def learn(memory, signature, patch, success):
    """Updates memory with the result of a repair attempt."""
    # Check if we already have this exact entry to avoid spamming
    for entry in memory:
        if entry["signature"] == signature and entry["patch"] == patch:
            entry["success"] = success # Update status
            return memory

    # Add new entry
    memory.append({
        "signature": signature,
        "patch": patch,
        "success": success,
        "timestamp": "now" # In a real system, use ISO timestamp
    })
    
    # Keep memory lean: keep only latest 500 patterns
    if len(memory) > 500:
        memory = memory[-500:]
        
    return memory
