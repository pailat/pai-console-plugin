"""The pai-harness plugin ships nothing project-specific: no real ids, panes, hosts, repos or emails, only fictional Acme."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_codex  # noqa: E402

SCANNED = (build_codex.HARNESS, build_codex.HARNESS_CODEX)
# The vendored upstream Herdr skill is third-party text, pinned and sha256-checked by build_codex.herdr_vendor.
VENDORED = ("skills/herdr/",)

LINEAR_ID = re.compile(r"\b([A-Z]{2,10})-\d+\b")
# Standards that look like issue ids; everything else except ACME is refused.
NOT_ISSUE_PREFIXES = frozenset(("ACME", "UTF", "SHA", "ISO", "RFC", "MD", "CVE", "TLS", "AES", "HTTP", "ECMA"))
PANE_ID = re.compile(r"\bw[0-9A-Z]{2,3}:p[0-9A-Z]{1,3}\b")
EMAIL = re.compile(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)")
HOSTNAME = re.compile(r"\b(?:[a-z0-9-]+\.)+(?:com|net|org|io|dev|lat|app|mx|ai|run|cloud|local|internal|xyz|co)\b", re.I)
NETWORK = re.compile(r"\b(?:10|100|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d+\.\d+(?:\.\d+)?\b|\.ts\.net\b")
PATHS = re.compile(r"/home/|/Users/|~/worktrees")
REPO_NAMES = re.compile(r"pai-portal|pai-agent-cli|pai-console-plugin|reui-orch|paitesting|railway\.app|pailat|herdrdev", re.I)
# What a manifest must carry because it identifies the package. Only plugin manifests may hold them.
MANIFEST_FILES = ("plugin.json",)
MANIFEST_ALLOWED = ("alex.sanchez@pai.lat", "https://pai.lat", "https://github.com/pailat/pai-console-plugin")
ALLOWED_HOSTS = ("example.com", "json-schema.org", "agent-plugins.org")


def findings(text: str, name: str = "") -> list[str]:
    """Return every real-looking identifier in the text."""
    if Path(name).name in MANIFEST_FILES:
        for allowed in MANIFEST_ALLOWED:
            text = text.replace(allowed, "")
    found = []
    for match in LINEAR_ID.finditer(text):
        if match.group(1) not in NOT_ISSUE_PREFIXES:
            found.append(f"issue id {match.group(0)}")
    found += [f"pane id {m.group(0)}" for m in PANE_ID.finditer(text)]
    found += [f"email {m.group(0)}" for m in EMAIL.finditer(text) if not (m.group(1) == "example.com" or m.group(1).endswith(".example.com"))]
    for match in HOSTNAME.finditer(text):
        host = match.group(0).lower()
        if not any(host == ok or host.endswith("." + ok) for ok in ALLOWED_HOSTS):
            found.append(f"hostname {match.group(0)}")
    found += [f"network address {m.group(0)}" for m in NETWORK.finditer(text)]
    found += [f"machine path {m.group(0)}" for m in PATHS.finditer(text)]
    found += [f"real name {m.group(0)}" for m in REPO_NAMES.finditer(text)]
    return found


def scanned_files() -> list[Path]:
    files = []
    for base in SCANNED:
        for path in sorted((ROOT / base).rglob("*")):
            relative = path.relative_to(ROOT / base).as_posix()
            if path.is_file() and "__pycache__" not in path.parts and not relative.startswith(VENDORED):
                files.append(path)
    return files


class DenylistTest(unittest.TestCase):
    def test_the_plugin_and_its_codex_package_contain_no_real_identifiers(self) -> None:
        files = scanned_files()
        self.assertGreater(len(files), 10)
        for path in files:
            self.assertEqual(findings(path.read_text(), path.name), [], path.relative_to(ROOT).as_posix())

    def test_detects_planted_real_identifiers(self) -> None:
        planted = {
            "issue id ATE-1173": "see ATE-1173",
            "issue id ABC-9": "see ABC-9",
            "pane id wM8:p1": "pane wM8:p1",
            "email alex@gmail.com": "mail alex@gmail.com",
            "email owner@pai.lat": "mail owner@pai.lat",
            "hostname build.paitesting.com": "curl https://build.paitesting.com/x",
            "network address 100.64.0.7": "ssh 100.64.0.7",
            "machine path /home/": "cd /home/alex",
            "real name pai-portal": "repo pai-portal",
        }
        for expected, text in planted.items():
            self.assertIn(expected, findings(text), text)

    def test_accepts_the_fictional_acme_vocabulary(self) -> None:
        text = "ACME-123 in acme-app on acme-desktop.example.com, mail owner@example.com, UTF-8 and SHA-256"
        self.assertEqual(findings(text), [])

    def test_manifest_identity_is_allowed_only_in_plugin_manifests(self) -> None:
        text = '"email": "alex.sanchez@pai.lat", "url": "https://pai.lat"'
        self.assertEqual(findings(text, "plugin.json"), [])
        self.assertNotEqual(findings(text, "SKILL.md"), [])

    def test_examples_use_only_the_fictional_names(self) -> None:
        text = (ROOT / build_codex.HARNESS / "examples/acme/.pai-harness.toml").read_text()
        self.assertIn("ACME-123", text)
        for name in ("acme-app", "acme-desktop", "example.com"):
            self.assertIn(name, text)


if __name__ == "__main__":
    unittest.main()
