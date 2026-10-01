#!/usr/bin/env python3
"""Stage a published plugin entry in a schema-v2 catalog checkout for review."""
import json
import pathlib
import re
import sys

catalog_root, assets = map(pathlib.Path, sys.argv[1:])
entry = json.loads((assets / "catalog-entry.json").read_text())
manifest_raw = (assets / "plugin.yaml").read_bytes()
manifest = json.loads(manifest_raw)
relative = pathlib.Path(entry["manifest"])
if not relative.parts or relative.parts[0] != "manifests" or relative.is_absolute() or ".." in relative.parts:
    raise SystemExit("catalog manifest path must stay inside manifests/")
seed_path = catalog_root / "plugins.json"
seed = json.loads(seed_path.read_text())
kept = []
for existing in seed["plugins"]:
    previous = json.loads((catalog_root / existing["manifest"]).read_text())
    if previous["id"] != manifest["id"]:
        kept.append(existing)
# This file is the exact declaration released beside the archives, not a
# regeneration with a different platform or a version stamped at runtime.
target = catalog_root / relative
target.parent.mkdir(exist_ok=True)
if target.is_symlink():
    raise SystemExit("catalog manifest target cannot be a symlink")
target.write_bytes(manifest_raw)
seed["plugins"] = kept + [entry]
version_match = re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", seed["catalog_version"])
if not version_match:
    raise SystemExit("catalog_version must be stable SemVer for automatic updates")
major, minor, patch = map(int, version_match.groups())
seed["catalog_version"] = f"{major}.{minor}.{patch + 1}"
seed_path.write_text(json.dumps(seed, indent=2) + "\n")
