#!/usr/bin/env python3
"""Check package layout and checksums against the published catalog seed."""
import hashlib
import json
import pathlib
import sys
import tarfile

folder = pathlib.Path(sys.argv[1])
entry = json.loads((folder / "catalog-entry.json").read_text())
manifest_raw = (folder / "plugin.yaml").read_bytes()
manifest = json.loads(manifest_raw)
plugin = entry["source"]["tag"].split("/v", 1)[0]
if entry["source"]["tag"] != f"{plugin}/v{manifest['version']}":
    raise SystemExit("tag/manifest version mismatch")
platforms = set()
schema_bytes = {}
for archive in entry["archives"]:
    file = folder / archive["url"].rsplit("/", 1)[1]
    if file.stat().st_size != archive["size"] or hashlib.sha256(file.read_bytes()).hexdigest() != archive["sha256"]:
        raise SystemExit("archive digest or byte size mismatch")
    with tarfile.open(file, "r:gz") as tar:
        names = tar.getnames()
        if any(pathlib.PurePosixPath(name).is_absolute() or ".." in pathlib.PurePosixPath(name).parts for name in names):
            raise SystemExit("archive escapes its root")
        if any(member.issym() or member.islnk() for member in tar.getmembers()):
            raise SystemExit("archive contains links")
        required = {f"{plugin}/bin/{plugin}", f"{plugin}/plugin.yaml", f"{plugin}/ui/index.js"}
        extension = manifest.get("nanite", {})
        for envelope in extension.get("registers", {}).get("envelopes", []):
            schema = pathlib.PurePosixPath(envelope["schema"])
            if schema.is_absolute() or ".." in schema.parts:
                raise SystemExit("envelope schema escapes bundle")
            required.add(f"{plugin}/{schema}")
            raw_schema = tar.extractfile(f"{plugin}/{schema}").read()
            json.loads(raw_schema)
            if schema_bytes.setdefault(str(schema), raw_schema) != raw_schema:
                raise SystemExit("envelope schema differs between platform archives")
        if not required.issubset(names):
            raise SystemExit("archive is missing installable plugin files")
        if tar.extractfile(f"{plugin}/plugin.yaml").read() != manifest_raw:
            raise SystemExit("archive manifest differs from published manifest")
    platforms.add(archive["platform"])
if platforms != {"darwin-arm64", "darwin-amd64", "linux-arm64", "linux-amd64"}:
    raise SystemExit("release does not cover all four platforms")
print("Verified four installable platform archives, manifest bytes, sizes and digests")
