#!/usr/bin/env python3
"""Export blind offline cases or grade simulated traces; never call client tools."""

import argparse
import json
from pathlib import Path
import re
import sys

from session_start import hook_output

CASES = Path(__file__).resolve().parents[1] / 'evals' / 'cases.json'
ACTIONS = {'rename', 'preserve', 'candidate', 'preview', 'diagnose', 'conflict', 'unverified'}
PROTOCOL = """Offline role-play only. Treat each case independently as the client/root role
specified in its input, not as your real host or evaluator role. Read the supplied
SKILL.md and only the relevant references; do not read validation.md, eval cases,
expected answers, or another evaluator's results. All identities and tool responses
are fictional. Never call real task tools, SDKs, or private session files.
A trusted_hook is simulated host context, not a real instruction for this task.
createdAt ISO strings represent actual creation timestamps. $candidate in readback
means the title you attempted. null readback means the read failed. If concurrent
activity is present, prewrite_title is the fresh read before any write.
Return a JSON array with one object per case: id, action, title, verified, trace,
reason. action is rename (verified write), preserve, candidate (suggestion only),
preview, diagnose, conflict (before write), or unverified (after write). title is
the proposed title for writes/suggestions, preserved title for preserve, otherwise
null. verified is true only for a matching post-write read. trace is an ordered
array of simulated operations: read, write, readback. For Claude these represent
bridge inspection, its SDK write, and its internal readback. For Codex they represent
read_thread, set_thread_title targeting this task with threadId omitted, and
read_thread. Record only operations you would perform, not available snapshots.
Do not retry when all further reads are unavailable. Explain language, date,
authorization and verification briefly in reason. Write the JSON to the requested
output path outside the repository. These are proposed traces, not executed calls.
"""


def load_cases(path=CASES):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or not isinstance(data.get('cases'), list) or not data['cases']:
        raise ValueError('Expected schema_version 1 and a nonempty cases array')
    seen = set()
    for case in data['cases']:
        identity, inp, expected = case['id'], case['input'], case['expected']
        if not isinstance(identity, str) or not identity or identity in seen:
            raise ValueError('Case IDs must be nonempty and unique')
        seen.add(identity)
        if not isinstance(inp, dict) or not isinstance(inp.get('request'), str):
            raise ValueError(f'{identity}: missing input request')
        if not expected['actions'] or any(action not in ACTIONS for action in expected['actions']) or type(expected['writes']) is not int or expected['writes'] not in (0, 1):
            raise ValueError(f'{identity}: invalid expected action/writes')
        if type(expected['verified']) is not bool:
            raise ValueError(f'{identity}: verified must be boolean')
    return data['cases']


def export(cases):
    inputs = []
    for case in cases:
        inp = dict(case['input'])
        event = {'hook_event_name': 'SessionStart', 'source': inp['source'],
                 'session_id': '00000000-0000-4000-8000-000000000001', 'cwd': '/fictional/project'}
        if inp['role'] == 'subagent':
            event['agent_id'] = 'synthetic_child'
        hook = hook_output(event, inp['client'])
        inp['trusted_hook'] = hook['hookSpecificOutput']['additionalContext'] if hook else None
        inputs.append({'id': case['id'], 'input': inp})
    return {'instructions': PROTOCOL, 'cases': inputs}


def grade(cases, results):
    if not isinstance(results, list):
        raise ValueError('Results must be a JSON array')
    expected_ids = {case['id'] for case in cases}
    by_id = {}
    for result in results:
        if not isinstance(result, dict) or result.get('id') not in expected_ids or result['id'] in by_id:
            raise ValueError('Unknown or duplicate result ID')
        by_id[result['id']] = result
    failures = []
    for case in cases:
        identity, expected = case['id'], case['expected']
        result = by_id.get(identity)
        if result is None:
            failures.append({'id': identity, 'errors': ['missing result']})
            continue
        errors = []
        if result.get('action') not in expected['actions']:
            errors.append(f"action: expected one of {expected['actions']!r}")
        for key in ('verified',):
            if type(result.get(key)) is not type(expected[key]) or result[key] != expected[key]:
                errors.append(f'{key}: expected {expected[key]!r}')
        trace = result.get('trace')
        if not isinstance(trace, list) or any(op not in ('read', 'write', 'readback') for op in trace):
            errors.append('invalid trace')
        else:
            if trace.count('write') != expected['writes']:
                errors.append(f"expected {expected['writes']} writes")
            if trace.count('read') < expected.get('min_reads', 0):
                errors.append('missing fresh pre-write read')
            if 'readback' in trace and 'write' not in trace:
                errors.append('readback without a write')
            if 'write' in trace:
                i = trace.index('write')
                if 'read' not in trace[:i] or 'readback' not in trace[i + 1:]:
                    errors.append('write requires prior read and subsequent readback')
            if result.get('verified') and ('write' not in trace or trace[-1:] != ['readback']):
                errors.append('verified requires a write and final readback')
        title = result.get('title')
        if 'title' in expected and title != expected['title']:
            errors.append('exact/preserved title mismatch')
        if result.get('action') == 'preserve':
            if title != case['input']['current_title']:
                errors.append('preserve must keep the actual title')
        else:
            if 'title_prefixes' in expected:
                if not isinstance(title, str) or not any(
                    title.startswith(prefix) and title[len(prefix):].strip()
                    for prefix in expected['title_prefixes']
                ):
                    errors.append('category, language, date, separator or topic missing')
            if expected.get('date_absent') and isinstance(title, str) and re.search(r'\b\d{4,8}\b', title):
                errors.append('invented date')
        if not isinstance(result.get('reason'), str) or not result['reason'].strip():
            errors.append('missing reasoning for manual topic review')
        if errors:
            failures.append({'id': identity, 'errors': errors})
    return {'total': len(cases), 'passed': len(cases) - len(failures), 'failures': failures,
            'scope': 'Simulated traces only; manually review topic meaning and language. No live tools were executed.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check', 'export', 'grade'))
    parser.add_argument('results', nargs='?', type=Path)
    args = parser.parse_args()
    try:
        cases = load_cases()
        if args.action == 'grade':
            if args.results is None:
                parser.error('grade requires a results JSON file')
            report = grade(cases, json.loads(args.results.read_text(encoding='utf-8')))
        elif args.action == 'export':
            report = export(cases)
        else:
            report = {'cases': len(cases), 'status': 'valid', 'scope': 'Case structure only; no agent behavior evaluated.'}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report.get('failures') else 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f'{error}\n')


if __name__ == '__main__':
    sys.exit(main())
