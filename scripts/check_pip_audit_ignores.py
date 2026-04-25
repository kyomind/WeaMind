"""Check whether pip-audit vulnerability ignores can be removed."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

IGNORE_PATTERN = re.compile(r"--ignore-vuln=(GHSA-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+)")
SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "htmlcov",
    "security-reports",
}


@dataclass(frozen=True)
class IgnoreHit:
    """A pip-audit ignore found in a repository file."""

    advisory_id: str
    path: Path
    line_number: int


@dataclass(frozen=True)
class AdvisoryStatus:
    """The current GitHub Advisory state for an ignored GHSA."""

    advisory_id: str
    html_url: str
    summary: str
    withdrawn_at: str | None
    patched_versions: tuple[str, ...]

    @property
    def is_actionable(self) -> bool:
        """Return whether this ignored advisory may be removed or upgraded away."""
        return self.withdrawn_at is not None or bool(self.patched_versions)


def should_skip(path: Path) -> bool:
    """Return whether a path should be excluded from repository scanning."""
    return any(part in SKIP_DIRS for part in path.parts)


def find_ignore_hits(root: Path) -> list[IgnoreHit]:
    """Find all pip-audit GHSA ignores in text files under the repository root."""
    hits: list[IgnoreHit] = []
    for path in root.rglob("*"):
        if not path.is_file() or should_skip(path):
            continue

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(lines, start=1):
            hits.extend(
                IgnoreHit(
                    advisory_id=match.group(1),
                    path=path.relative_to(root),
                    line_number=line_number,
                )
                for match in IGNORE_PATTERN.finditer(line)
            )
    return hits


def fetch_advisory(advisory_id: str) -> dict[str, Any]:
    """Fetch one GitHub Advisory document from the public advisory API."""
    request = urllib.request.Request(
        f"https://api.github.com/advisories/{advisory_id}",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Failed to fetch {advisory_id}: HTTP {exc.code}: {message}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to fetch {advisory_id}: {exc.reason}") from exc


def parse_advisory(advisory_id: str, payload: dict[str, Any]) -> AdvisoryStatus:
    """Convert a GitHub Advisory API payload into the status this check needs."""
    patched_versions: set[str] = set()
    for vulnerability in payload.get("vulnerabilities", []):
        patched_version = vulnerability.get("first_patched_version")
        if patched_version:
            patched_versions.add(str(patched_version))

    return AdvisoryStatus(
        advisory_id=advisory_id,
        html_url=str(payload.get("html_url", "")),
        summary=str(payload.get("summary", "")),
        withdrawn_at=payload.get("withdrawn_at"),
        patched_versions=tuple(sorted(patched_versions)),
    )


def print_report(hits: list[IgnoreHit], statuses: dict[str, AdvisoryStatus]) -> int:
    """Print a human-readable report and return the intended process exit code."""
    if not hits:
        print("No pip-audit GHSA ignores found.")
        return 0

    print("Found pip-audit GHSA ignores:")
    for hit in hits:
        print(f"- {hit.advisory_id} at {hit.path}:{hit.line_number}")

    actionable = [status for status in statuses.values() if status.is_actionable]
    if not actionable:
        print("\nNo ignored advisories are currently actionable.")
        for status in statuses.values():
            print(f"- {status.advisory_id}: still ignored; no patched version and not withdrawn.")
        return 0

    print("\nAction required: at least one ignored advisory may be removable.")
    for status in actionable:
        print(f"- {status.advisory_id}: {status.summary}")
        if status.withdrawn_at:
            print(f"  withdrawn_at: {status.withdrawn_at}")
        if status.patched_versions:
            versions = ", ".join(status.patched_versions)
            print(f"  first_patched_version: {versions}")
        if status.html_url:
            print(f"  advisory: {status.html_url}")
    print("\nTry updating the affected dependency and remove the ignore if pip-audit passes.")
    return 1


def main() -> int:
    """Run the stale pip-audit ignore check."""
    root = Path.cwd()
    hits = find_ignore_hits(root)
    advisory_ids = sorted({hit.advisory_id for hit in hits})
    statuses = {
        advisory_id: parse_advisory(advisory_id, fetch_advisory(advisory_id))
        for advisory_id in advisory_ids
    }
    return print_report(hits, statuses)


if __name__ == "__main__":
    sys.exit(main())
