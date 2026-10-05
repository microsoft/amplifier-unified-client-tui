"""Connected pending inputs through a sealed public Host and independent ACP peer."""
import asyncio
import json
import os
from pathlib import Path

import pytest
import pytest_asyncio
from test_ahp_client import request, view, wait_for

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not os.environ.get('AHP_HOST_MODULE'), reason='Set sealed public Host module')


@pytest_asyncio.fixture
async def pending_host(tmp_path, request):
    log = tmp_path / 'prompts.jsonl'
    config = tmp_path / 'host.json'
    env = {'FIXTURE_LOG': str(log)}
    if getattr(request, 'param', '') == 'no-steer':
        env['FIXTURE_NO_STEER'] = '1'
    config.write_text(json.dumps({'stateDirectory': str(tmp_path / 'host'), 'port': 0,
        'allowedWorkspaceRoots': [str(tmp_path)], 'engines': [{'id': 'fixture', 'label': 'Pending fixture',
        'command': 'node', 'args': [str(ROOT / 'tests/fixtures/pending_agent.mjs')], 'env': env}]}))
    process = await asyncio.create_subprocess_exec('node', str(ROOT / 'tests/fixtures/ahp_fixture_host.mjs'),
        '--config', str(config), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    async with asyncio.timeout(10):
        line = await process.stdout.readline()
    assert line, (await process.stderr.read()).decode()
    yield json.loads(line)['url'], tmp_path, log
    process.terminate()
    await process.wait()


async def seeded(host):
    url, root, log = host
    a, events = await view(root / 'a', url)
    assert (await a.dispatch(request(a, 'submit', text='seed')))[0]
    await wait_for(lambda: a.session['status'] == 'ready')
    return a, events, log


def texts(log):
    return [' '.join(b['text'] for b in json.loads(line)['prompt'] if b['type'] == 'text')
            for line in log.read_text().splitlines()]


async def test_shared_queue_edit_remove_and_natural_drain(pending_host):
    a, events, log = await seeded(pending_host)
    b = None
    try:
        b, _ = await view(pending_host[1] / 'b', pending_host[0], session=a.selected)
        await a.dispatch(request(a, 'draft', text='private draft'))
        assert (await a.dispatch(request(a, 'submit', text='busy')))[0]
        await wait_for(lambda: a.session['status'] == 'working')
        assert (await a.dispatch(request(a, 'queue', text='queued first')))[0]
        await wait_for(lambda: bool(b.session.get('queuedMessages')))
        first = b.session['queuedMessages'][0]['id']
        assert (await b.dispatch(request(b, 'queue_edit', id=first, text='edited shared')))[0]
        assert (await b.dispatch(request(b, 'queue', text='remove me')))[0]
        remove = next(row['id'] for row in b.session['queuedMessages'] if row['id'] != first)
        assert (await b.dispatch(request(b, 'queue_remove', id=remove)))[0]
        await wait_for(lambda: 'edited shared' in texts(log) and a.session['status'] == 'ready')
        assert texts(log) == ['seed', 'busy', 'edited shared']
        assert not a.session['queuedMessages']
        assert a.store.data['drafts'][a.selected] == 'private draft'
        assert any(e['type'] == 'followups' and any(row['id'] == first for row in e['rows']) for e in events)
        assert not (await a.dispatch(request(a, 'queue_edit', id=first, text='replay')))[0]
    finally:
        await a.close()
        if b:
            await b.close()


async def test_cancel_holds_queue_and_explicit_same_id_rearms(pending_host):
    a, _, log = await seeded(pending_host)
    try:
        await a.dispatch(request(a, 'submit', text='busy'))
        await wait_for(lambda: a.session['status'] == 'working')
        assert (await a.dispatch(request(a, 'queue', text='held follow-up')))[0]
        identity = a.session['queuedMessages'][0]['id']
        assert (await a.dispatch(request(a, 'stop')))[0]
        await wait_for(lambda: a.session['status'] == 'ready')
        assert texts(log) == ['seed', 'busy']
        assert a.session['queuedMessages'][0]['message']['_meta']['amplifier.dev/queue']['held']
        assert not (await a.dispatch(request(a, 'queue_pause')))[0]
        assert (await a.dispatch(request(a, 'queue_run', id=identity)))[0]
        await wait_for(lambda: len(texts(log)) == 3 and a.session['status'] == 'ready')
        assert texts(log)[-1] == 'held follow-up'
        receipt = await a.transport.receipt(a.selected, identity)
        assert receipt['commandId'] == identity and receipt['status'] == 'completed'
    finally:
        await a.close()


@pytest.mark.parametrize('lost_ack', ['exception', 'unknown-response'])
async def test_unknown_queue_ack_retains_original_and_reconnect_never_replays(pending_host, monkeypatch, lost_ack):
    a, _, log = await seeded(pending_host)
    try:
        await a.dispatch(request(a, 'submit', text='busy'))
        await wait_for(lambda: a.session['status'] == 'working')
        original = a.transport.command
        calls = []
        async def lost(session, action, args, identity):
            calls.append(identity)
            await original(session, action, args, identity)
            if lost_ack == 'exception':
                raise OSError('fixture loses acknowledgement after admission')
            return {'delivery': 'unknown'}
        monkeypatch.setattr(a.transport, 'command', lost)
        ok, _ = await a.dispatch(request(a, 'queue', text='admitted once'))
        assert not ok
        identity = calls[0]
        assert a.store.data['outbox'][identity]['status'] == 'unknown'
        assert a.store.data['outbox'][identity]['args']['id'] == identity
        assert not (await a.dispatch(request(a, 'queue', text='uncertain duplicate')))[0]
        generation = a.transport.generation
        await a.transport.rpc('disconnect')
        await wait_for(lambda: a.transport.online and a.transport.generation > generation)
        await wait_for(lambda: a.session['status'] == 'ready' and 'admitted once' in texts(log))
        assert len(calls) == 1
        assert texts(log).count('admitted once') == 1
        assert texts(log) == ['seed', 'busy', 'admitted once']
    finally:
        await a.close()


async def test_steering_idle_pending_then_exact_applied_receipt(pending_host):
    a, _, log = await seeded(pending_host)
    try:
        assert a.steering_supported()
        assert (await a.dispatch(request(a, 'steer', text='idle correction')))[0]
        identity = next(k for k,v in a.store.data['outbox'].items() if v['action'] == 'conversation.steer.set')
        assert a.session['steeringMessage']['id'] == identity
        assert not Path(str(log)+'.steering').exists()
        assert not (await a.dispatch(request(a, 'retry_delivery', id=identity)))[0]
        assert a.store.data['outbox'][identity]['args']['id'] == identity
        assert next(i for i in a.items() if i['id'] == 'correction:'+identity)['status'] == 'pending'
        assert (await a.dispatch(request(a, 'submit', text='busy')))[0]
        await wait_for(lambda: Path(str(log)+'.steering').exists())
        await asyncio.sleep(.06)
        assert (await a.dispatch(request(a, 'retry_delivery', id=identity)))[0]
        row = a.store.data['outbox'][identity]
        assert row['receiptLookup']['commandId'] == identity
        assert row['steeringDisposition'] == 'applied'
        assert next(i for i in a.items() if i['id'] == 'correction:'+identity)['status'] == 'applied'
        assert len(Path(str(log)+'.steering').read_text().splitlines()) == 1
        assert texts(log) == ['seed', 'busy']
    finally:
        await a.close()


async def test_steering_withdraw_and_captured_chat_refusal(pending_host):
    a, _, log = await seeded(pending_host)
    try:
        target = a.selected
        assert not (await a.dispatch(request(a, 'steer', id='another-conversation', text='wrong target')))[0]
        assert (await a.dispatch(request(a, 'steer', id=target, text='withdraw pending')))[0]
        identity = a.session['steeringMessage']['id']
        assert (await a.dispatch(request(a, 'steer_remove', id=identity)))[0]
        assert not a.session.get('steeringMessage')
        assert not (await a.dispatch(request(a, 'steer_remove', id=identity)))[0]
        assert not (await a.dispatch(request(a, 'steer', text='x'*16001)))[0]
        assert texts(log) == ['seed']
    finally:
        await a.close()


@pytest.mark.parametrize('pending_host', ['no-steer'], indirect=True)
async def test_native_capability_required_before_user_or_agent_steering(pending_host):
    a, events, _ = await seeded(pending_host)
    try:
        assert not a.steering_supported()
        assert not any(e['type'] == 'commands' and '/steer' in e.get('commands', []) for e in events)
        assert not (await a.dispatch(request(a, 'steer', text='unsupported')))[0]
        assert not a.store.data['outbox']
    finally:
        await a.close()


@pytest.mark.parametrize('text,expected', [('hold steering', 'held'), ('silent steering', 'unconfirmed')])
async def test_steering_pending_removal_does_not_prove_insertion(pending_host, text, expected):
    a, _, log = await seeded(pending_host)
    try:
        await a.dispatch(request(a, 'submit', text='busy'))
        await wait_for(lambda: a.session['status'] == 'working')
        assert (await a.dispatch(request(a, 'steer', text=text)))[0]
        identity = next(k for k,v in a.store.data['outbox'].items() if v['action'] == 'conversation.steer.set')
        await wait_for(lambda: not a.session.get('steeringMessage'))
        assert next(i for i in a.items() if i['id'] == 'correction:'+identity)['status'] == 'pending'
        if expected == 'unconfirmed':
            assert (await a.dispatch(request(a, 'stop')))[0]
            await wait_for(lambda: a.session['status'] == 'ready')
        else:
            await asyncio.sleep(.06)
        assert (await a.dispatch(request(a, 'retry_delivery', id=identity)))[0]
        assert a.store.data['outbox'][identity]['steeringDisposition'] == expected
        assert len(Path(str(log)+'.steering').read_text().splitlines()) == 1
        assert texts(log) == ['seed', 'busy']
    finally:
        await a.close()


async def test_agent_queue_uses_same_backend_after_renderer_revision_gate(pending_host):
    a, _, log = await seeded(pending_host)
    try:
        await a.dispatch(request(a, 'submit', text='busy'))
        await wait_for(lambda: a.session['status'] == 'working')
        emitted = a.emit
        def renderer(packet):
            emitted(packet)
            if packet['type'] == 'client_ui':
                a.later(a.dispatch({'op': 'client_ui_reply', 'token': packet['token'],
                    'result': {'accepted': packet['expectedRevision'] == 42, 'revision': 43}}))
        a.emit = renderer
        def tool(identity, revision):
            return {'session': a.selected, 'tool': {'toolCallId': identity,
                'toolName': 'amplifier_tui_action_terminal', 'toolInput': json.dumps({
                    'action': 'queue', 'expectedRevision': revision, 'args': {'text': 'agent follow-up'}})}}
        assert not (await a.client_tool(tool('stale-tool', 41)))['success']
        assert not a.session.get('queuedMessages')
        assert (await a.client_tool(tool('reviewed-tool', 42)))['success']
        identity = a.session['queuedMessages'][0]['id']
        # The same original tool receipt returns without a second queue dispatch.
        assert (await a.client_tool(tool('reviewed-tool', 42)))['success']
        assert a.session['queuedMessages'][0]['id'] == identity
        await wait_for(lambda: a.session['status'] == 'ready' and 'agent follow-up' in texts(log))
        assert texts(log) == ['seed', 'busy', 'agent follow-up']
    finally:
        await a.close()


async def test_shared_steering_withdraw_and_private_quote_preservation(pending_host, monkeypatch):
    a, _, log = await seeded(pending_host)
    b = None
    try:
        b, _ = await view(pending_host[1] / 'b', pending_host[0], session=a.selected)
        await a.dispatch(request(a, 'draft', text='private quoted draft'))
        monkeypatch.setattr(a.messages, 'quote', lambda: {'id': 'retained-quote'})
        assert not (await a.dispatch(request(a, 'queue', text='private quoted draft')))[0]
        assert not (await a.dispatch(request(a, 'steer', text='private quoted draft')))[0]
        assert a.store.data['drafts'][a.selected] == 'private quoted draft'
        assert a.messages.quote()['id'] == 'retained-quote'
        assert not a.store.data['outbox']
        assert (await b.dispatch(request(b, 'steer', text='shared steering')))[0]
        await wait_for(lambda: bool(a.session.get('steeringMessage')))
        identity = a.session['steeringMessage']['id']
        assert any(i['id'] == 'correction:'+identity for i in a.items())
        assert (await a.dispatch(request(a, 'steer_remove', id=identity)))[0]
        assert not a.session.get('steeringMessage')
        assert texts(log) == ['seed']
    finally:
        await a.close()
        if b:
            await b.close()


async def test_steering_receipt_requires_original_id_chat_and_typed_outcome(pending_host, monkeypatch):
    a, _, _ = await seeded(pending_host)
    try:
        assert (await a.dispatch(request(a, 'steer', text='original pending')))[0]
        identity = a.session['steeringMessage']['id']
        row = a.store.data['outbox'][identity]
        async def mismatched(session, command):
            return {'commandId': command, 'channel': 'another-chat', 'status': 'completed', 'detail': 'steering:applied:fixture'}
        monkeypatch.setattr(a.transport, 'receipt', mismatched)
        assert not (await a.dispatch(request(a, 'retry_delivery', id=identity)))[0]
        assert 'steeringDisposition' not in row
        async def untyped(session, command):
            return {'commandId': command, 'channel': row['chat'], 'status': 'completed', 'detail': 'end_turn'}
        monkeypatch.setattr(a.transport, 'receipt', untyped)
        assert (await a.dispatch(request(a, 'retry_delivery', id=identity)))[0]
        assert row['steeringDisposition'] == 'unconfirmed'
        assert row['args']['id'] == identity
    finally:
        await a.close()


@pytest.mark.parametrize('operation', ['queue_edit', 'queue_remove'])
async def test_actual_lost_mutation_echo_never_queries_unsent_uuid_or_snapshot_proof(pending_host, operation, monkeypatch):
    a, _, log = await seeded(pending_host)
    b = proxy = None
    try:
        await a.dispatch(request(a, 'submit', text='busy'))
        await wait_for(lambda: a.session['status'] == 'working')
        await a.dispatch(request(a, 'queue', text='original held input'))
        pending_id = a.session['queuedMessages'][0]['id']
        await a.dispatch(request(a, 'stop'))
        await wait_for(lambda: a.session['status'] == 'ready')
        fault = pending_host[1] / 'fault'
        fault.mkdir()
        proxy = await asyncio.create_subprocess_exec('node', str(ROOT / 'tests/fixtures/pending_fault_proxy.mjs'),
            pending_host[0], str(fault), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        async with asyncio.timeout(10):
            line = await proxy.stdout.readline()
        assert line, (await proxy.stderr.read()).decode()
        b, _ = await view(pending_host[1] / 'lost-client', json.loads(line)['url'], session=a.selected, identity='lost-client')
        kind = 'chat/pendingMessageRemoved' if operation == 'queue_remove' else 'chat/pendingMessageSet'
        (fault / 'drop.json').write_text(json.dumps({'type': kind, 'id': pending_id}))
        assert not (await b.dispatch(request(b, operation, id=pending_id, text='edited after lost echo')))[0]
        await wait_for(lambda: (fault / 'dropped.json').exists())
        echo = json.loads((fault / 'dropped.json').read_text())['params']
        assert echo['origin']['clientId'] == 'lost-client'
        assert type(echo['origin']['clientSeq']) is int
        assert echo['action']['id'] == pending_id and echo['action']['type'] == kind
        local_id, row = next(iter(b.store.data['outbox'].items()))
        assert local_id != pending_id and row['args']['id'] == pending_id and row['status'] == 'unknown'
        await wait_for(lambda: b.transport.online)
        await b.dispatch(request(b, 'queue_inspect'))
        assert row['status'] == 'unknown'  # Equal/missing snapshot cannot settle the original mutation.
        async def invalid_receipt(*args):
            pytest.fail('Local mutation UUID was never sent as an AHP command ID')
        monkeypatch.setattr(b.transport, 'receipt', invalid_receipt)
        assert not (await b.dispatch(request(b, 'retry_delivery', id=local_id)))[0]
        assert row['status'] == 'unknown'
        sent = [json.loads(line) for line in (fault / 'sent.jsonl').read_text().splitlines()]
        mutations = [r for r in sent if r.get('params', {}).get('action', {}).get('id') == pending_id]
        assert len(mutations) == 1
        assert local_id not in (fault / 'sent.jsonl').read_text()
        if operation == 'queue_edit':
            await wait_for(lambda: 'edited after lost echo' in texts(log))
            assert texts(log).count('edited after lost echo') == 1
        else:
            assert texts(log) == ['seed', 'busy']
    finally:
        await a.close()
        if b:
            await b.close()
        if proxy:
            proxy.terminate()
            await proxy.wait()
