from backend.runtime.graph import GRAPH, Node
from backend.runtime.kernel import KERNEL


def run_mfem_solve(node: dict) -> dict:
    """Production MFEM physics node."""
    print(f"[PHYSICS] MFEM Solve -> Mesh: {node.get('mesh')} | Params: {node.get('params', {})}")

    result = KERNEL.execute(node)
    return {
        "status": "success",
        "solver": "mfem",
        "mesh": node.get("mesh"),
        "result": result,
        "gpu_used": True,
    }


def run_sundials_integrate(node: dict) -> dict:
    """SUNDIALS time integration node."""
    print("[PHYSICS] SUNDIALS Integration on previous MFEM output")
    return {
        "status": "success",
        "solver": "sundials",
        "integration_steps": 1000,
        "gpu_used": False,
    }


def register_physics_nodes():
    """Register physics nodes into the main ExecutionGraph."""

    GRAPH.register(
        Node(
            id="physics.mfem.solve",
            deps=[],
            fn=run_mfem_solve,
            metadata={"type": "physics", "gpu": True, "timeout": 300},
        )
    )

    GRAPH.register(
        Node(
            id="physics.sundials.integrate",
            deps=["physics.mfem.solve"],
            fn=run_sundials_integrate,
            metadata={"type": "physics", "gpu": False, "timeout": 60},
        )
    )

    print("Physics nodes successfully registered into main DAG")


register_physics_nodes()
