"""Installed consumer against the independent public distribution and native ACP."""
import asyncio
import json
import os
import subprocess
from pathlib import Path

import pytest
import pytest_asyncio
from test_ahp_client import request, wait_for
from test_ahp_terminal import Probe, displayed

from amplifier_tui.client_state import ClientState
from amplifier_tui.unified_client import UnifiedBridge
from amplifier_tui.unified_transport import Transport

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not all(os.environ.get(name) for name in ('TUI_MESSAGE_DISTRIBUTION', 'TUI_MESSAGE_WS', 'TUI_MESSAGE_NATIVE')), reason='Exact installed public distribution/native inputs required')


@pytest_asyncio.fixture
async def message_host(tmp_path):
    native = os.environ['TUI_MESSAGE_NATIVE']
    subprocess.run([native, '-I', '-B', str(ROOT / 'tests/fixtures/native_messages.py'), str(tmp_path)], check=True)
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    config = {'account': 'tui-owned-message-account', 'stateDirectory': str(tmp_path / 'distribution'),
              'webDirectory': str(workspace), 'defaultWorkspace': str(workspace), 'allowedWorkspaceRoots': [str(tmp_path)],
              'engines': [{'id': 'amplifier', 'command': native,
                           'args': ['-I', '-B', '-m', 'amplifier_acp', '--config', str(tmp_path / 'native.json')],
                           'env': {'PYTHONDONTWRITEBYTECODE': '1', 'AMPLIFIER_RUNTIME_IMMUTABLE': '1', 'AMPLIFIER_SESSION_STATE_HOME': str(tmp_path / 'writers')}}],
              'nativeAdmin': {'engine': 'amplifier'}}
    (tmp_path / 'distribution-config.json').write_text(json.dumps(config))
    process = await asyncio.create_subprocess_exec('node', str(ROOT / 'tests/fixtures/message_distribution.mjs'), str(tmp_path), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        async with asyncio.timeout(45):
            line = await process.stdout.readline()
        assert line, (await process.stderr.read()).decode()
        yield json.loads(line)['url'], tmp_path, workspace
    finally:
        if process.returncode is None:
            process.terminate()
            async with asyncio.timeout(20):
                await process.wait()
        (tmp_path / 'distribution-stderr.txt').write_bytes(await process.stderr.read())
        frames = json.loads((tmp_path / 'protocol-frames.json').read_text()) if (tmp_path / 'protocol-frames.json').exists() else []
        reactions = [row['params'] for row in frames if row.get('params', {}).get('operation') == 'message.reaction']
        assert len({row['commandId'] for row in reactions}) == len(reactions), 'Reaction was replayed'
        assert all(set(row['args']) == {'reference', 'emoji', 'present'} for row in reactions)
        if (tmp_path / 'expected-turns.json').exists():
            turns = [row for row in frames if row.get('params', {}).get('action', {}).get('type') == 'chat/turnStarted']
            assert len(turns) == json.loads((tmp_path / 'expected-turns.json').read_text())
        evidence = Path(os.environ.get('TUI_EVIDENCE_DIR', tmp_path))
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / (tmp_path.name + '-protocol-frames.json')).write_text(json.dumps(frames, indent=2))


async def open_bridge(url, root, workspace, identity, session=None):
    store = ClientState(root / identity, url, identity)
    transport = Transport(url, '', identity)
    events = []
    bridge = UnifiedBridge(events.append, transport, store, workspace=str(workspace), session=session)
    await bridge.open()
    return bridge, events


async def seeded(bridge):
    assert (await bridge.dispatch(request(bridge, 'submit', text='original fixture source')))[0]
    async with asyncio.timeout(90):
        while not any(row.get('messageReference') and row['role'] == 'assistant' for row in bridge.session.get('messages', [])):
            await asyncio.sleep(.02)
    await wait_for(lambda: not bridge.messages.refreshing)
    return next(row for row in bridge.session['messages'] if row.get('messageReference') and row['role'] == 'assistant')


async def test_installed_public_bridge_private_quote_actual_freeze_and_exact_unknown_receipt(message_host):
    url, root, workspace = message_host
    bridge, events = await open_bridge(url, root, workspace, 'one')
    other = isolated = None
    try:
        message = await seeded(bridge)
        session = bridge.selected
        assert not bridge.messages.refreshing
        await bridge.dispatch(request(bridge, 'draft', text='Private quoted reply text'))
        assert (await bridge.dispatch(request(bridge, 'message.reply', message_id=message['id'])))[0]
        quote = bridge.messages.quote()
        other, _ = await open_bridge(url, root, workspace, 'two', session)
        assert other.messages.quote() is None
        isolated, _ = await open_bridge(url, root, workspace, 'isolated')
        await seeded(isolated)
        assert isolated.selected != session
        await bridge.select(isolated.selected)
        assert bridge.messages.quote() is None
        assert bridge.store.data['drafts'][session] == 'Private quoted reply text'
        await bridge.select(session)
        assert bridge.messages.quote() == quote
        await bridge.close()
        bridge, events = await open_bridge(url, root, workspace, 'one', session)
        assert bridge.messages.quote() == quote
        assert bridge.store.data['drafts'][session] == 'Private quoted reply text'
        assert (await bridge.dispatch(request(bridge, 'submit', text='Explicit quoted fixture response')))[0]
        async with asyncio.timeout(90):
            while not any(row.get('replyTo') for row in bridge.session.get('messages', [])):
                await asyncio.sleep(.02)
        frozen = next(row['replyTo'] for row in bridge.session['messages'] if row.get('replyTo'))
        assert frozen['excerpt'] == message['text'] and frozen['sourceDigest'] == quote['reference']['sourceDigest']
        assert bridge.messages.quote() is None
        await bridge.dispatch(request(bridge, 'draft', text='Private reaction draft'))
        await wait_for(lambda: not bridge.messages.refreshing and not bridge.session.get('activeTurnId'))
        message = next(row for row in bridge.session['messages'] if (row.get('messageReference') or {}).get('messageId') == message['messageReference']['messageId'])
        await bridge.messages.read(message['id'])
        (root / 'drop-next-reaction').touch()
        changed = await bridge.dispatch(request(bridge, 'message.reaction', message_id=message['id'], emoji='👍', present=True))
        assert not changed[0] and 'not confirmed' in changed[1]
        command, effect = next(iter(bridge.store.data['messageEffects'].items()))
        assert effect['status'] == 'unknown'
        # A second authenticated view changes current state after the lost echo.
        other_message = next(row for row in other.session['messages'] if (row.get('messageReference') or {}).get('messageId') == message['messageReference']['messageId'])
        assert (await other.dispatch(request(other, 'message.reaction', message_id=other_message['id'], emoji='👍', present=False)))[0]
        assert (await other.dispatch(request(other, 'message.reaction', message_id=other_message['id'], emoji='✅', present=True)))[0]
        await bridge.close()
        bridge, events = await open_bridge(url, root, workspace, 'one', session)
        current = next(row for row in bridge.session['messages'] if (row.get('messageReference') or {}).get('messageId') == message['messageReference']['messageId'])
        await bridge.messages.read(current['id'])
        assert bridge.messages.rows[(session, message['messageReference']['messageId'])]['mine'] == ['✅']
        assert (await bridge.dispatch(request(bridge, 'message.receipt', id=command)))[0]
        assert bridge.messages.rows[(session, message['messageReference']['messageId'])]['mine'] == ['✅']
        assert bridge.store.data['drafts'][session] == 'Private reaction draft'
        evidence = Path(os.environ.get('TUI_EVIDENCE_DIR', root))
        evidence.mkdir(parents=True, exist_ok=True)
        (root / 'expected-turns.json').write_text('3')
        (evidence / 'installed-message-bridge.json').write_text(json.dumps({'session': session, 'reference': message['messageReference'], 'frozenQuote': frozen, 'originalReaction': command, 'providerCalls': len((root / 'provider-audit.jsonl').read_text().splitlines()), 'outcome': 'passed'}, indent=2))
    finally:
        await bridge.close()
        if other:
            await other.close()
        if isolated:
            await isolated.close()


async def test_actual_installed_terminal_quote_reload_reactions_missing_ref_and_cancel(message_host):
    url, root, workspace = message_host
    executable = os.environ.get('TUI_CONNECTED_EXECUTABLE')
    if not executable:
        pytest.skip('Exact installed native executable required')
    bridge, _ = await open_bridge(url, root, workspace, 'setup')
    message = await seeded(bridge)
    session = bridge.selected
    await bridge.close()
    state_root = root / 'terminal'
    store = ClientState(state_root, url, 'terminal')
    store.draft(session, 'Private terminal quote draft')
    store.close()
    args = [executable, '--server', url, '--workspace', str(workspace), '--state-dir', str(state_root), '--client', 'terminal', '--session', session]
    probes = []
    async def choose(probe, query):
        probe.send(b'\x1bOS')
        await displayed([probe], lambda: 'Actions' in probe.text)
        probe.send(query.encode() + b'\r')
    try:
        probe = Probe(args, 120, 40, guard_terminal_modes=True, env={'PYTHONPATH': ''})
        probes.append(probe)
        await displayed([probe], lambda: 'Private terminal quote draft' in probe.text)
        await choose(probe, 'messages')
        await displayed([probe], lambda: 'Saved messages' in probe.text)
        probe.send(b'Offline TUI reply\r')
        await displayed([probe], lambda: 'Reply with private quote' in probe.text)
        probe.send(b'Reply with private quote\r')
        await displayed([probe], lambda: 'Replying to Amplifier' in probe.text)
        await asyncio.sleep(.2)
        saved = json.loads(store.path.read_text())
        assert saved['drafts'][session] == 'Private terminal quote draft' and saved['quotes'][session]['reference']['messageId'] == message['messageReference']['messageId']
        await asyncio.to_thread(probe.close)
        probes.remove(probe)
        probe = Probe(args, 120, 40, guard_terminal_modes=True, env={'PYTHONPATH': ''})
        probes.append(probe)
        await displayed([probe], lambda: 'Replying to Amplifier' in probe.text and 'Private terminal quote draft' in probe.text)
        await choose(probe, 'messages')
        await displayed([probe], lambda: 'Saved messages' in probe.text)
        probe.send(b'Offline TUI reply\r')
        await displayed([probe], lambda: 'Inspect shared reactions' in probe.text)
        probe.send(b'Inspect shared reactions\r')
        await displayed([probe], lambda: 'Shared reactions' in probe.text)
        (root / 'drop-next-reaction').touch()
        probe.send(b'Add \xf0\x9f\x91\x8d\r')
        await displayed([probe], lambda: 'Reaction is not confirmed' in probe.text)
        await asyncio.to_thread(probe.close)
        probes.remove(probe)
        probe = Probe(args, 120, 40, guard_terminal_modes=True, env={'PYTHONPATH': ''})
        probes.append(probe)
        await displayed([probe], lambda: 'Replying to Amplifier' in probe.text and 'Private terminal quote draft' in probe.text)
        await choose(probe, 'messages')
        await displayed([probe], lambda: 'Saved messages' in probe.text)
        probe.send(b'Offline TUI reply\r')
        await displayed([probe], lambda: 'Inspect shared reactions' in probe.text)
        probe.send(b'Inspect shared reactions\r')
        await displayed([probe], lambda: 'Inspect original reaction receipt' in probe.text)
        probe.send(b'Inspect original reaction receipt\r')
        await displayed([probe], lambda: 'replayed' in probe.text and 'false' in probe.text)
        assert next(iter(json.loads(store.path.read_text())['messageEffects'].values()))['status'] == 'confirmed'
        probe.send(b'\x1b')
        # Native naming can call the deterministic provider independently; exact
        # protocol frames below prove these interactions admitted no extra turn.
        observer, _ = await open_bridge(url, root, workspace, 'observer', session)
        try:
            # Missing references refuse locally and never clear either private draft.
            refused = await observer.dispatch(request(observer, 'message.reply', message_id='missing'))
            assert not refused[0] and not observer.messages.quote()
            await observer.dispatch(request(observer, 'submit', text='busy-fixture'))
            await wait_for(lambda: (root / 'busy.entered').exists())
            await displayed([probe], lambda: '[ Queue ]' in probe.text or 'Working' in probe.text or 'running' in probe.text)
            turn = observer.session['activeTurnId']
            probe.send(b'\x03')
            await displayed([probe], lambda: (root / 'cancellation-requested.json').exists())
            assert json.loads((root / 'cancellation-requested.json').read_text())['action']['turnId'] == turn
            # Standard Stop requests cancellation; it is not force termination
            # of a blocked provider. Permit the owned fixture to settle gracefully.
            (root / 'busy.release').touch()
            async with asyncio.timeout(30):
                while observer.session.get('activeTurnId'):
                    probe.read(0)
                    await asyncio.sleep(.02)
        finally:
            (root / 'busy.release').touch()
            await observer.close()
        saved = json.loads(store.path.read_text())
        assert saved['drafts'][session] == 'Private terminal quote draft' and saved['quotes'][session]
        evidence = Path(os.environ.get('TUI_EVIDENCE_DIR', root))
        evidence.mkdir(parents=True, exist_ok=True)
        (root / 'expected-turns.json').write_text('2')
        (evidence / 'installed-message-terminal.txt').write_text(probe.text)
        (evidence / 'installed-message-terminal.ansi').write_bytes(bytes(probe.raw))
    finally:
        for probe in probes:
            evidence = Path(os.environ.get('TUI_EVIDENCE_DIR', root))
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / 'installed-message-terminal-last.txt').write_text(probe.text)
            await asyncio.to_thread(probe.close)
