from typing import Any

import structlog
import sympy as sp

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


class SymbolicPhysicsEngine:
    """Symbolic derivation and invariant extraction — reasoning only."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

    async def derive(self, equations: dict[str, str]) -> dict[str, Any]:
        """Derive symbolic invariants and constraints from equations."""
        job_id = await self.supabase.create_job("symbolic_derivation", {"equations": equations})

        symbols = {}
        all_symbols = set().union(*[eq.split() for eq in equations.values()])
        for name in all_symbols:
            if name.isidentifier() and name not in ["sin", "cos", "exp", "log"]:
                symbols[name] = sp.symbols(name)

        derived = {}
        invariants = []

        for name, eq_str in equations.items():
            try:
                expr = sp.sympify(eq_str, locals=symbols)
                simplified = sp.simplify(expr)
                derived[name] = str(simplified)

                # Extract conservation-style invariants
                if "d/dt" in eq_str or "div" in eq_str.lower():
                    invariants.append({"type": "conservation", "equation": name, "simplified": str(simplified)})
            except Exception as e:
                log.warning("symbolic derivation failed", equation=name, error=str(e))

        await self.supabase.record_event(
            "symbolic_derivation_completed",
            {"job_id": job_id, "equations_count": len(equations), "invariants_found": len(invariants)},
        )

        return {
            "derived_equations": derived,
            "invariants": invariants,
            "symbol_map": {k: str(v) for k, v in symbols.items()},
        }
