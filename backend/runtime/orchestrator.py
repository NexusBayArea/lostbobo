from backend.runtime.dag_executor import execute_dag
from backend.runtime.execution_intelligence import INTELLIGENCE
from backend.runtime.visualizer import print_dag_ascii


class SimHPCOrchestrator:
    def __init__(self):
        self.intelligence = INTELLIGENCE

    async def run_full_pipeline(self, mode: str = "production"):
        print(f"\nStarting SimHPC Full Pipeline ({mode.upper()})")

        print_dag_ascii()

        analysis = self.intelligence.full_analysis()
        print("Intelligence Report:", analysis)

        trace = await execute_dag()

        print(f"\nPipeline completed! Trace: {trace.timestamp}")
        return trace


ORCHESTRATOR = SimHPCOrchestrator()
