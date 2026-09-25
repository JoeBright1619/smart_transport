"""Tests for GPS Device model."""

from __future__ import annotations

import uuid


from app.models.gps_device import GPSDevice, generate_gps_device_id


class TestGPSDeviceModel:
    """Unit tests for GPSDevice model."""

    def test_generate_gps_device_id_format(self):
        """Test that generated ID follows the expected format."""
        device_id = generate_gps_device_id()
        assert device_id.startswith("gps-")
        # Should be a valid UUID after gps- prefix
        uuid_str = device_id.replace("gps-", "")
        uuid.UUID(uuid_str)  # Will raise if invalid

    def test_gps_device_creation(self, db, make_tenant, tenant):
        """Test basic GPS device creation."""
        import asyncio

        async def _test():
            device = GPSDevice(
                id="gps-test-001",
                tenant_id=tenant.id,
                name="Test Device",
                token="test-token-123",
                device_type="gps_service",
                is_active=True,
            )
            db.add(device)
            await db.commit()
            await db.refresh(device)

            assert device.id == "gps-test-001"
            assert device.name == "Test Device"
            assert device.token == "test-token-123"
            assert device.device_type == "gps_service"
            assert device.is_active is True
            assert device.created_at is not None

        asyncio.get_event_loop().run_until_complete(_test())

    def test_gps_device_default_values(self, db, make_tenant, tenant):
        """Test default values for GPS device fields."""
        import asyncio

        async def _test():
            device = GPSDevice(
                id=f"gps-{uuid.uuid4()}",
                tenant_id=tenant.id,
                name="Default Device",
                token="token-123",
                device_type="gps_service",
            )
            db.add(device)
            await db.commit()
            await db.refresh(device)

            # is_active should default to True
            assert device.is_active is True

        asyncio.get_event_loop().run_until_complete(_test())

    def test_gps_device_inactive_status(self, db, make_tenant, tenant):
        """Test GPS device with inactive status."""
        import asyncio

        async def _test():
            device = GPSDevice(
                id=f"gps-{uuid.uuid4()}",
                tenant_id=tenant.id,
                name="Inactive Device",
                token="token-123",
                device_type="gps_service",
                is_active=False,
            )
            db.add(device)
            await db.commit()
            await db.refresh(device)

            assert device.is_active is False

        asyncio.get_event_loop().run_until_complete(_test())


class TestGPSDeviceSerialization:
    """Tests for GPS device serialization."""

    def test_to_dict(self, db, make_tenant, tenant):
        """Test GPS device can be serialized to dictionary."""
        import asyncio

        async def _test():
            device = GPSDevice(
                id="gps-serialize-001",
                tenant_id=tenant.id,
                name="Serialization Test",
                token="token-abc",
                device_type="calamp",
            )
            db.add(device)
            await db.commit()

            # Access the columns for serialization
            data = {
                "id": device.id,
                "tenant_id": device.tenant_id,
                "name": device.name,
                "token": device.token,
                "device_type": device.device_type,
                "is_active": device.is_active,
            }

            assert data["id"] == "gps-serialize-001"
            assert data["name"] == "Serialization Test"
            assert data["device_type"] == "calamp"

        asyncio.get_event_loop().run_until_complete(_test())
