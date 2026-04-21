import json
import sqlite3
import subprocess
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse

from tools.runtime.telemetry import DB_PATH, TelemetryManager

router = APIRouter()
tm = TelemetryManager()

TRACE_FILE = Path(__file__).resolve().parents[5] / "runtime_trace.json"


@router.get("/admin/observability", response_class=HTMLResponse)
def get_dashboard():
    stats = tm.get_baseline_stats()

    # Ensure values are safely formatted for display
    total_runs = stats.get("total_runs", 0)
    p95_latency = stats.get("p95_wall_clock", 0.0)
    avg_gpu = stats.get("avg_gpu", 0.0) or 0.0
    total_cost = stats.get("total_cost", 0.0) or 0.0

    # Simple Tailwind-based UI for zero-footprint modern UX
    return f"""
    <html>
        <head><script src="https://cdn.tailwindcss.com"></script></head>
        <body class="bg-gray-900 text-white p-8">
            <h1 class="text-3xl font-bold mb-6">System Observability: Mercury 2</h1>
            <div class="grid grid-cols-4 gap-4 mb-8">
                <div class="bg-gray-800 p-4 rounded">
                    <p class="text-gray-400 text-sm">Total Runs</p>
                    <p class="text-2xl font-mono">{total_runs}</p>
                </div>
                <div class="bg-gray-800 p-4 rounded">
                    <p class="text-gray-400 text-sm">p95 Latency</p>
                    <p class="text-2xl font-mono">{p95_latency:.2f}s</p>
                </div>
                <div class="bg-gray-800 p-4 rounded">
                    <p class="text-gray-400 text-sm">Avg GPU Util</p>
                    <p class="text-2xl font-mono">{avg_gpu:.1f}%</p>
                </div>
                <div class="bg-gray-800 p-4 rounded">
                    <p class="text-gray-400 text-sm">Total Cost</p>
                    <p class="text-2xl font-mono">${total_cost:.4f}</p>
                </div>
            </div>
            
            <div class="flex gap-4">
                <a href="/admin/traction-proof" class="bg-blue-600 px-4 py-2 rounded hover:bg-blue-500 transition">Download Traction Proof (CSV)</a>
                <form action="/admin/replay/full" method="post" class="inline">
                    <button type="submit" class="bg-gray-700 px-4 py-2 rounded hover:bg-gray-600 transition text-sm">Replay Full DAG</button>
                </form>
            </div>

            <div class="mt-12">
                <h2 class="text-xl font-semibold mb-4 text-gray-400 font-mono">Legacy Trace Data</h2>
                <div class="bg-gray-800 p-4 rounded max-h-64 overflow-auto font-mono text-xs">
                    <pre>{json.dumps(json.loads(TRACE_FILE.read_text()) if TRACE_FILE.exists() else {{"status": "no legacy data"}}, indent=2)}</pre>
                </div>
            </div>
        </body>
    </html>
    """


@router.get("/admin/traction-proof")
def export_csv():
    # Uses pandas to create a clean CSV/Excel-ready table
    if not DB_PATH.exists():
        return Response(content="No data available", media_type="text/plain")

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM runs", conn)

    return Response(
        content=df.to_csv(index=False),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=traction_proof.csv"},
    )


@router.post("/admin/replay")
def replay_failed():
    subprocess.Popen(["python", "tools/runtime/replay.py"])
    return {"status": "started"}


@router.post("/admin/replay/full")
def replay_full():
    subprocess.Popen(["python", "tools/runtime/replay.py", "full"])
    return {"status": "started"}
