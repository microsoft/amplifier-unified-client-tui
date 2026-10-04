"""Real published AHP CLI + independent ACP process; no host implementation imports."""
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

import pytest
import pytest_asyncio

from amplifier_tui.client_state import ClientState
from amplifier_tui.unified_client import UnifiedBridge
from amplifier_tui.unified_transport import Transport

ROOT = Path(__file__).resolve().parents[1]
ENTRY = os.environ.get('AHP_HOST_ENTRY')
pytestmark = pytest.mark.skipif(not ENTRY, reason='Set independent AHP_HOST_ENTRY CLI')


@pytest_asyncio.fixture
async def ahp_host(tmp_path):
    config = tmp_path / 'host.json'
    log = tmp_path / 'prompts.jsonl'
    config.write_text(json.dumps({'stateDirectory': str(tmp_path / 'host'), 'port': 0,
        'allowedWorkspaceRoots': [str(tmp_path)], 'engines': [{'id': 'fixture', 'label': 'ACP Fixture',
        'command': 'node', 'args': [str(ROOT / 'tests/fixtures/acp_agent.mjs')],
        'env': {'FIXTURE_LOG': str(log), 'FIXTURE_MODELS': '1', 'FIXTURE_CONFIG_LOG': str(tmp_path / 'settings.jsonl')}}]}))
    entry = str(ROOT / 'tests/fixtures/ahp_fixture_host.mjs') if os.environ.get('AHP_HOST_MODULE') else ENTRY
    process = await asyncio.create_subprocess_exec('node', entry, '--config', str(config),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    async with asyncio.timeout(10):
        line = await process.stdout.readline()
    assert line, (await process.stderr.read()).decode()
    url = json.loads(line)['url']
    yield url, tmp_path, log
    process.terminate()
    await process.wait()


async def wait_for(predicate):
    async with asyncio.timeout(10):
        while not predicate():
            await asyncio.sleep(.01)


def request(bridge, op, **kwargs):
    return {'op': op, 'session_id': bridge.selected or '', 'request_id': str(uuid.uuid4()), **kwargs}


async def view(root, url, *, session=None, identity=None):
    state = ClientState(root, url, identity)
    transport = Transport(url, '', state.identity)
    events = []
    bridge = UnifiedBridge(events.append, transport, state, session=session, workspace=str(root.parent))
    await bridge.open()
    return bridge, events


async def test_two_ahp_clients_local_drafts_streaming_and_reconnect_no_replay(ahp_host):
    url, root, log = ahp_host
    a, _ = await view(root / 'a', url)
    b = None
    try:
        assert (await a.dispatch(request(a, 'submit', text='first')))[0]
        await wait_for(lambda: any(i['text'] == 'Echo: first' for i in a.items()))
        b, _ = await view(root / 'b', url, session=a.selected)
        await a.dispatch(request(a, 'draft', text='private A'))
        await b.dispatch(request(b, 'draft', text='private B'))
        assert a.store.data['drafts'][a.selected] == 'private A'
        assert b.store.data['drafts'][b.selected] == 'private B'
        before = len(log.read_text().splitlines())
        generation = b.transport.generation
        await b.transport.rpc('disconnect')
        await wait_for(lambda: b.transport.online and b.transport.generation > generation)
        assert len(log.read_text().splitlines()) == before
        assert b.store.data['drafts'][b.selected] == 'private B'
        assert (await a.dispatch(request(a, 'submit', text='hello again')))[0]
        await wait_for(lambda: any(i['text'] == 'Echo: hello again' for i in b.items()))
        assert len(log.read_text().splitlines()) == before + 1
        assert not a.store.data['outbox']
    finally:
        await a.close()
        if b:
            await b.close()


async def test_permissions_use_offered_option_identity_and_shared_result(ahp_host):
    url, root, _ = ahp_host
    a, _ = await view(root / 'a', url)
    try:
        assert (await a.dispatch(request(a, 'submit', text='approval')))[0]
        await wait_for(lambda: a.session.get('approvals'))
        approval = a.session['approvals'][0]
        option = next(o for o in approval['options'] if '[allow]' in o)
        assert (await a.dispatch(request(a, 'decision', approval_id=approval['id'], option=option)))[0]
        await wait_for(lambda: a.session['status'] == 'ready')
        assert any(i['kind'] == 'tool' and i['status'] == 'completed' for i in a.items())
        assert not a.session['approvals']
    finally:
        await a.close()


async def test_host_work_survives_detach_and_cold_client_restores_private_draft(ahp_host):
    url, root, log = ahp_host
    a, _ = await view(root / 'a', url, identity='recoverable')
    await a.dispatch(request(a, 'submit', text='slow'))
    session = a.selected
    await a.dispatch(request(a, 'draft', text='retained intent'))
    await a.close()
    await asyncio.sleep(.35)
    b, _ = await view(root / 'a', url, identity='recoverable')
    try:
        await wait_for(lambda: any(i['text'] == 'Echo: slow' for i in b.items()))
        assert b.selected == session
        assert b.store.data['drafts'][session] == 'retained intent'
        assert len(log.read_text().splitlines()) == 1
    finally:
        await b.close()


async def test_unknown_delivery_is_read_only_on_retry_and_never_replayed(ahp_host):
    url, root, log = ahp_host
    a, _ = await view(root / 'a', url)
    try:
        await a.dispatch(request(a, 'submit', text='first'))
        await wait_for(lambda: not a.store.data['outbox'])
        identity = str(uuid.uuid4())
        a.store.data['outbox'][identity] = {'session': a.selected, 'action': 'conversation.send',
            'args': {'text': 'DO NOT RESEND'}, 'status': 'unknown'}
        a.store.save()
        before = log.read_text()
        result = await a.dispatch(request(a, 'retry_delivery', id=identity))
        assert result[0] is False
        assert log.read_text() == before
        assert a.store.data['outbox'][identity]['status'] == 'unknown'
        assert not (await a.dispatch(request(a, 'continue_here')))[0]
    finally:
        await a.close()


async def test_selected_history_window_and_explicit_fetch(ahp_host):
    url, root, _ = ahp_host
    a, events = await view(root / 'a', url)
    b = None
    try:
        for index in range(53):
            await a.dispatch(request(a, 'submit', text=f'row {index}'))
            await wait_for(lambda: a.session.get('status') == 'ready')
        session = a.selected
        await a.dispatch(request(a, 'switch', target='new', draft=''))
        b, _ = await view(root / 'b', url, session=session)
        assert len([message for message in b.session['messages'] if message['role'] == 'user']) == 50
        assert b.session['historyCursor']
        await b.transport.command(session, 'session.history', {}, str(uuid.uuid4()))
        await wait_for(lambda: len([message for message in b.session['messages'] if message['role'] == 'user']) == 53)
        assert not b.session['historyCursor']
        await b.dispatch(request(b, 'rename', title='Renamed through AHP'))
        await wait_for(lambda: b.session['title'] == 'Renamed through AHP')
        page = await b.transport.sessions(workspace=str(root))
        assert len(page['items']) == 1
        assert page['items'][0]['title'] == 'Renamed through AHP'
    finally:
        await a.close()
        if b:
            await b.close()


async def test_connected_imports_no_execution_runtime(ahp_host):
    url, root, _ = ahp_host
    a, _ = await view(root / 'a', url)
    try:
        process = await asyncio.create_subprocess_exec(sys.executable, '-c', "import sys; import amplifier_tui.connected; assert not any(name in sys.modules for name in ('amplifier_core','amplifier_foundation','amplifier_app_cli'))")
        assert await process.wait() == 0
        assert a.transport.attached['protocolVersion'] == '0.9.0'
    finally:
        await a.close()


async def test_client_effect_receipt_precedes_renderer_and_unknown_never_repeats(ahp_host):
    url, root, _ = ahp_host
    a, events = await view(root / 'a', url)
    try:
        await a.dispatch(request(a, 'submit', text='first'))
        await wait_for(lambda: a.selected is not None)
        packet = {'session': a.selected, 'tool': {'toolCallId': 'owned-effect', 'toolName': 'amplifier_tui_action_fixture', 'toolInput': json.dumps({'action': 'draft.replace', 'expectedRevision': 1, 'args': {'text': 'not sent'}})}}
        pending = asyncio.create_task(a.client_tool(packet))
        await wait_for(lambda: any(e['type'] == 'client_ui' for e in events))
        key = a.selected + '/owned-effect'
        persisted = json.loads(a.store.path.read_text())
        assert persisted['clientEffects'][key]['status'] == 'unknown'
        query = next(e for e in events if e['type'] == 'client_ui')
        await a.dispatch(request(a, 'client_ui_reply', token=query['token'], result={'accepted': True, 'revision': 2}))
        assert (await pending)['success']
        before = len(events)
        assert (await a.client_tool(packet))['success']
        assert len(events) == before
        packet['tool']['toolCallId'] = 'uncertain-effect'
        a.store.data['clientEffects'][a.selected + '/uncertain-effect'] = {'status': 'unknown'}
        a.store.save()
        result = await a.client_tool(packet)
        assert result['error']['code'] == 'CLIENT_OUTCOME_UNKNOWN'
        assert len(events) == before
    finally:
        await a.close()


async def test_long_stream_local_ipc_is_linear_and_reconnect_restores_exact_text(ahp_host):
    url, root, _ = ahp_host
    a, events = await view(root / 'stream', url)
    try:
        received = a.transport.received_bytes
        start = len(events)
        await a.dispatch(request(a, 'submit', text='long-stream'))
        await wait_for(lambda: any(i['text'].endswith('LONG-STREAM-COMPLETE') for i in a.items()))
        await wait_for(lambda: a.session['status'] == 'ready')
        expected = ''.join(f'chunk-{i:03d} ' + 'x' * 1013 + '\n' for i in range(128)) + 'LONG-STREAM-COMPLETE'
        assert any(i['text'] == expected for i in a.items())
        helper_bytes = a.transport.received_bytes - received
        renderer_bytes = sum(len(json.dumps(event).encode()) for event in events[start:])
        assert any(event['type'] == 'delta' for event in events[start:])
        # Full baselines/final transitions are allowed; copying every growing prefix is not.
        assert helper_bytes < 8 * len(expected), helper_bytes
        assert renderer_bytes < 8 * len(expected), renderer_bytes
        evidence = Path(os.environ.get('TUI_EVIDENCE_DIR', root))
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / 'stream-ipc.json').write_text(json.dumps({'chunks': 128, 'responseBytes': len(expected), 'helperBytes': helper_bytes, 'rendererBytes': renderer_bytes}, indent=2))
        generation = a.transport.generation
        await a.transport.rpc('disconnect')
        await wait_for(lambda: a.transport.online and a.transport.generation > generation)
        assert any(i['text'] == expected for i in a.items())
    finally:
        await a.close()


async def test_standard_model_settings_confirm_refusal_unknown_and_receipt_no_replay(ahp_host):
    url, root, prompt_log = ahp_host
    transport = Transport(url, '', 'standard-config')
    await transport.open()
    identity = 'ahp-session:/' + str(uuid.uuid4())
    await transport.rpc('create', session=identity, cwd=root.as_uri(), provider='fixture')
    events = []
    bridge = UnifiedBridge(events.append, transport, ClientState(root / 'config-client', url, 'standard-config'), session=identity)
    try:
        await bridge.open()
        await bridge.dispatch(request(bridge, 'draft', text='Private model-change draft'))
        assert (await bridge.dispatch(request(bridge, 'settings')))[0]
        assert (await bridge.dispatch(request(bridge, 'setting_choices', property='model')))[0]
        choices = next(e for e in reversed(events) if e['type'] == 'setting_choices')
        assert len(choices['choices']) == 9
        assert choices['current'] == 'openai/gpt-6-sol'
        assert (await bridge.dispatch(request(bridge, 'setting_set', property='model', value='openai/gpt-6-astra')))[0]
        assert bridge.session['config']['values']['model'] == 'openai/gpt-6-astra'
        refused = await bridge.dispatch(request(bridge, 'setting_set', property='model', value='fixture/model-2'))
        assert not refused[0] and 'declined' in refused[1] and 'RPC' not in refused[1]
        assert list(bridge.store.data['configEffects'].values())[-1]['status'] == 'refused'
        original = transport.command
        async def lost_result(*args, **kwargs):
            await original(*args, **kwargs)
            raise OSError('Simulated lost result after actual installed host applied setting')
        transport.command = lost_result
        unknown = await bridge.dispatch(request(bridge, 'setting_set', property='model', value='fixture/model-3'))
        assert not unknown[0] and 'not confirmed' in unknown[1]
        effect_id, effect = list(bridge.store.data['configEffects'].items())[-1]
        assert effect['status'] == 'unknown'
        transport.command = original
        count = len((root / 'settings.jsonl').read_text().splitlines())
        assert (await bridge.dispatch(request(bridge, 'host_receipt', id=effect_id)))[0]
        assert len((root / 'settings.jsonl').read_text().splitlines()) == count == 3
        assert effect['status'] == 'unknown'  # Current readback does not prove the original outcome.
        assert bridge.store.data['drafts'][identity] == 'Private model-change draft'
        assert not prompt_log.exists()  # Configuration never submits a model prompt.
        commands = next(e for e in reversed(events) if e['type'] == 'commands')['commands']
        assert '/settings' in commands
        assert 'message.reply' not in commands and 'message.reaction' not in commands
        for op in ('message.reply', 'message.reaction'):
            unavailable = await bridge.dispatch(request(bridge, op))
            assert not unavailable[0] and 'not available' in unavailable[1]
        assert len((root / 'settings.jsonl').read_text().splitlines()) == count
        bridge.store.data['hostEffects'] = {'saved-copy': {'session': identity, 'operation': 'fork', 'args': {'commandId': 'saved-copy'}, 'status': 'unknown', 'error': 'RPC -32011: Indexed family coverage is incomplete or stale'}}
        original_lifecycle = transport.lifecycle
        async def lookup_unavailable(*args, **kwargs):
            raise OSError('Receipt lookup is temporarily unavailable')
        transport.lifecycle = lookup_unavailable
        inspected = await bridge.dispatch(request(bridge, 'host_receipt', id='saved-copy'))
        assert not inspected[0] and 'RPC' not in inspected[1]
        details = next(e for e in reversed(events) if e['type'] == 'host_review')['detail']
        assert 'Indexed family coverage' in details and 'saved-copy' in details
        assert bridge.store.data['hostEffects']['saved-copy']['status'] == 'unknown'
        assert len((root / 'settings.jsonl').read_text().splitlines()) == count
        transport.lifecycle = original_lifecycle
        transport.attached = {}
        bridge.publish_controls()
        controls = next(e for e in reversed(events) if e['type'] == 'commands')['commands']
        assert '/details' not in controls and '/recovery' not in controls and '/managed-files' not in controls
        bridge.session['config'] = {'schema': {'properties': {'model': {'enum': ['read-only'], 'sessionMutable': False}}}}
        bridge.publish_controls()
        assert '/settings' not in next(e for e in reversed(events) if e['type'] == 'commands')['commands']
    finally:
        await bridge.close()
