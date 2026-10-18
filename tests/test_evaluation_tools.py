"""Check behavior shared by Claude/Codex trace grading and English reference rendering."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class TraceEvaluationTest(unittest.TestCase):
    def test_client_prefixes_and_order(self):
        runner = load('evaluate_traces')
        with tempfile.TemporaryDirectory() as temp:
            case = Path(temp)
            (case/'graders').mkdir()
            (case/'graders'/'order.md').write_text('---\ntype: tool_order\nbefore: mcp__plugin_pai-console_pai__knowledge_search\nafter: mcp__plugin_pai-console_pai__knowledge_create\n---\n')
            (case/'graders'/'review.md').write_text('---\ntype: llm\n---\nInspect sources and typed columns.\n')
            calls=[{'name':'mcp__pai-console-staging__knowledge_search'}, {'name':'mcp__pai-console-staging__knowledge_create'}]
            report=runner.evaluate(case,{'calls':calls})
            self.assertTrue(report['deterministic_passed'])
            self.assertTrue(report['review_required'])
            self.assertIsNone(report['results'][1]['passed'])
            self.assertFalse(runner.evaluate(case,{'calls':list(reversed(calls))})['deterministic_passed'])

    def test_json_match_and_forbidden_calls(self):
        runner=load('evaluate_traces')
        selector={'tool':'mcp__plugin_pai-console_pai__page_create','input_match':r'"typeSlug"\s*:\s*"'}
        self.assertTrue(runner.matches({'name':'mcp__pai__page_create','arguments':{'typeSlug':'report'}}, selector))
        self.assertFalse(runner.matches({'name':'mcp__pai__page_create','arguments':{'content':{}}}, selector))

class ReferenceTranslationTest(unittest.TestCase):
    def test_source_drift_requires_review_but_wire_examples_survive(self):
        renderer=load('localize_references')
        source='- La herramienta devuelve datos.'  # language: literal multilingual fixture
        key=hashlib.sha256(source.encode()).hexdigest()
        literal='```json\n{"description":"La herramienta devuelve datos."}\n```'
        result=renderer.localize(source+'\n'+literal,{key:'- The tool returns data.'})
        self.assertEqual(result,'- The tool returns data.\n'+literal+'\n')
        with self.assertRaises(ValueError):
            renderer.localize('- La herramienta devuelve otra cosa.',{key:'- The tool returns data.'})  # language: literal multilingual fixture

    def test_real_catalog_keys_are_consistent(self):
        renderer=load('localize_references')
        entries=renderer.catalog()
        self.assertGreater(len(entries),200)

class LanguageCheckTest(unittest.TestCase):
    def test_instructions_are_checked_but_literal_errors_are_not(self):
        checker=load('check_english')
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'SKILL.md'
            p.write_text('Antes de crear, busca.\nLiteral: `No escribas aquí`.\n```json\n{"text":"La herramienta"}\n```\n')  # language: literal multilingual fixture
            self.assertEqual([n for n,_ in checker.findings(p)],[1])

if __name__=='__main__':
    unittest.main()
