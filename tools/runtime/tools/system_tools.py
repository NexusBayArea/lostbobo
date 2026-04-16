import subprocess
from tools.runtime.tool_registry import TOOL_REGISTRY, Tool


def run_ruff_check(_):
    return subprocess.run(["python", "-m", "ruff", "check", "."]).returncode


def run_ruff_format(_):
    return subprocess.run(["python", "-m", "ruff", "format", "."]).returncode


def run_pytest(_):
    return subprocess.run(["pytest", "-q"]).returncode


def register_system_tools():
    TOOL_REGISTRY.register(Tool("lint", run_ruff_check))
    TOOL_REGISTRY.register(Tool("format", run_ruff_format))
    TOOL_REGISTRY.register(Tool("test", run_pytest))
