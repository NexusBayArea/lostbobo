from typing import Any

from fastapi import FastAPI, HTTPException

from backend.tools.runtime.contract import compute_contract
from backend.tools.runtime.explain import explain
from backend.tools.runtime.lineage import build_lineage
from backend.tools.runtime.planner import plan_execution
from backend.tools.runtime.trace import load

app = FastAPI(title="SimHPC Execution Compiler API")

WORKSPACE = "/tmp/simhpc"


@app.post("/plan")
async def get_plan(nodes: list[dict[str, Any]]):
    try:
        return plan_execution(nodes, WORKSPACE)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/report")
async def get_report(nodes: list[dict[str, Any]]):
    try:
        plan = plan_execution(nodes, WORKSPACE)
        contracts = {n["id"]: compute_contract(n) for n in nodes}

        prev_contracts = {}
        for n in nodes:
            t = load(n["id"], WORKSPACE)
            prev_contracts[n["id"]] = t["contract"] if t else None

        lineage = build_lineage(nodes, contracts)
        report = {}

        for n in nodes:
            nid = n["id"]
            report[nid] = {
                "will_run": nid in plan["dirty"],
                "reason": explain(nid, plan, prev_contracts, contracts, lineage),
                "deps": n.get("deps", []),
            }
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
