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


def translatableKeys(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return {key: value for key, value in data.items() if not key.startswith("_comment_")}


sourceKeys = set(translatableKeys(langDir / "en_us.json"))

languages = {}
translated = {}
for path in sorted(langDir.glob("*.json")):
    languages[path.stem] = lastChanged(path)
    entries = translatableKeys(path)
    translated[path.stem] = sum(1 for key, value in entries.items() if key in sourceKeys and value != "")

manifest = {
    "generated": utcNow(),
    "source": len(sourceKeys),
    "languages": languages,
    "translated": translated,
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
