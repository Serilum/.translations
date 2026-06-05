#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

langDir = Path("lang")


def toUtc(moment):
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def utcNow():
    return toUtc(datetime.now(timezone.utc))


def lastChanged(path):
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cI", "--", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    stamp = result.stdout.strip()
    return toUtc(datetime.fromisoformat(stamp)) if stamp else utcNow()


languages = {}
for path in sorted(langDir.glob("*.json")):
    languages[path.stem] = lastChanged(path)

manifest = {
    "generated": utcNow(),
    "languages": languages,
}

Path("manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
Path("manifest.min.json").write_text(
    json.dumps(manifest, ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8",
)

print(f"Wrote manifest for {len(languages)} languages")
