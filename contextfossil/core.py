from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

VERSION = "0.1.0"
INSTRUCTION_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".cursorrules",
    "copilot-instructions.md",
}
TOOL_NAMES = ("git", "python", "python3", "node", "npm", "gh", "codex", "claude", "gemini")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip()


def _instruction_metadata(root: Path) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {".git", ".venv", "venv", "node_modules", "__pycache__"}]
        current_path = Path(current)
        for name in files:
            if name not in INSTRUCTION_FILES:
                continue
            path = current_path / name
            try:
                relative = path.relative_to(root).as_posix()
                found[relative] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}
            except OSError:
                continue
    return dict(sorted(found.items()))


def snapshot(root: Path) -> dict[str, Any]:
    root = root.resolve()
    env_names = sorted(k for k in os.environ if k)
    tools: dict[str, dict[str, str | bool]] = {}
    for name in TOOL_NAMES:
        executable = shutil.which(name)
        if not executable:
            tools[name] = {"present": False}
            continue
        version = _tool_version(name)
        tools[name] = {"present": True, "path": executable, "version": version}

    head = _git(root, "rev-parse", "HEAD")
    status = _git(root, "status", "--porcelain=v1")
    return {
        "schema": 1,
        "contextfossil": VERSION,
        "workspace": str(root),
        "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "python": platform.python_version(),
        "git": {
            "repository": _git(root, "rev-parse", "--show-toplevel"),
            "head": head,
            "dirty": bool(status),
        },
        "instruction_files": _instruction_metadata(root),
        "tools": tools,
        "environment_names": env_names,
    }


def _tool_version(name: str) -> str:
    try:
        result = subprocess.run([name, "--version"], capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    output = (result.stdout or result.stderr).strip().splitlines()
    return output[0][:160] if output else "unknown"


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("schema") != 1 or "contextfossil" not in data:
        raise ValueError("unsupported or invalid ContextFossil snapshot")
    return data


def diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []

    if before.get("git", {}).get("head") != after.get("git", {}).get("head"):
        changes.append({"kind": "git.head", "before": before.get("git", {}).get("head"), "after": after.get("git", {}).get("head")})
    if before.get("git", {}).get("dirty") != after.get("git", {}).get("dirty"):
        changes.append({"kind": "git.dirty", "before": before.get("git", {}).get("dirty"), "after": after.get("git", {}).get("dirty")})
    if before.get("platform") != after.get("platform"):
        changes.append({"kind": "platform", "before": before.get("platform"), "after": after.get("platform")})
    if before.get("python") != after.get("python"):
        changes.append({"kind": "python", "before": before.get("python"), "after": after.get("python")})

    for section in ("instruction_files", "tools"):
        old = before.get(section, {})
        new = after.get(section, {})
        for key in sorted(set(old) | set(new)):
            if old.get(key) != new.get(key):
                changes.append({"kind": f"{section}.{key}", "before": old.get(key), "after": new.get(key)})

    old_env = set(before.get("environment_names", []))
    new_env = set(after.get("environment_names", []))
    if old_env != new_env:
        changes.append({"kind": "environment.names", "added": sorted(new_env - old_env), "removed": sorted(old_env - new_env)})

    return {"changed": bool(changes), "count": len(changes), "changes": changes}


def dump(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
