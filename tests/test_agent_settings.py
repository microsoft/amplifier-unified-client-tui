"""Shared settings/naming actions through actual client tools and Ratatui PTYs."""
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

import pytest
from test_ahp_client import ahp_host as ahp_host  # noqa: F401
from test_ahp_client import request, view, wait_for
from test_ahp_terminal import Probe, displayed, saved_draft_state

from amplifier_tui.unified_transport import Transport

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not os.environ.get('AHP_HOST_MODULE'), reason='Independent public Host required')


def packet(session, action, args, tool_id=None):
    return {'session': session, 'tool': {'toolCallId': tool_id or str(uuid.uuid4()),
            'toolName': 'amplifier_tui_action_fixture',
            'toolInput': json.dumps({'action': action, 'expectedRevision': 1, 'args': args})}}


async def guarded(bridge, events, item, *, accepted=True, before_reply=None):
    offset = len(events)
    task = asyncio.create_task(bridge.client_tool(item))
    await wait_for(lambda: any(row['type'] == 'client_ui' for row in events[offset:]))
    row = next(row for row in events[offset:] if row['type'] == 'client_ui')
    if before_reply:
        before_reply()
    await bridge.dispatch(request(bridge, 'client_ui_reply', token=row['token'],
                                 result={'accepted': accepted, 'revision': 2, 'error': 'Stale actual renderer revision'}))
    return await task


async def test_agent_change_argument_session_and_receipt_guards(ahp_host):
    url, root, log = ahp_host
    bridge, events = await view(root / 'bridge', url)
    try:
        await bridge.dispatch(request(bridge, 'submit', text='seed'))
        await wait_for(lambda: bridge.session.get('status') == 'ready')
        await bridge.dispatch(request(bridge, 'draft', text='private draft'))
        original = bridge.selected
        for action, args in [('setting_set', {'property': [], 'value': 'bad'}),
                             ('rename', {'title': 'wrong', 'session_id': 'ahp-session:/other'}),
                             ('host_receipt', {'id': {}})]:
            result = await guarded(bridge, events, packet(original, action, args))
            assert not result['success']
        stale = await guarded(bridge, events, packet(original, 'rename', {'title': 'stale'}), accepted=False)
        assert not stale['success']
        wrong = await bridge.client_tool(packet('ahp-session:/other', 'rename', {'title': 'other'}))
        assert not wrong['success']
        def change_target():
            bridge.selected = 'ahp-session:/new-selection'
        changed = await guarded(bridge, events, packet(original, 'rename', {'title': 'retargeted'}), before_reply=change_target)
        assert not changed['success']
        bridge.selected = original
        assert not bridge.store.data.get('hostEffects')
        assert not (root / 'settings.jsonl').exists()
        assert bridge.store.data['drafts'][original] == 'private draft'
        assert len(log.read_text().splitlines()) == 1
        legacy_id = str(uuid.uuid4())
        bridge.store.data['outbox'][legacy_id] = {'session': original, 'action': 'session.rename',
            'args': {'title': 'Legacy uncertain name'}, 'status': 'unknown'}
        bridge.store.save()
        async def unbound_remote_receipt(*args):
            pytest.fail('A local naming UUID is not a remote receipt identity')
        bridge.transport.receipt = unbound_remote_receipt
        recovered = await guarded(bridge, events, packet(original, 'host_receipt', {'id': legacy_id}))
        assert recovered['success'] and recovered['structuredContent']['original']['status'] == 'unknown'
        assert (await bridge.dispatch(request(bridge, 'retry_delivery', id=legacy_id)))[0]
        assert bridge.store.data['outbox'][legacy_id]['status'] == 'unknown'
    finally:
        await bridge.close()


async def create_session(url, root):
    transport = Transport(url, '', 'seed-settings')
    try:
        await transport.open()
        identity = 'ahp-session:/' + str(uuid.uuid4())
        await transport.rpc('create', session=identity, cwd=root.as_uri(), provider='fixture')
        return identity
    finally:
        await transport.close()


def terminal(url, root, session, client='terminal'):
    executable = os.environ.get('TUI_CONNECTED_EXECUTABLE')
    args = [executable] if executable else [sys.executable, '-m', 'amplifier_tui.connected']
    return Probe([*args, '--server', url, '--workspace', str(root), '--state-dir', str(root / client),
                  '--client', client, '--session', session], 120, 40, guard_terminal_modes=True,
                 env={'PYTHONPATH': ''} if executable else None)


def ui_rows(root):
    path = root / 'ui-results.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def actions(root):
    return [row['result'] for row in ui_rows(root) if row['kind'] == 'action']


def capture(probe, name):
    evidence = Path(os.environ.get('TUI_EVIDENCE_DIR', '.evidence/agent-settings'))
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / (name+'.txt')).write_text(probe.text)
    (evidence / (name+'.ansi')).write_bytes(bytes(probe.raw))
    from terminal_raster import render_terminal
    render_terminal(probe, evidence / (name+'.png'), font_size=16)


@pytest.mark.skipif(os.environ.get('TUI_TEST_CANDIDATES') != '1', reason='Updated native renderer required')
async def test_actual_agent_settings_naming_and_refusal_preserve_two_drafts(ahp_host):
    url, root, log = ahp_host
    session = await create_session(url, root)
    a, b = terminal(url, root, session), terminal(url, root, session, 'other-terminal')
    observer = None
    try:
        await displayed([a, b], lambda: 'UNIFIED' in a.text and 'UNIFIED' in b.text)
        a.send(b'Private target draft')
        b.send(b'Other private draft')
        await saved_draft_state(a, root/'terminal/connections/terminal.json', session, 'Private target draft')
        await saved_draft_state(b, root/'other-terminal/connections/other-terminal.json', session, 'Other private draft')
        script = [{'action': 'settings', 'args': {}},
                  {'action': 'setting_choices', 'args': {'property': 'model'}},
                  {'action': 'setting_set', 'args': {'property': 'model', 'value': 'openai/gpt-6-astra'}},
                  {'action': 'setting_set', 'args': {'property': 'mode', 'value': 'fast'}},
                  {'action': 'rename', 'args': {'title': 'Named by selected agent'}},
                  {'action': 'host_effects', 'args': {}},
                  {'action': 'host_receipt', 'args': {'id': '$original'}},
                  {'action': 'setting_set', 'args': {'property': 'model', 'value': 'fixture/model-2'}}]
        (root/'ui-script.json').write_text(json.dumps(script))
        observer, _ = await view(root/'observer', url, session=session)
        assert (await observer.dispatch(request(observer, 'submit', text='client-changes')))[0]
        await displayed([a,b], lambda: len(actions(root)) == len(script), timeout=40)
        results = actions(root)
        assert all(row['success'] for row in results[:-1]), results
        assert not results[-1]['success']
        assert results[2]['structuredContent']['original']['status'] == 'confirmed'
        assert results[4]['structuredContent']['original']['status'] == 'confirmed'
        assert results[4]['structuredContent']['original']['id'] == results[6]['structuredContent']['original']['id']
        assert results[-1]['structuredContent']['original']['status'] == 'refused'
        initial = ui_rows(root)[0]['result']['structuredContent']
        assert 'draft' not in initial and initial['connected']
        assert {row['id'] for row in initial['settings']} >= {'model', 'mode'}
        await wait_for(lambda: observer.session.get('title') == 'Named by selected agent')
        for probe, client, draft in [(a,'terminal','Private target draft'), (b,'other-terminal','Other private draft')]:
            state = await saved_draft_state(probe, root/client/'connections'/f'{client}.json', session, draft)
            assert state['drafts'][session] == draft
        assert len(log.read_text().splitlines()) == 1  # Only the explicit fixture turn; changes never prompt.
        assert len((root/'settings.jsonl').read_text().splitlines()) == 2
        capture(a, 'agent-settings-naming-refusal')
    finally:
        if observer:
            await observer.close()
        await asyncio.gather(asyncio.to_thread(a.close), asyncio.to_thread(b.close))


@pytest.mark.skipif(os.environ.get('TUI_TEST_CANDIDATES') != '1', reason='Updated native renderer required')
async def test_actual_agent_change_refuses_unflushed_keystroke_and_other_target(ahp_host):
    url, root, log = ahp_host
    session = await create_session(url, root)
    probe = terminal(url, root, session)
    observer = None
    try:
        await displayed([probe], lambda: 'UNIFIED' in probe.text)
        release = root/'continue-agent'
        (root/'ui-script.json').write_text(json.dumps([
            {'action': 'rename', 'args': {'title': 'Stale name'}, 'pause': str(release)},
            {'action': 'rename', 'args': {'title': 'Other name', 'session_id': 'ahp-session:/other'}},
            {'action': 'rename', 'args': {'title': 'Fresh name'}}]))
        observer, _ = await view(root/'observer', url, session=session)
        assert (await observer.dispatch(request(observer, 'submit', text='client-changes')))[0]
        await displayed([probe], lambda: len(ui_rows(root)) == 1)
        probe.send(b'Unflushed private keystrokes')
        await displayed([probe], lambda: 'Unflushed private keystrokes' in probe.text)
        release.touch()
        await displayed([probe], lambda: len(actions(root)) == 3)
        results = actions(root)
        assert [row['success'] for row in results] == [False, False, True], results
        state = await saved_draft_state(probe, root/'terminal/connections/terminal.json', session, 'Unflushed private keystrokes')
        assert len(state['hostEffects']) == 1
        assert next(iter(state['hostEffects'].values()))['args']['title'] == 'Fresh name'
        assert not (root/'settings.jsonl').exists()
        assert len(log.read_text().splitlines()) == 1
        capture(probe, 'agent-stale-and-target-refusal')
    finally:
        if observer:
            await observer.close()
        await asyncio.to_thread(probe.close)


@pytest.mark.parametrize('operation,args,kind,fields', [
    ('setting_set', {'property': 'model', 'value': 'openai/gpt-6-astra'}, 'session/configChanged', {'config': {'model': 'openai/gpt-6-astra'}}),
    ('rename', {'title': 'Lost original name'}, 'session/titleChanged', {'title': 'Lost original name'})])
@pytest.mark.skipif(os.environ.get('TUI_TEST_CANDIDATES') != '1', reason='Updated native renderer required')
async def test_actual_agent_lost_original_echo_inspect_reload_no_replay(ahp_host, operation, args, kind, fields):
    url, root, log = ahp_host
    session = await create_session(url, root)
    fault = root/'fault'
    fault.mkdir()
    proxy = await asyncio.create_subprocess_exec('node', str(ROOT/'tests/fixtures/pending_fault_proxy.mjs'), url, str(fault), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    probe = observer = None
    try:
        async with asyncio.timeout(10):
            proxy_url = json.loads(await proxy.stdout.readline())['url']
        probe = terminal(proxy_url, root, session)
        await displayed([probe], lambda: 'UNIFIED' in probe.text)
        probe.send(b'Original private draft')
        await saved_draft_state(probe, root/'terminal/connections/terminal.json', session, 'Original private draft')
        (fault/'drop.json').write_text(json.dumps({'type': kind, 'fields': fields, 'channel': session}))
        release = root/'inspect-after-reconnect'
        (root/'ui-script.json').write_text(json.dumps([{'action': operation, 'args': args}, {'action': 'host_receipt', 'args': {'id': '$original'}, 'before': str(release)}]))
        observer, _ = await view(root/'observer', url, session=session)
        assert (await observer.dispatch(request(observer, 'submit', text='client-changes')))[0]
        await displayed([probe], lambda: len(actions(root)) == 1, timeout=40)
        await displayed([probe], lambda: (fault/'registered.json').exists()
                        and json.loads((fault/'registered.json').read_text())['generation'] >= 2)
        state_path = root/'terminal/connections/terminal.json'
        await displayed([probe], lambda: any(row.get('result', {}).get('structuredContent', {}).get('original', {}).get('status') == 'unknown'
                        for row in json.loads(state_path.read_text()).get('clientEffects', {}).values()))
        release.touch()
        await displayed([probe], lambda: len(actions(root)) == 2, timeout=40)
        first, inspected = actions(root)
        assert (fault/'dropped.json').exists(), first
        echo = json.loads((fault/'dropped.json').read_text())['params']
        assert echo['origin']['clientId'] == 'terminal' and type(echo['origin']['clientSeq']) is int
        assert echo['channel'] == session and echo['action']['type'] == kind
        assert all(echo['action'][key] == value for key, value in fields.items())
        assert not first['success'] and inspected['success'], actions(root)
        original = inspected['structuredContent']['original']
        assert original['status'] == 'unknown'
        assert first['error']['code'] == 'CLIENT_OUTCOME_UNKNOWN'
        assert inspected['structuredContent']['original']['status'] == 'unknown'
        await wait_for(lambda: observer.session.get('status') == 'ready')
        capture(probe, 'agent-lost-echo-'+operation)
        await asyncio.to_thread(probe.close)
        probe=None
        before = len(log.read_text().splitlines())
        probe = terminal(proxy_url, root, session)
        await displayed([probe], lambda: 'UNIFIED' in probe.text and 'Original private draft' in probe.text)
        state = await saved_draft_state(probe, root/'terminal/connections/terminal.json', session, 'Original private draft')
        collection = state['configEffects'] if operation == 'setting_set' else state['hostEffects']
        assert collection[original['id']]['status'] == 'unknown'
        probe.send(b'\x1bOS')
        await displayed([probe], lambda: 'Actions' in probe.text)
        probe.send(b'Original receipts\r')
        await displayed([probe], lambda: 'Original host effect receipts' in probe.text)
        probe.send(b'\r')
        await displayed([probe], lambda: original['id'][:8] in probe.text and 'Host review' in probe.text)
        capture(probe, 'agent-reloaded-original-id-'+operation)
        for _ in range(8):
            if 'unknown' in probe.text:
                break
            before_page = probe.text
            probe.send(b'\x1b[6~')
            await displayed([probe], lambda: probe.text != before_page)
        assert 'unknown' in probe.text and 'Host review' in probe.text
        capture(probe, 'agent-reloaded-original-'+operation)
        frames = [json.loads(line) for line in (fault/'sent.jsonl').read_text().splitlines()]
        mutations = [row for row in frames if row.get('params',{}).get('action',{}).get('type') == kind]
        assert len(mutations) == 1
        assert not any(row.get('method') == 'x-commandReceipt' and row.get('params',{}).get('commandId') == original['id'] for row in frames)
        assert len(log.read_text().splitlines()) == before == 1
        if operation == 'setting_set':
            assert len((root/'settings.jsonl').read_text().splitlines()) == 1
    finally:
        if observer:
            await observer.close()
        if probe:
            capture(probe, 'last-fault-'+operation)
            await asyncio.to_thread(probe.close)
        proxy.terminate()
        await proxy.wait()


@pytest.mark.skipif(os.environ.get('TUI_TEST_CANDIDATES') != '1', reason='Updated native renderer required')
async def test_actual_agent_name_does_not_follow_human_selection(ahp_host):
    url, root, _ = ahp_host
    session = await create_session(url, root)
    probe = terminal(url, root, session)
    observer = None
    try:
        await displayed([probe], lambda: 'UNIFIED' in probe.text)
        probe.send(b'Draft in original conversation')
        await saved_draft_state(probe, root/'terminal/connections/terminal.json', session, 'Draft in original conversation')
        release = root/'name-after-switch'
        (root/'ui-script.json').write_text(json.dumps([{'action': 'rename', 'args': {'title': 'Retargeted name'}, 'pause': str(release)}]))
        observer, _ = await view(root/'observer', url, session=session)
        assert (await observer.dispatch(request(observer, 'submit', text='client-changes')))[0]
        await displayed([probe], lambda: len(ui_rows(root)) == 1)
        probe.send(b'\x1bOS')
        await displayed([probe], lambda: 'Actions' in probe.text)
        probe.send(b'New conversation\r')
        state_path = root/'terminal/connections/terminal.json'
        await displayed([probe], lambda: json.loads(state_path.read_text())['session'] is None)
        await wait_for(lambda: not any(row.get('clientId') == 'terminal' for row in observer.transport.sessions_state.get(session, {}).get('activeClients', [])))
        release.touch()
        await displayed([probe], lambda: len(actions(root)) == 1)
        assert not actions(root)[0]['success']
        state = json.loads(state_path.read_text())
        assert state['session'] is None and state['drafts'][session] == 'Draft in original conversation'
        assert not state.get('hostEffects')
        assert observer.session['title'] != 'Retargeted name'
        capture(probe, 'agent-selection-refusal')
    finally:
        if observer:
            await observer.close()
        await asyncio.to_thread(probe.close)
