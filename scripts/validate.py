#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

langDir = Path("lang")
placeholderPattern = re.compile(r"%%|%(?:\d+\$)?s")


def loadJson(path):
    return json.loads(path.read_text(encoding="utf-8"))


def placeholdersIn(text):
    return sorted(placeholderPattern.findall(text))


english = loadJson(langDir / "en_us.json")
englishKeys = set(english)
commentHeaders = {key: text for key, text in english.items() if key.startswith("_comment_")}
translatableKeys = [key for key in english if not key.startswith("_comment_")]

foundProblem = False

for path in sorted(langDir.glob("*.json")):
    locale = path.stem
    if locale == "en_us":
        continue

    try:
        translation = loadJson(path)
    except json.JSONDecodeError as error:
        print(f"::error file={path}::{locale}: invalid JSON — {error}")
        foundProblem = True
        continue

    problems = []

    unknownKeys = [key for key in translation if key not in englishKeys]
    if unknownKeys:
        problems.append(f"unknown keys ({len(unknownKeys)}): {unknownKeys[:5]}")

    for key, expectedText in commentHeaders.items():
        if key in translation and translation[key] != expectedText:
            problems.append(f"comment header was changed: {key}")

    for key in translatableKeys:
        if key not in translation:
            continue
        if placeholdersIn(translation[key]) != placeholdersIn(english[key]):
            problems.append(
                f"placeholders don't match on {key}: "
                f"{placeholdersIn(translation[key])} vs {placeholdersIn(english[key])}"
            )

    if problems:
        foundProblem = True
        for problem in problems[:25]:
            print(f"::error file={path}::{locale}: {problem}")
        continue

    untranslated = sum(1 for key in translatableKeys if key not in translation)
    if untranslated > 0:
        print(f"{locale}: ok, {untranslated} still untranslated")
    else:
        print(f"{locale}: ok")

if foundProblem:
    sys.exit(1)
