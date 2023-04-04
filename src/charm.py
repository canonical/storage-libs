#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Placeholder charm for storage libs."""

import logging

from ops.charm import CharmBase, StartEvent
from ops.main import main
from ops.model import BlockedStatus

logger = logging.getLogger(__name__)


class StorageLibsCharm(CharmBase):
    """Placeholder charm for storage libs."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.framework.observe(self.on.start, self._on_start)

    def _on_start(self, _: StartEvent) -> None:
        """Handle start event."""
        self.unit.status = BlockedStatus(
            "storage-libs is not meant to be deployed as a standalone charm"
        )


if __name__ == "__main__":  # pragma: nocover
    main(StorageLibsCharm)
