"""Controlled observer causals; no renderer, host, environment or provider needed."""
import ast
import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

SOURCE = Path(__file__).resolve().parents[2] / 'tests/test_ahp_terminal.py'
TREE = ast.parse(SOURCE.read_text())
FUNCTIONS = ast.Module(body=[node for node in TREE.body if isinstance(node, ast.AsyncFunctionDef)
                            and node.name in ('displayed', 'saved_draft_state')], type_ignores=[])
NAMESPACE = {'asyncio': asyncio, 'os': os, 'Path': Path}
exec(compile(FUNCTIONS, str(SOURCE), 'exec'), NAMESPACE)
observe = NAMESPACE['saved_draft_state']


class ObserverTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='tui-draft-observer-')
        self.path = Path(self.directory.name) / 'state.json'
        self.probe = SimpleNamespace(text='complete local draft', read=lambda _: None,
                                     process=SimpleNamespace(poll=lambda: None))
        self.old = os.environ.pop('TUI_EVIDENCE_DIR', None)

    def tearDown(self):
        if self.old is not None:
            os.environ['TUI_EVIDENCE_DIR'] = self.old
        self.directory.cleanup()

    async def test_delayed_save_fails_old_fixed_sleep_but_requires_live_exact_retention(self):
        self.path.write_text(json.dumps({'drafts': {}}))

        async def save():
            await asyncio.sleep(.35)
            self.path.write_text(json.dumps({'drafts': {'original': 'complete local draft'}}))

        writer = asyncio.create_task(save())
        await asyncio.sleep(.3)
        with self.assertRaises(KeyError):
            _ = json.loads(self.path.read_text())['drafts']['original']
        result = await observe(self.probe, self.path, 'original', 'complete local draft', timeout=1)
        await writer
        self.assertEqual(result['drafts']['original'], 'complete local draft')
        proof = json.loads((self.path.parent / 'draft-persistence-observer.txt').read_text())
        self.assertFalse(proof['initialExactDraftPresent'])
        self.assertTrue(proof['matchedWhileClientLive'])

    async def test_wrong_session_never_qualifies(self):
        self.path.write_text(json.dumps({'drafts': {'other': 'complete local draft'}}))
        with self.assertRaises(TimeoutError):
            await observe(self.probe, self.path, 'original', 'complete local draft', timeout=.03)

    async def test_partial_text_never_qualifies(self):
        self.path.write_text(json.dumps({'drafts': {'original': 'complete local'}}))
        with self.assertRaises(TimeoutError):
            await observe(self.probe, self.path, 'original', 'complete local draft', timeout=.03)

    async def test_malformed_state_is_not_an_empty_fallback(self):
        self.path.write_text('{bad')
        with self.assertRaises(json.JSONDecodeError):
            await observe(self.probe, self.path, 'original', 'complete local draft', timeout=.03)

    async def test_post_exit_retention_does_not_qualify(self):
        self.path.write_text(json.dumps({'drafts': {'original': 'complete local draft'}}))
        self.probe.process.poll = lambda: 0
        with self.assertRaises(AssertionError):
            await observe(self.probe, self.path, 'original', 'complete local draft', timeout=.03)


if __name__ == '__main__':
    unittest.main()
