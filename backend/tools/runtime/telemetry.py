import sqlite3
from pathlib import Path
from typing import Any

# Adjusting DB_PATH to be in the project root/data
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "telemetry.sqlite"
RUNPOD_HOURLY_RATE = 0.44  # Example rate for an A6000


class TelemetryManager:
    def __init__(self):
        DB_PATH.parent.mkdir(exist_ok=True, parents=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    project_type TEXT,
                    sim_type TEXT,
                    wall_clock_sec REAL,
                    gpu_util_avg REAL,
                    cost_usd REAL,
                    status TEXT
                )
            """)

    def record_run(
        self, project: str, sim_type: str, duration: float, gpu_util: float, status: str
    ):
        cost = (duration / 3600) * RUNPOD_HOURLY_RATE
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO runs (project_type, sim_type, wall_clock_sec, gpu_util_avg, cost_usd, status) VALUES (?, ?, ?, ?, ?, ?)",
                (project, sim_type, duration, gpu_util, cost, status),
            )

    def get_baseline_stats(self) -> dict[str, Any]:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            # p95 Calculation
            cursor = conn.execute("SELECT wall_clock_sec FROM runs ORDER BY wall_clock_sec ASC")
            times = [r[0] for r in cursor.fetchall()]

            if not times:
                return {
                    "total_runs": 0,
                    "avg_gpu": 0.0,
                    "total_cost": 0.0,
                    "avg_time": 0.0,
                    "p95_wall_clock": 0.0,
                }

            p95_index = int(len(times) * 0.95)
            # Ensure index is within bounds
            p95_index = min(p95_index, len(times) - 1)
            p95 = times[p95_index]

            stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_runs,
                    AVG(gpu_util_avg) as avg_gpu,
                    SUM(cost_usd) as total_cost,
                    AVG(wall_clock_sec) as avg_time
                FROM runs
            """).fetchone()

            res = dict(stats)
            res["p95_wall_clock"] = p95
            return res
