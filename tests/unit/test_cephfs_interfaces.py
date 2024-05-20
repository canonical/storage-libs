#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Test the cephfs_interfaces charm library."""

import json
import unittest
from dataclasses import asdict
from unittest.mock import patch

from charms.storage_libs.v0.cephfs_interfaces import (
    CephFSAuthInfo,
    CephFSProvides,
    CephFSRequires,
    CephFSShareInfo,
    MountShareEvent,
    ServerConnectedEvent,
    ShareRequestedEvent,
    UmountShareEvent,
)
from ops.charm import CharmBase
from ops.testing import Harness

CEPHFS_INTEGRATION_NAME = "cephfs-share"
CEPHFS_INTEGRATION_INTERFACE = "cephfs_share"
CEPHFS_CLIENT_METADATA = f"""
name: cephfs-client
requires:
  {CEPHFS_INTEGRATION_NAME}:
    interface: {CEPHFS_INTEGRATION_INTERFACE}
"""
CEPHFS_SERVER_METADATA = f"""
name: cephfs-server
provides:
  {CEPHFS_INTEGRATION_NAME}:
    interface: {CEPHFS_INTEGRATION_INTERFACE}
"""

FSID = "123456789-0abc-defg-hijk-lmnopqrstuvw"
NAME = "filesystem"
PATH = "/data"
MONITOR_HOSTS = [
    "192.168.1.1:6789",
    "192.168.1.2:6789",
    "192.168.1.3:6789",
]
USERNAME = "user"
KEY = "R//appdqz4NP4Bxcc5XWrg=="
SHARE_INFO = json.dumps({"fsid": FSID, "name": NAME, "path": PATH, "monitor_hosts": MONITOR_HOSTS})


class CephFSClientCharm(CharmBase):
    """Mock CephFS client charm for unit tests."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.requirer = CephFSRequires(self, CEPHFS_INTEGRATION_NAME)
        self.framework.observe(self.requirer.on.server_connected, self._on_server_connected)
        self.framework.observe(self.requirer.on.mount_share, self._on_mount_share)
        self.framework.observe(self.requirer.on.umount_share, self._on_umount_share)

    def _on_server_connected(self, _: ServerConnectedEvent) -> None:
        pass

    def _on_mount_share(self, _: MountShareEvent) -> None:
        pass

    def _on_umount_share(self, _: UmountShareEvent) -> None:
        pass


class CephFSServerCharm(CharmBase):
    """Mock CephFS server charm for unit tests."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.provider = CephFSProvides(self, CEPHFS_INTEGRATION_NAME)
        self.framework.observe(self.provider.on.share_requested, self._on_share_requested)

    def _on_share_requested(self, _: ShareRequestedEvent) -> None:
        pass


class TestBaseInterface(unittest.TestCase):
    """Test the base interface for cephfs_interfaces."""

    def setUp(self) -> None:
        self.harness = Harness(CephFSClientCharm, meta=CEPHFS_CLIENT_METADATA)
        self.integration_id = self.harness.add_relation(CEPHFS_INTEGRATION_NAME, "application")
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
            {
                "share_info": SHARE_INFO,
                "auth": "scheme:/path",
            },
        )
        self.assertDictEqual(
            self.harness.charm.requirer.fetch_data(),
            {
                0: {
                    "share_info": SHARE_INFO,
                    "auth": "scheme:/path",
                }
            },
        )

    def tearDown(self) -> None:
        self.harness.cleanup()


class TestCephFSClientCharm(unittest.TestCase):
    """Test cephfs_interfaces from the requirer side."""

    def setUp(self) -> None:
        self.harness = Harness(CephFSClientCharm, meta=CEPHFS_CLIENT_METADATA)
        self.integration_id = self.harness.add_relation(CEPHFS_INTEGRATION_NAME, "application")
        self.harness.add_relation_unit(self.integration_id, "application/0")
        self.harness.set_leader(True)
        self.harness.begin_with_initial_hooks()

    @patch.object(CephFSClientCharm, "_on_server_connected")
    def test_on_server_connected(self, _on_server_connected) -> None:
        """Assert that correct hook is called when new server is connected."""
        # Add placeholder unit to trigger a `relation-joined` event.
        self.harness.add_relation_unit(self.integration_id, "application/1")
        _on_server_connected.assert_called_once()

    @patch.object(CephFSClientCharm, "_on_mount_share")
    def test_on_mount_share(self, _on_mount_share) -> None:
        """Assert that correct hook is called when CephFS share is ready to mount."""
        # Simulate creating the auth secret
        auth = self.harness.add_model_secret(
            "application", asdict(CephFSAuthInfo(username=USERNAME, key=KEY))
        )
        self.harness.grant_secret(auth, self.harness.charm.app)

        # Simulate server setting new CephFS share endpoint
        self.harness.update_relation_data(
            self.integration_id,
            "application",
            {
                "share_info": SHARE_INFO,
                "auth": auth,
            },
        )

        # Assert the correct event handler is invoked and event parameters are passed.
        _on_mount_share.assert_called_once()
        event = _on_mount_share.call_args[0][0]
        self.assertEqual(
            event.share_info,
            CephFSShareInfo(fsid=FSID, name=NAME, path=PATH, monitor_hosts=MONITOR_HOSTS),
        )
        self.assertEqual(event.auth_info, CephFSAuthInfo(username=USERNAME, key=KEY))

    @patch.object(CephFSClientCharm, "_on_mount_share")
    def test_on_mount_share_compat(self, _on_mount_share) -> None:
        """Assert that correct hook is called when CephFS share is ready to mount.

        Uses the compatibility auth info for reactive charms that don't support secrets.
        """
        # Simulate server setting new CephFS share endpoint
        self.harness.update_relation_data(
            self.integration_id,
            "application",
            {
                "share_info": SHARE_INFO,
                "auth": "plain:" + json.dumps(asdict(CephFSAuthInfo(username=USERNAME, key=KEY))),
            },
        )

        # Assert the correct event handler is invoked and event parameters are passed.
        _on_mount_share.assert_called_once()
        event = _on_mount_share.call_args[0][0]
        self.assertEqual(
            event.share_info,
            CephFSShareInfo(fsid=FSID, name=NAME, path=PATH, monitor_hosts=MONITOR_HOSTS),
        )
        self.assertEqual(event.auth_info, CephFSAuthInfo(username=USERNAME, key=KEY))

    @patch.object(CephFSClientCharm, "_on_umount_share")
    def test_on_umount_share(self, _on_umount_share) -> None:
        """Assert that correct hook is called when CephFS share is ready to be unmounted."""
        # Disconnect the related unit to trigger `relation-departed`.
        self.harness.remove_relation_unit(self.integration_id, "application/0")

        # Simulate the auth secret
        auth = self.harness.add_model_secret(
            "application", asdict(CephFSAuthInfo(username=USERNAME, key=KEY))
        )
        self.harness.grant_secret(auth, self.harness.charm.app)

        # Simulate CephFS share endpoint being present.
        self.harness.update_relation_data(
            self.integration_id,
            "application",
            {
                "share_info": SHARE_INFO,
                "auth": auth,
            },
        )

        # Assert the correct event handler is invoked and event parameters are passed.
        _on_umount_share.assert_called_once()
        event = _on_umount_share.call_args[0][0]
        self.assertEqual(
            event.share_info,
            CephFSShareInfo(fsid=FSID, name=NAME, path=PATH, monitor_hosts=MONITOR_HOSTS),
        )
        self.assertEqual(event.auth_info, CephFSAuthInfo(username=USERNAME, key=KEY))

    @patch.object(CephFSClientCharm, "_on_umount_share")
    def test_on_umount_share_compat(self, _on_umount_share) -> None:
        """Assert that correct hook is called when CephFS share is ready to be unmounted.

        Uses the compatibility auth info for reactive charms that don't support secrets.
        """
        # Disconnect the related unit to trigger `relation-departed`.
        self.harness.remove_relation_unit(self.integration_id, "application/0")

        # Simulate CephFS share endpoint being present.
        self.harness.update_relation_data(
            self.integration_id,
            "application",
            {
                "share_info": SHARE_INFO,
                "auth": "plain:" + json.dumps(asdict(CephFSAuthInfo(username=USERNAME, key=KEY))),
            },
        )

        # Assert the correct event handler is invoked and event parameters are passed.
        _on_umount_share.assert_called_once()
        event = _on_umount_share.call_args[0][0]
        self.assertEqual(
            event.share_info,
            CephFSShareInfo(fsid=FSID, name=NAME, path=PATH, monitor_hosts=MONITOR_HOSTS),
        )
        self.assertEqual(event.auth_info, CephFSAuthInfo(username=USERNAME, key=KEY))

    def test_request_share(self) -> None:
        """Assert that name is in integration databag."""
        # Evaluate if all values are set.
        self.harness.charm.requirer.request_share(self.integration_id, "/data")
        self.assertDictEqual(
            self.harness.get_relation_data(self.integration_id, "cephfs-client"),
            {"name": "/data"},
        )

    def tearDown(self) -> None:
        self.harness.cleanup()


class TestCephFSServerCharm(unittest.TestCase):
    """Test cephfs_interfaces from the provider side."""

    def setUp(self):
        self.harness = Harness(CephFSServerCharm, meta=CEPHFS_SERVER_METADATA)
        self.integration_id = self.harness.add_relation(CEPHFS_INTEGRATION_NAME, "application")
        self.harness.add_relation_unit(self.integration_id, "application/0")
        self.harness.set_leader(True)
        self.harness.begin_with_initial_hooks()

    @patch.object(CephFSServerCharm, "_on_share_requested")
    def test_on_share_requested(self, _on_share_requested) -> None:
        """Assert that correct hook is called when a new CephFS share is requested."""
        name = "/data"
        # Simulate the request of a new CephFS share.
        self.harness.update_relation_data(
            self.integration_id,
            "application",
            {
                "name": name,
            },
        )

        # Assert the correct event handler is invoked and event parameters are passed.
        _on_share_requested.assert_called_once()
        event = _on_share_requested.call_args[0][0]
        self.assertEqual(event.name, name)

    def test_set_endpoint(self) -> None:
        """Assert that endpoint is in integration databag."""
        share_info = CephFSShareInfo(fsid=FSID, name=NAME, path=PATH, monitor_hosts=MONITOR_HOSTS)
        auth_info = CephFSAuthInfo(username=USERNAME, key=KEY)
        self.harness.charm.provider.set_share(self.integration_id, share_info, auth_info)

        relation_data = self.harness.get_relation_data(self.integration_id, "cephfs-server")
        stored_share_info = json.loads(relation_data["share_info"])
        stored_auth_info = self.harness.charm.model.get_secret(
            id=relation_data["auth"]
        ).get_content()
        self.assertEqual(stored_share_info, asdict(share_info))
        self.assertEqual(stored_auth_info, asdict(auth_info))

    def test_set_share_twice(self) -> None:
        """Assert that the auth info can be set multiple times."""
        share_info = CephFSShareInfo(fsid=FSID, name=NAME, path=PATH, monitor_hosts=MONITOR_HOSTS)
        auth_info = CephFSAuthInfo(username=USERNAME, key=KEY)

        self.harness.charm.provider.set_share(self.integration_id, share_info, auth_info)

        relation_data = self.harness.get_relation_data(self.integration_id, "cephfs-server")
        old_auth_id = relation_data["auth"]
        new_auth_info = CephFSAuthInfo(username="new-user", key=KEY)

        self.harness.charm.provider.set_share(self.integration_id, share_info, new_auth_info)

        relation_data = self.harness.get_relation_data(self.integration_id, "cephfs-server")
        self.assertEqual(relation_data["auth"], old_auth_id)

        stored_share_info = json.loads(relation_data["share_info"])
        stored_auth_info = self.harness.charm.model.get_secret(
            id=relation_data["auth"]
        ).get_content(refresh=True)
        self.assertEqual(stored_share_info, asdict(share_info))
        self.assertEqual(stored_auth_info, asdict(new_auth_info))

    def tearDown(self) -> None:
        self.harness.cleanup()
