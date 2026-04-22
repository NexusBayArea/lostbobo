def should_execute(node, previous_trace, current_contract):
    if previous_trace is None:
        return True

    if previous_trace["contract"] != current_contract:
        return True

    return False
