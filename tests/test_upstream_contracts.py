"""Prevent silent inventory truncation and obsolete operational tool references."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent


class UpstreamContractsTest(unittest.TestCase):
    def test_complete_fixture_fits_native_claude_mock_limit(self):
        fixture = ROOT / 'evals/mocks/pai/_tools.json'
        self.assertLessEqual(fixture.stat().st_size, 1048576,
                             'Compact the literal JSON; never drop schemas to fit.')
        tools = json.loads(fixture.read_text())['tools']
        names = [tool['name'] for tool in tools]
        self.assertEqual(len(names), len(set(names)))
        inventory = json.loads((ROOT / 'hooks/tools.json').read_text())['tools']
        self.assertEqual(set(names), set(inventory))
        for tool in tools:
            self.assertIsInstance(tool['annotations']['readOnlyHint'], bool)
            self.assertEqual(inventory[tool['name']]['readOnly'], tool['annotations']['readOnlyHint'])
            self.assertEqual(inventory[tool['name']]['destructive'], tool['annotations'].get('destructiveHint', False))
        self.assertTrue({'task_complete', 'chat_send', 'iam_policy_set', 'knowledge_merge',
                         'folder_reorder', 'crm_lead_anonymize'} <= set(names))
        self.assertTrue({'proposal_accept', 'proposal_reject'}.isdisjoint(names))

    def test_connection_registry_has_only_the_released_surface(self):
        tools = json.loads((ROOT / 'evals/mocks/pai/_tools.json').read_text())['tools']
        connections = {tool['name']: tool for tool in tools if tool['name'].startswith('connection_')}
        self.assertEqual(set(connections), {
            'connection_list', 'connection_get', 'connection_events',
            'connection_create', 'connection_revoke'})
        for name, tool in connections.items():
            self.assertEqual(tool['annotations']['readOnlyHint'], name in {
                'connection_list', 'connection_get', 'connection_events'})
            self.assertFalse(tool['inputSchema']['additionalProperties'])
            self.assertIn('organizationId', tool['inputSchema']['required'])
        revoke = connections['connection_revoke']
        self.assertTrue(revoke['annotations']['destructiveHint'])
        self.assertTrue(revoke['annotations']['idempotentHint'])
        self.assertIn('expectedRevision', revoke['inputSchema']['required'])

    def test_retired_crm_aliases_are_not_taught_or_registered(self):
        retired = re.compile(r'\bcrm_(?:lead_)?task_(?:create|complete|get|list|tag_list|update)\b')
        paths = list((ROOT / 'skills').rglob('*.md')) + list((ROOT / 'agents').glob('*.md'))
        paths.append(ROOT / 'evals/mocks/pai/_tools.json')
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(retired.search(path.read_text()))


if __name__ == '__main__':
    unittest.main()
