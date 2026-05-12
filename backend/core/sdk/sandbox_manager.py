from __future__ import annotations

import asyncio
import uuid

from backend.core.sdk.abi.plugin_manifest import PluginManifest


class PluginSandbox:
    def __init__(self, sandbox_id: str, plugin_id: str):
        self.sandbox_id = sandbox_id
        self.plugin_id = plugin_id
        self.process: asyncio.subprocess.Process | None = None


class SandboxManager:
    def __init__(self):
        self._sandboxes: dict[str, PluginSandbox] = {}

    async def create(self, manifest: PluginManifest) -> PluginSandbox:
        sandbox_id = uuid.uuid4().hex[:12]
        sandbox = PluginSandbox(sandbox_id, manifest.name)
        self._sandboxes[sandbox_id] = sandbox

        if manifest.isolation.value == "container":
            await self._start_container(sandbox, manifest)
        elif manifest.isolation.value == "process":
            await self._start_process(sandbox, manifest)
        else:
            await self._start_process(sandbox, manifest)

        return sandbox

    async def _start_container(self, sandbox: PluginSandbox, manifest: PluginManifest):
        image = f"simhpc-plugin-{manifest.name}"
        cmd = [
            "docker",
            "run",
            "-d",
            "--rm",
            "--network",
            "none",
            "--name",
            f"simhpc-{sandbox.sandbox_id}",
            "--label",
            f"simhpc.plugin={manifest.name}",
            image,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()
        sandbox.process = proc

    async def _start_process(self, sandbox: PluginSandbox, manifest: PluginManifest):
        sandbox.process = None

    async def stop(self, sandbox_id: str):
        sandbox = self._sandboxes.pop(sandbox_id, None)
        if sandbox is None:
            return
        if sandbox.process is not None:
            sandbox.process.terminate()
            try:
                await asyncio.wait_for(sandbox.process.wait(), timeout=5)
            except TimeoutError:
                sandbox.process.kill()

    async def stop_all(self):
        for sid in list(self._sandboxes.keys()):
            await self.stop(sid)
