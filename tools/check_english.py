#!/usr/bin/env python3
"""Flag recurring Spanish authoring patterns; literal contract data is exempt.

This deliberately small heuristic complements review; it is not a language detector.
Run on maintained prose, never translate identifiers to satisfy this check.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Source-owned MCP responses and schemas retain their actual wire text. Translation
# catalogs also retain source strings so that changes upstream fail explicitly.
EXEMPT = ('evals/mocks/pai/_tools.json', 'hooks/tools.json', 'evals/spanish-locale/prompt.md')
PATTERNS = re.compile(
    r'\b(?:el skill|los skills|la herramienta|las herramientas|'
    r'no inventes|no escribas|no cambies|no guardes|no publiques|'
    r'antes de crear|antes de guardar|responde solo|responde siempre|'
    r'la persona debe|la persona pide|se debe|siempre que|'
    r'cada escritura|fuera de alcance|no está permitido|'
    r'genera(?:do|da) por|no editar a mano)\b', re.IGNORECASE,
)


def maintained_files(root: Path):
    for p in sorted(root.rglob('*')):
        rel = p.relative_to(root)
        if any(part in {'.git', '__pycache__', 'node_modules', 'results', '.pytest_cache'} for part in rel.parts):
            continue
        if not p.is_file() or p.suffix not in {'.md', '.py', '.ts', '.js', '.json', '.yml', '.yaml', '.toml'}:
            continue
        if any(rel.as_posix() == item or rel.as_posix().endswith('/' + item) for item in EXEMPT) or p.name.startswith('reference-translations') or p.name == 'check_english.py':
            continue
        yield p


def findings(path: Path):
    fenced = False
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if line.lstrip().startswith('```'):
            fenced = not fenced
            continue
        if fenced or '# language: literal multilingual fixture' in line:
            continue
        # Backticks preserve literal errors, fixture data, identifiers and commands.
        prose = re.sub(r'`[^`]*`', '', line)
        if PATTERNS.search(prose):
            yield number, line.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', type=Path)
    args = parser.parse_args()
    paths = args.paths or list(maintained_files(ROOT))
    errors = [(p, n, line) for p in paths for n, line in findings(p)]
    for p, n, line in errors:
        print(f'{p}:{n}: author maintained prose in English: {line[:180]}')
    print(f'English authoring check: {len(errors)} finding(s) across {len(paths)} files.')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
