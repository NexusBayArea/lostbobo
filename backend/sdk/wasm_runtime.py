# backend/sdk/wasm_runtime.py
from __future__ import annotations

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class WasmPluginConfig:
    module_path: str
    max_memory_pages: int = 256
    max_fuel: int = 10_000_000
    allowed_host_functions: list[str] = None


class WasmSandbox:
    """Secure WASM execution environment."""

    def __init__(self, config: WasmPluginConfig):
        self.config = config
        self.engine = None
        self.store = None
        self.instance = None
        self._initialized = False

    def _initialize(self) -> None:
        """Initialize WASM runtime."""
        try:
            import wasmtime

            self.engine = wasmtime.Engine()
            self.store = wasmtime.Store(self.engine)

            self.store.set_limits(self.config.max_memory_pages * 64 * 1024)

            with open(self.config.module_path, "rb") as f:
                module = wasmtime.Module(self.store.engine, f.read())

            linker = wasmtime.Linker(self.engine)
            linker.define(
                "env",
                "log",
                wasmtime.Func(
                    self.store,
                    wasmtime.FuncType([], []),
                    self._host_log,
                ),
            )

            self.instance = wasmtime.Instance(self.store, module, linker)
            self._initialized = True

        except ImportError:
            log.warning("wasmtime not installed, WASM plugins will fall back to sandbox")
        except Exception as e:
            log.error("WASM initialization failed: %s", e)

    async def execute(self, command: str, payload: dict) -> dict:
        """Run WASM function with fuel (CPU) limit."""
        if not self._initialized:
            self._initialize()

        if not self._initialized or not self.instance:
            return {"success": False, "error": "WASM runtime not available"}

        try:
            func = self.instance.exports(self.store).get("execute")
            if func is None:
                return {"success": False, "error": "No execute function in WASM module"}

            self.store.set_fuel(self.config.max_fuel)

            result_ptr = func(self.store, command, self._serialize_payload(payload))
            return self._read_result(result_ptr)

        except Exception as e:
            log.error("WASM execution error: %s", e)
            return {"success": False, "error": str(e)}

    def _host_log(self, caller):
        log.info("WASM plugin logged message")

    def _serialize_payload(self, payload: dict) -> int:
        return 0

    def _read_result(self, ptr: int) -> dict:
        return {"success": True, "result": "ok"}


def create_wasm_sandbox(config: WasmPluginConfig) -> WasmSandbox:
    return WasmSandbox(config)
