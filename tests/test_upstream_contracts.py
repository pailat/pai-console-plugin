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
            'connection_create', 'connection_revoke',
            'connection_enrollment_get', 'connection_enrollment_approve',
            'connection_terminal_list', 'connection_terminal_terminate'})
        reads = {'connection_list', 'connection_get', 'connection_events',
                 'connection_enrollment_get', 'connection_terminal_list'}
        for name, tool in connections.items():
            self.assertEqual(tool['annotations']['readOnlyHint'], name in reads)
            self.assertFalse(tool['inputSchema']['additionalProperties'])
            # The registry belongs to one operator-configured organization.
            self.assertNotIn('organizationId', tool['inputSchema']['properties'])
        for name in ('connection_revoke', 'connection_terminal_terminate'):
            self.assertTrue(connections[name]['annotations']['destructiveHint'])
            self.assertTrue(connections[name]['annotations']['idempotentHint'])
        self.assertIn('expectedRevision', connections['connection_revoke']['inputSchema']['required'])
        self.assertTrue({'hostId', 'terminalId'} <= set(connections['connection_terminal_terminate']['inputSchema']['required']))
        self.assertTrue({'hostId', 'enrollmentId', 'expectedRevision'} <= set(connections['connection_enrollment_approve']['inputSchema']['required']))
        self.assertEqual(connections['connection_list']['inputSchema']['properties']['scope']['enum'], ['mine', 'all'])

    def test_retired_crm_aliases_are_not_taught_or_registered(self):
        retired = re.compile(r'\bcrm_(?:lead_)?task_(?:create|complete|get|list|tag_list|update)\b')
        paths = list((ROOT / 'skills').rglob('*.md')) + list((ROOT / 'agents').glob('*.md'))
        paths.append(ROOT / 'evals/mocks/pai/_tools.json')
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(retired.search(path.read_text()))


if __name__ == '__main__':
    unittest.main()
