# nanite-plugins

First-party subprocess plugins for [Nanite](https://github.com/hollis-labs/nanite).

> **Pre-release.** Built in the open. Interfaces and behavior may change between
> minor versions; read release notes before upgrading.

Each plugin is its own Go module and program. Plugins depend on the public
`nanite/pkg/pluginapi` host contract and `plugin-sdk`, never on host internals.
The `example` plugin demonstrates a declared read-only tool and a React panel;
it holds no user data and performs no host mutations.

The [bookmarks](bookmarks/) plugin owns durable message bookmarks, with a
session panel, slash command, agent tools, and verified core-data imports.

The [Giphy](giphy/) plugin provides GIF search; [oEmbed](oembed/) provides
provider link previews. Their envelope schemas ship with the UI assets.

The headless [Loom integration](loom/) translates fragment callbacks into
scoped curator wakes and contributes reminder defaults for Loom agents.

The [Reminders](reminders/) plugin contributes a working-drawer tab, agent tools
and pending reminder context with explicit acknowledgment and durable imports.

The [Pins](pins/) plugin owns durable session/project context with a working
drawer tab, agent tools and verified imports.

The [Plan](plan/) plugin owns scoped todos and multi-step plans with the nine
work-tracking tools, a right-rail panel and atomic paired data imports.

## Build

```sh
make all
```

The root `PLUGINS` registry drives tests, builds and the CI matrix. `make dist`
writes `dist/<plugin>/` with a binary in `bin/`, generated `plugin.yaml` and an
ES module UI bundle. React is external and supplied by Nanite's import map.
Host installation requires a release that supports the shared manifest and
public host contract; declarations alone do not install or grant permissions.

## Release

Update a plugin's version constant and changelog, then run:

```sh
make release-bundle PLUGIN=example VERSION=0.1.0
python3 scripts/verify-release.py release/example-0.1.0
```

The output contains darwin/linux × arm64/amd64 tarballs, `SHA256SUMS`, the exact
generated manifest and a catalog seed record. The release script refuses tag
version mismatches and existing output directories. The publication workflow
also requires stable public-contract versions; commit pins are for local review
builds only. Per-plugin tags are
`<plugin>/vX.Y.Z`. A tag triggers archive publication and opens a catalog pull
request with the released manifest and checksums. The catalog workflow uses a
repository-scoped `CATALOG_TOKEN` with access to the catalog repository;
`PLUGINS_CATALOG_REPO` selects that repository. A missing token fails the
catalog job rather than silently skipping publication. Feed deployment follows
the catalog repository's publication process.

Build and release an extracted feature, adopt the release in the host, migrate
existing user data into the plugin's host-supplied DataDir, then remove the core
copy. Persistent data and cache directories stay outside plugin bundles and
survive upgrades. Do not treat an executable release as authority to delete data.
