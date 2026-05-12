from enum import Enum


class Capability(str, Enum):
    STATE_READ = "state.read"
    STATE_MUTATE = "state.mutate"
    EVENT_SUBSCRIBE = "event.subscribe"
    EVENT_EMIT = "event.emit"
    FORECAST_WRITE = "forecast.write"
    GRAPH_READ = "graph.read"
    GRAPH_MUTATE = "graph.mutate"
    AGENT_REGISTER = "agent.register"
    DAG_EXECUTE = "dag.execute"
    RESOURCE_QUERY = "resource.query"
    EXECUTION_SUBMIT = "execution.submit"
    EXECUTION_CANCEL = "execution.cancel"
    EXECUTION_STATUS = "execution.status"
    SCHEDULER_SCHEDULE = "scheduler.schedule"
    SCHEDULER_RELEASE = "scheduler.release"
    SCHEDULER_QUERY = "scheduler.query"
