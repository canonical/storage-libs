#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Test the nfs_interfaces charm library."""

import unittest
from unittest.mock import patch

from charms.storage_libs.v0.nfs_interfaces import (
    MountShareEvent,
    NFSProvides,
    NFSRequires,
    ServerConnectedEvent,
    ShareRequestedEvent,
    UmountShareEvent,
)
from ops.charm import CharmBase
from ops.testing import Harness

NFS_INTEGRATION_NAME = "nfs-share"
NFS_INTEGRATION_INTERFACE = "nfs_share"
NFS_CLIENT_METADATA = f"""
name: nfs-client
requires:
  {NFS_INTEGRATION_NAME}:
    interface: {NFS_INTEGRATION_INTERFACE}
"""
NFS_SERVER_METADATA = f"""
name: nfs-server
provides:
  {NFS_INTEGRATION_NAME}:
    interface: {NFS_INTEGRATION_INTERFACE}
"""


class NFSClientCharm(CharmBase):
    """Mock NFS client charm for unit tests."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.requirer = NFSRequires(self, NFS_INTEGRATION_NAME)
        self.framework.observe(self.requirer.on.server_connected, self._on_server_connected)
        self.framework.observe(self.requirer.on.mount_share, self._on_mount_share)
        self.framework.observe(self.requirer.on.umount_share, self._on_umount_share)

    def _on_server_connected(self, _: ServerConnectedEvent) -> None:
        pass

    def _on_mount_share(self, _: MountShareEvent) -> None:
        pass

    def _on_umount_share(self, _: UmountShareEvent) -> None:
        pass


class NFSServerCharm(CharmBase):
    """Mock NFS server charm for unit tests."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.provider = NFSProvides(self, NFS_INTEGRATION_NAME)
        self.framework.observe(self.provider.on.share_requested, self._on_share_requested)

    def _on_share_requested(self, _: ShareRequestedEvent) -> None:
        pass


class TestBaseInterface(unittest.TestCase):
    """Test the base interface for nfs_interfaces."""

    def setUp(self) -> None:
        self.harness = Harness(NFSClientCharm, meta=NFS_CLIENT_METADATA)
        self.integration_id = self.harness.add_relation(NFS_INTEGRATION_NAME, "application")
        self.harness.add_relation_unit(self.integration_id, "application/0")
        self.harness.set_leader(True)
        self.harness.begin_with_initial_hooks()

    def test_integrations(self) -> None:
        """Test `integrations` property."""
        self.assertNotEqual(self.harness.charm.requirer.integrations, [])

    def test_fetch_data(self) -> None:
        """Test _BaseInterface `fetch_data` method."""
        self.harness.update_relation_data(
            self.integration_id,
            "application",
            {"endpoint": "nfs://127.0.0.1/data"},
        )
        self.assertDictEqual(
            self.harness.charm.requirer.fetch_data(), {0: {"endpoint": "nfs://127.0.0.1/data"}}
        )

    def tearDown(self) -> None:
        self.harness.cleanup()


class TestNFSClientCharm(unittest.TestCase):
    """Test nfs_interfaces from the requirer side."""

    def setUp(self) -> None:
        self.harness = Harness(NFSClientCharm, meta=NFS_CLIENT_METADATA)
        self.integration_id = self.harness.add_relation(NFS_INTEGRATION_NAME, "application")
        self.harness.add_relation_unit(self.integration_id, "application/0")
        self.harness.set_leader(True)
        self.harness.begin_with_initial_hooks()

    @patch.object(NFSClientCharm, "_on_server_connected")
    def test_on_server_connected(self, _on_server_connected) -> None:
        """Assert that correct hook is called when new server is connected."""
        # Add placeholder unit to trigger a `relation-joined` event.
        self.harness.add_relation_unit(self.integration_id, "application/1")
        _on_server_connected.assert_called_once()

    @patch.object(NFSClientCharm, "_on_mount_share")
    def test_on_mount_share(self, _on_mount_share) -> None:
        """Assert that correct hook is called when NFS share is ready to mount."""
        # Simulate server setting new NFS share endpoint
        self.harness.update_relation_data(
            self.integration_id,
            "application",
            {"endpoint": (endpoint := "nfs://127.0.0.1/data")},
        )

        # Assert the correct event handler is invoked and event parameters are passed.
        _on_mount_share.assert_called_once()
        event = _on_mount_share.call_args[0][0]
        self.assertEqual(event.endpoint, endpoint)

    @patch.object(NFSClientCharm, "_on_umount_share")
    def test_on_umount_share(self, _on_umount_share) -> None:
        """Assert that correct hook is called when NFS share is ready to be unmounted."""
        # Disconnect the related unit to trigger `relation-departed`.
        self.harness.remove_relation_unit(self.integration_id, "application/0")
        # Simulate NFS share endpoint being present.
        self.harness.update_relation_data(
            self.integration_id,
            "application",
            {"endpoint": (endpoint := "nfs://127.0.0.1/data")},
        )

        # Assert the correct event handler is invoked and event parameters are passed.
        _on_umount_share.assert_called_once()
        event = _on_umount_share.call_args[0][0]
        self.assertEqual(event.endpoint, endpoint)

    def test_request_share(self) -> None:
        """Assert that name, allowlist, size is in integration databag."""
        # Evaluate if all values are set.
        self.harness.charm.requirer.request_share(
            self.integration_id, "/data", "192.168.0.15/24", 100
        )
        self.assertDictEqual(
            self.harness.get_relation_data(self.integration_id, "nfs-client"),
            {"name": "/data", "allowlist": "192.168.0.15/24", "size": "100"},
        )
        # Evaluate if multiple addresses in allowlist.
        self.harness.charm.requirer.request_share(
            self.integration_id, "/data", ["192.168.0.15/24", "10.152.28.100/24"]
        )
        self.assertDictEqual(
            self.harness.get_relation_data(self.integration_id, "nfs-client"),
            {"name": "/data", "allowlist": "192.168.0.15/24,10.152.28.100/24", "size": "-1"},
        )
        # Evaluate if only name is set.
        self.harness.charm.requirer.request_share(self.integration_id, "/data")
        self.assertDictEqual(
            self.harness.get_relation_data(self.integration_id, "nfs-client"),
            {"name": "/data", "allowlist": "0.0.0.0", "size": "-1"},
        )

    def tearDown(self) -> None:
        self.harness.cleanup()


class TestNFSServerCharm(unittest.TestCase):
    """Test nfs_interfaces from the provider side."""

    def setUp(self):
        self.harness = Harness(NFSServerCharm, meta=NFS_SERVER_METADATA)
        self.integration_id = self.harness.add_relation(NFS_INTEGRATION_NAME, "application")
        self.harness.add_relation_unit(self.integration_id, "application/0")
        self.harness.set_leader(True)
        self.harness.begin_with_initial_hooks()

    @patch.object(NFSServerCharm, "_on_share_requested")
    def test_on_share_requested(self, _on_share_requested) -> None:
        """Assert that correct hook is called when a new NFS share is requested."""
        # Simulate the request of a new NFS share.
        self.harness.update_relation_data(
            self.integration_id,
            "application",
            {
                "name": (name := "/data"),
                "allowlist": (allowlist := "192.168.0.15/24,10.152.28.100/24"),
                "size": (size := "100"),
            },
        )

        # Assert the correct event handler is invoked and event parameters are passed.
        _on_share_requested.assert_called_once()
        event = _on_share_requested.call_args[0][0]
        self.assertEqual(event.name, name)
        self.assertEqual(event.allowlist, allowlist)
        self.assertEqual(event.size, size)

    def test_set_endpoint(self) -> None:
        """Assert that endpoint is in integration databag."""
        self.harness.charm.provider.set_endpoint(self.integration_id, "nfs://127.0.0.1/data")
        self.assertDictEqual(
            self.harness.get_relation_data(self.integration_id, "nfs-server"),
            {"endpoint": "nfs://127.0.0.1/data"},
        )

    def tearDown(self) -> None:
        self.harness.cleanup()
