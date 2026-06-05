#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

langDir = Path("lang")


def utcNow():
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return stamp.replace("+00:00", "Z")


def lastChanged(path):
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cI", "--", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip() or utcNow()


languages = {}
for path in sorted(langDir.glob("*.json")):
    locale = path.stem
    if locale == "en_us":
        continue
    languages[locale] = lastChanged(path)

manifest = {
    "generated": utcNow(),
    "languages": languages,
}

Path("manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(f"Wrote manifest for {len(languages)} languages")
