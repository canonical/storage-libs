<div align="center">

# Storage Libs

Storage libraries for integrating with charmed filesystems and storage devices.

[![CI](https://github.com/canonical/storage-libs/actions/workflows/ci.yaml/badge.svg)](https://github.com/canonical/storage-libs/actions/workflows/ci.yaml/badge.svg)
[![Release](https://github.com/canonical/storage-libs/actions/workflows/release-libs.yaml/badge.svg)](https://github.com/canonical/storage-libe/actions/workflows/release-libs.yaml/badge.svg)
[![Matrix](https://img.shields.io/matrix/ubuntu-hpc%3Amatrix.org?logo=matrix&label=ubuntu-hpc)](https://matrix.to/#/#ubuntu-hpc:matrix.org)

</div>

## Features

The Storage Libs operator provides a set of [charm libraries](https://juju.is/docs/sdk/libraries) 
which offer convenience methods for interacting with filesystems and storage devices via [Juju](https://juju.is) operators, 
but also writing your own filesystem/storage providing or requiring Juju operators. Storage Libs hosts the following charm libraries:

- `nfs_interfaces`: Library to manage integrations between NFS providers and consumers.

## Usage

This charm is __not meant to be deployed__. It is used for hosting storage or
filesystem-related charm libraries only. It serves as a namespace for standalone
charm libraries managed using 
[`charmcraft fetch-lib ...`](https://juju.is/docs/sdk/find-and-use-a-charm-library). After
fetching the charm library, it can be imported and used as a normal library inside a charm.
For example, you can fetch the `nfs_interfaces` using the following command:

```shell
$ charmcraft fetch-lib charms.storage_libs.v0.nfs_interfaces
```

Documentation on how to use each individual charm library listed above can 
be found in the [_Libraries_](https://charmhub.io/storage-libs/libraries) tab on Charmhub,
or the documentation can be found in each libraries' module-level docstring.

## Project & Community

The Storage Libs charm library collection is a project of the [Ubuntu HPC](https://discourse.ubuntu.com/t/high-performance-computing-team/35988) 
community. It is an open source project that is welcome to community involvement, contributions, suggestions, fixes, and 
constructive feedback. Interested in being involved with the development of the Storage Libs collection of charmed libraries? Check out these links below:

* [Join our online chat](https://matrix.to/#/#ubuntu-hpc:matrix.org)
* [Contributing guidelines](./CONTRIBUTING.md)
* [Code of conduct](https://ubuntu.com/community/ethos/code-of-conduct)
* [File a bug report](https://github.com/canonical/nfs-client-operator/issues)
* [Juju SDK docs](https://juju.is/docs/sdk)

## License

The Storage Libs charm libraries are free software,
distributed under the Apache Software License, version 2.0. 
See the [LICENSE](./LICENSE) file for more information.
