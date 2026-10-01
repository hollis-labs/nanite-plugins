# Nanite plugins

Every directory in the root Makefile's `PLUGINS` registry is a separate module.
The registry also generates the CI matrix. There is no root Go module.

Run `make all` from the root. CI pins golangci-lint v2.11.4 and tests each module
with `GOWORK=off` and `-race`. Plugins import only the public host contract
and plugin-sdk; publication requires stable release pins, while local review
builds may use commit pins. `scripts/check-dependencies.py` checks that boundary.

Generate plugin.yaml from the plugin binary with `--manifest`; never maintain a
second manifest by hand. Use the shared manifest and Nanite extension validators.
DataDir/CacheDir are host-supplied and outside the bundle. Never put durable
user state under dist/ or a release archive.

Release tags are `<plugin>/vX.Y.Z` and must match the version constant. The
release workflow publishes four platform archives and SHA256SUMS, then opens a
catalog update PR. Verify a local release with `scripts/verify-release.py`.
A feature extraction is ready only after release, host adoption and a tested
migration path; deleting the core copy is the last implementation step.
