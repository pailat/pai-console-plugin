#!/usr/bin/env python3
"""Evaluate shared tool-use graders against normalized Claude or Codex call traces.

Input JSON: {"calls":[{"name":"knowledge_search","arguments":{},"isError":false}],
             "final_response":"..."}.
Use --client claude|codex only for report metadata. LLM graders are emitted for
independent review, never silently marked passed. Requires PyYAML.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def tool_name(name: str) -> str:
    return name.rsplit('__', 1)[-1]


def matches(call: dict, selector) -> bool:
    if isinstance(selector, str):
        selector = {'tool': selector}
    if tool_name(call.get('name', '')) != tool_name(selector['tool']):
        return False
    expression = selector.get('input_match')
    if not expression:
        return True
    # Graders were authored against JSON input, not a provider's serialization.
    args = json.dumps(call.get('arguments', {}), ensure_ascii=False, separators=(',', ':'))
    return re.search(expression, args) is not None


def evaluate(case: Path, trace: dict) -> dict:
    import yaml
    calls = trace['calls']
    results = []
    for path in sorted((case / 'graders').glob('*.md')):
        _, front, body = path.read_text().split('---', 2)
        grader = yaml.safe_load(front)
        kind = grader['type']
        result = {'grader': path.name, 'type': kind}
        if kind == 'tool_used':
            count = sum(matches(c, grader) for c in calls)
            result.update(count=count, passed=grader.get('min', 0) <= count <= grader.get('max', float('inf')))
        elif kind == 'tool_order':
            before = [i for i,c in enumerate(calls) if matches(c, grader['before'])]
            after = [i for i,c in enumerate(calls) if matches(c, grader['after'])]
            result['passed'] = bool(before and after and min(before) < min(after))
        elif kind == 'llm':
            result.update(passed=None, review_required=True, instructions=body.strip(), focus=grader.get('focus', 'response'))
        else:
            raise ValueError(f'Unsupported grader type {kind!r} in {path}')
        results.append(result)
    return {'case': case.name, 'deterministic_passed': all(r['passed'] for r in results if r['passed'] is not None),
            'review_required': any(r.get('review_required') for r in results), 'results': results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', help='Existing eval case directory or name')
    parser.add_argument('trace', type=Path)
    parser.add_argument('--client', choices=('claude', 'codex'), required=True)
    args = parser.parse_args()
    case = Path(args.case)
    if not case.is_dir():
        case = ROOT / 'evals' / args.case
    trace = json.loads(args.trace.read_text())
    if not isinstance(trace.get('calls'), list):
        parser.error('trace.calls must be an array')
    report = evaluate(case, trace)
    report['client'] = args.client
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['deterministic_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
