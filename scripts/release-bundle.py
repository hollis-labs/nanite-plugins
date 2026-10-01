#!/usr/bin/env python3
"""Build four platform archives and a manifest-derived catalog seed record."""
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

root = pathlib.Path(__file__).resolve().parent.parent


def run(plugin, version):
    plugins = next(line for line in (root / "Makefile").read_text().splitlines() if line.startswith("PLUGINS :=")).split(":=", 1)[1].split()
    if plugin not in plugins or not re.fullmatch(r"[a-z][a-z0-9-]*", plugin):
        raise ValueError("plugin must be in the root PLUGINS registry")
    if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version):
        raise ValueError("version must be X.Y.Z without a leading v")
    source = root / plugin
    output = root / "release" / f"{plugin}-{version}"
    if output.exists():
        raise ValueError(f"refusing to overwrite {output}")
    env = dict(os.environ, GOWORK="off", CGO_ENABLED="0")
    if os.environ.get("REQUIRE_RELEASED_CONTRACTS") == "1":
        for module in ("github.com/hollis-labs/plugin-sdk", "github.com/hollis-labs/nanite/pkg/pluginapi"):
            info = json.loads(subprocess.check_output(["go", "list", "-m", "-json", module], cwd=source, env=env))
            if info.get("Replace") or not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", info.get("Version", "")):
                raise ValueError(f"release requires a stable public contract version, not a replacement or commit pin: {module}")
    subprocess.run(["go", "test", "./..."], cwd=source, env=env, check=True)
    with tempfile.TemporaryDirectory() as temporary:
        temporary = pathlib.Path(temporary)
        native = temporary / "native"
        subprocess.run(["go", "build", "-trimpath", "-o", str(native), "."], cwd=source, env=env, check=True)
        manifest_raw = subprocess.check_output([str(native), "--manifest"])
        manifest = json.loads(manifest_raw)
        if manifest["version"] != version:
            raise ValueError(f"binary version {manifest['version']} does not match tag version {version}")
        built = temporary / "release"
        built.mkdir()
        (built / "plugin.yaml").write_bytes(manifest_raw)
        tag = f"{plugin}/v{version}"
        release_url = f"https://github.com/hollis-labs/nanite-plugins/releases/download/{tag}"
        archives = []
        for goos in ("darwin", "linux"):
            for goarch in ("arm64", "amd64"):
                stage = temporary / f"{goos}-{goarch}" / plugin
                (stage / "bin").mkdir(parents=True)
                subprocess.run(["go", "build", "-trimpath", "-ldflags=-s -w", "-o", str(stage / "bin" / plugin), "."], cwd=source, env=dict(env, GOOS=goos, GOARCH=goarch), check=True)
                (stage / "plugin.yaml").write_bytes(manifest_raw)
                ui = source / "ui"
                if ui.exists():
                    if any(path.is_symlink() for path in ui.rglob("*")):
                        raise ValueError("UI release assets cannot be symlinks")
                    shutil.copytree(ui, stage / "ui")
                name = f"{plugin}-{version}-{goos}-{goarch}.tar.gz"
                archive = built / name
                with tarfile.open(archive, "w:gz") as tar:
                    tar.add(stage, arcname=plugin)
                digest = hashlib.sha256(archive.read_bytes()).hexdigest()
                archives.append({"platform": f"{goos}-{goarch}", "url": f"{release_url}/{name}", "sha256": digest, "size": archive.stat().st_size})
        (built / "SHA256SUMS").write_text("".join(f"{entry['sha256']}  {entry['url'].rsplit('/', 1)[1]}\n" for entry in archives))
        entry = {
            "manifest": f"manifests/{plugin}-{version}.json",
            "manifest_url": f"{release_url}/plugin.yaml",
            "source": {"type": "git", "repo": "https://github.com/hollis-labs/nanite-plugins", "tag": tag},
            "archives": archives,
            "directory": {"status": "experimental", "short_desc": manifest.get("description", ""), "readme_url": f"https://github.com/hollis-labs/nanite-plugins/tree/{tag}/{plugin}"},
        }
        (built / "catalog-entry.json").write_text(json.dumps(entry, indent=2) + "\n")
        output.parent.mkdir(exist_ok=True)
        shutil.copytree(built, output)
    print(f"Built {output}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: release-bundle.py PLUGIN VERSION")
    run(*sys.argv[1:])
