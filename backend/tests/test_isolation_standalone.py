import asyncio
import unittest
from unittest.mock import MagicMock
from backend.core.hardware.isolation import GPUIsolationManager, GPUIsolationLevel


class TestGPUIsolation(unittest.IsolatedAsyncioTestCase):
    async def test_isolation_application(self):
        manager = GPUIsolationManager.manager()

        # Mock capacity and request objects
        mock_capacity = MagicMock()
        mock_capacity.pool_class.value = "shared"
        mock_capacity.supports_mig = False
        mock_capacity.vram_gb = 16.0

        mock_allocation = MagicMock()
        mock_allocation.allocation_id = "test-alloc-1"
        mock_allocation.gpu_fraction = 0.5
        mock_allocation.memory_fraction = 0.5

        mock_request = MagicMock()
        mock_request.tenant_id = "tenant-123"
        mock_request.sla_tier.value = "standard"

        success = await manager.apply_isolation(mock_capacity, mock_allocation, mock_request)
        self.assertTrue(success)

        config = manager.get_config("test-alloc-1")
        self.assertIsNotNone(config)
        self.assertEqual(config.level, GPUIsolationLevel.CONTAINER)
        self.assertEqual(config.tenant_id, "tenant-123")


if __name__ == "__main__":
    unittest.main()
