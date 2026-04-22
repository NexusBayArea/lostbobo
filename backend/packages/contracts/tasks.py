from typing import TypedDict, Any

class TaskPayload(TypedDict):
    task: str
    inputs: dict
    context: dict

class TaskResult(TypedDict):
    result: Any
