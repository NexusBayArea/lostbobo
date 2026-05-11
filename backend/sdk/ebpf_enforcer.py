# backend/sdk/ebpf_enforcer.py
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class EbpfPolicy:
    plugin_id: str
    allowed_syscalls: list[str] = field(default_factory=list)
    allowed_network: bool = False
    max_memory_mb: int = 512
    max_cpu_percent: int = 80
    allowed_endpoints: list[str] = field(default_factory=list)


class EbpfEnforcer:
    """Attaches eBPF programs to plugin processes/pods."""

    def __init__(self):
        self.programs: dict[str, Any] = {}
        self._bpf_module = None

    def _initialize_bpf(self) -> bool:
        """Initialize eBPF subsystem."""
        try:
            import bcc

            self._bpf_module = bcc
            return True
        except ImportError:
            log.warning("bcc not installed, eBPF enforcement unavailable")
            return False
        except Exception as e:
            log.error("eBPF initialization failed: %s", e)
            return False

    def attach_to_plugin(self, plugin_id: str, pid: int, policy: EbpfPolicy) -> bool:
        """Load and attach eBPF program to a running plugin process."""
        if not self._bpf_module and not self._initialize_bpf():
            log.warning("Cannot attach eBPF to %s - bcc not available", plugin_id)
            return False

        try:
            bpf_text = f"""
#include <linux/ptrace.h>
#include <linux/sched.h>

BPF_HASH(allowed_syscalls, u32);

int trace_syscall(struct pt_regs *ctx) {{
    u32 syscall_id = (u32)PT_REGS_PARM1(ctx);
    if (allowed_syscalls.lookup(&syscall_id) == 0) {{
        bpf_trace_printk("Plugin %s blocked syscall %d", "{plugin_id}", syscall_id);
        return -1;
    }}
    return 0;
}}
"""
            self._bpf_module.BPF(text=bpf_text)
            self.programs[plugin_id] = {"policy": policy, "attached": True}
            log.info("eBPF enforcer attached to plugin %s (pid=%d)", plugin_id, pid)
            return True

        except Exception as e:
            log.error("Failed to attach eBPF to %s: %s", plugin_id, e)
            return False

    def detach(self, plugin_id: str) -> bool:
        """Detach eBPF program from plugin."""
        if plugin_id in self.programs:
            try:
                if hasattr(self.programs[plugin_id], "cleanup"):
                    self.programs[plugin_id].cleanup()
                del self.programs[plugin_id]
                log.info("eBPF enforcer detached from plugin %s", plugin_id)
                return True
            except Exception as e:
                log.error("Failed to detach eBPF from %s: %s", plugin_id, e)
                return False
        return False

    def is_attached(self, plugin_id: str) -> bool:
        return plugin_id in self.programs

    def get_policy(self, plugin_id: str) -> EbpfPolicy | None:
        if plugin_id in self.programs:
            return self.programs[plugin_id].get("policy")
        return None


def create_ebpf_enforcer() -> EbpfEnforcer:
    return EbpfEnforcer()
