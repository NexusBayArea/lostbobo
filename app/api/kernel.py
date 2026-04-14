"""
API Entry Point — FastAPI server exposing execution contract

This is the ONLY public interface to the execution engine.
All requests go through strict schema validation.
"""

import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.contract import (
    RunRequest,
    RunResponse,
    HealthResponse,
    error_response,
    API_VERSION,
)
from app.runtime.dag import DAG, Node
from app.runtime.compiler import compile_dag
from app.runtime.executor import Executor
from app.runtime.dispatch import dispatch
from worker import tasks as task_registry

app = FastAPI(title="SimHPC Execution API", version=API_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


TASK_REGISTRY = {
    "task_a": task_registry.task_a,
    "task_b": task_registry.task_b,
    "task_multiply": task_registry.task_multiply,
    "task_sum": task_registry.task_sum,
}


def build_dag_from_request(dag_def: dict) -> DAG:
    dag = DAG()
    for name, node_def in dag_def.items():
        fn = TASK_REGISTRY.get(node_def.fn)
        if not fn:
            raise ValueError(f"Unknown task: {node_def.fn}")
        dag.add(name, fn, node_def.deps or [])
    return dag


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", version=API_VERSION)


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest):
    start = time.time()

    try:
        dag = build_dag_from_request(req.dag)

        plan = compile_dag(dag)

        executor = Executor(plan)
        results = executor.run(dispatch, context=req.context)

        return RunResponse(
            results=results, execution_time_ms=(time.time() - start) * 1000, status="ok"
        )

    except Exception as e:
        return error_response(str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
