from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_target_sdk_36_requires_robolectric_416() -> None:
    """Play targetSdk 36 needs Robolectric 4.16 (maxSdk 36) + JDK 21 for unit tests."""
    gradle = _read("native-android/app/build.gradle.kts")
    versions = _read("native-android/gradle/libs.versions.toml")
    ci = _read(".github/workflows/ci.yml")

    target = re.search(r"targetSdk\s*=\s*(?:ciTargetSdk\s*\?:\s*)?(\d+)", gradle)
    assert target is not None
    target_sdk = int(target.group(1))
    assert target_sdk >= 36

    match = re.search(r'^robolectric\s*=\s*"([^"]+)"', versions, re.M)
    assert match is not None, "missing robolectric version pin"
    major_minor = tuple(int(p) for p in match.group(1).split(".")[:2])
    assert major_minor >= (4, 16), f"robolectric {match.group(1)} cannot run targetSdk 36 (need >=4.16)"

    assert "java-version: '21'" in ci
    flaky = _read(".github/workflows/flaky-test-audit.yml")
    canary = _read(".github/workflows/android17-canary.yml")
    assert "java-version: '21'" in flaky
    assert "java-version: '21'" in canary
    assert "--add-opens=java.base/java.lang=ALL-UNNAMED" in gradle
