# Filesystem and Storage Libraries for Operator Framework Charms

## Description

The `storage-libs` charm provides a set of 
[charm libraries](https://juju.is/docs/sdk/libraries) which offers convenience
methods for interacting with charmed filesystems and storage devices, but also
writing your own filesystem/storage providing or consuming charms using
[integrations](https://juju.is/docs/olm/integration).

This charm is __not meant to be deployed__. It is used for hosting storage or
filesystem-related charm libraries only.

## Usage

This charm __is not intended to be deployed__. It serves as a namespace for standalone
charm libraries managed using 
[`charmcraft fetch-lib ...`](https://juju.is/docs/sdk/find-and-use-a-charm-library). After
fetching the charm library, it can be imported and used as a normal library inside a charm.
For example, you can fetch the `nfs_interfaces` using the following command:

`charmcraft fetch-lib charms.storage_libs.v0.nfs_interfaces`

The following libraries are available as part of this charm:

- `nfs_interfaces` - Library to manage integrations between NFS providers and consumers.

Documentation on how to use each individual charm library listed above can 
be found in the _Libraries_ tab.

## Contributing

Please see the Juju SDK docs for guidelines on enhancements to this charm 
following best practice guidelines, and `CONTRIBUTING.md` for developer guidance.

## License

The Storage Libs Operator and complementing charm libraries are free software,
distributed under the Apache Software License, version 2.0. See `LICENSE` 
for more information.
