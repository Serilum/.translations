#!/usr/bin/env python3
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

mcmetaUrl = "https://raw.githubusercontent.com/misode/mcmeta/summary/versions/data.json"
langDir = Path("lang")
packDir = Path("pack")

description = "Translation files for Serilum's mods."
collectiveVersions = json.loads(Path("settings/collectiveVersions.json").read_text(encoding="utf-8"))
knownSet = set(collectiveVersions)
newestKnown = max(tuple(int(part) for part in version.split(".")) for version in collectiveVersions)
minorSchemeSince = (1, 21, 9)  # first version whose pack.mcmeta uses min_format/max_format arrays
fixedDate = (1980, 1, 1, 0, 0, 0)


def versionTuple(version):
    return tuple(int("".join(ch for ch in part if ch.isdigit()) or "0") for part in version.split("."))


def isWanted(entry):
    if entry.get("type") != "release":
        return False
    # the Collective release versions, plus anything newer (future releases)
    return entry["id"] in knownSet or versionTuple(entry["id"]) > newestKnown


def packMeta(entry):
    major = entry["resource_pack_version"]
    minor = entry.get("resource_pack_version_minor", 0)
    if versionTuple(entry["id"]) >= minorSchemeSince:
        return {"description": description, "min_format": [major, minor], "max_format": [major, minor]}
    return {"description": description, "pack_format": major}


def addEntry(archive, name, text):
    entry = zipfile.ZipInfo(name, date_time=fixedDate)
    entry.create_system = 3  # fixed (Unix) so Windows and CI builds are byte-identical
    entry.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(entry, text)


def loadLangEntries():
    return [(f"assets/collective/lang/{path.name}", path.read_text(encoding="utf-8")) for path in sorted(langDir.glob("*.json"))]


def buildPack(version, meta, langEntries):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        addEntry(archive, "pack.mcmeta", json.dumps({"pack": meta}, ensure_ascii=False, indent=2) + "\n")
        for name, text in langEntries:
            addEntry(archive, name, text)

    data = buffer.getvalue()
    versionDir = packDir / version
    versionDir.mkdir(parents=True, exist_ok=True)
    (versionDir / "pack.zip").write_bytes(data)
    (versionDir / "pack.sha1").write_text(hashlib.sha1(data).hexdigest(), encoding="utf-8")
    return len(data)


def fetchReleases():
    with urllib.request.urlopen(mcmetaUrl, timeout=30) as response:
        versions = json.loads(response.read().decode("utf-8"))
    return sorted((entry for entry in versions if isWanted(entry)), key=lambda entry: versionTuple(entry["id"]))


try:
    releases = fetchReleases()
except Exception as error:
    print(f"::warning::Could not reach mcmeta ({error}); leaving existing packs unchanged.")
    raise SystemExit(0)

missing = [version for version in collectiveVersions if version not in {entry["id"] for entry in releases}]
if missing:
    print(f"::warning::listed Collective versions not found in mcmeta: {missing}")

langEntries = loadLangEntries()
total = 0
for entry in releases:
    meta = packMeta(entry)
    total += buildPack(entry["id"], meta, langEntries)
    print(f"  {entry['id']:<10} format {meta.get('pack_format', meta.get('min_format'))}")

print(f"Built {len(releases)} packs ({total} bytes total)")
