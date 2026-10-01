#!/usr/bin/env python3
"""Reject host internal imports and dependencies outside the public contracts."""
import json
import pathlib
import os
import subprocess

root = pathlib.Path(__file__).resolve().parent.parent
line = next(line for line in (root / "Makefile").read_text().splitlines() if line.startswith("PLUGINS :="))
for plugin in line.split(":=", 1)[1].split():
    modules = subprocess.check_output(["go", "list", "-m", "-json", "all"], cwd=root / plugin, text=True, env=dict(os.environ, GOWORK="off"))
    decoder = json.JSONDecoder()
    while modules.strip():
        module, end = decoder.raw_decode(modules.lstrip())
        modules = modules.lstrip()[end:]
        if not module.get("Main") and module["Path"] not in (
            "github.com/hollis-labs/plugin-sdk", "github.com/hollis-labs/nanite/pkg/pluginapi"
        ):
            raise SystemExit(f"{plugin}: dependency outside public contracts: {module['Path']}")
    packages = subprocess.check_output(["go", "list", "-deps", "-f", "{{.ImportPath}}", "./..."], cwd=root / plugin, text=True, env=dict(os.environ, GOWORK="off"))
    for package in packages.splitlines():
        if package.startswith("github.com/hollis-labs/") and "/internal/" in package:
            raise SystemExit(f"{plugin}: forbidden host internal import: {package}")
