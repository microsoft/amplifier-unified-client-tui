"""Canonical private intent and exact shared-message effects; no native store access."""
import asyncio
from copy import deepcopy

import pytest

from amplifier_tui.client_state import ClientState
from amplifier_tui.unified_client import UnifiedBridge
from amplifier_tui.unified_messages import reaction_row, reference
from amplifier_tui.unified_transport import Rejected, _turn_items

LOCATOR = {'sessionId': 'native-a', 'messageId': 'native:message', 'position': 2,
           'historyEpoch': None, 'sourceDigest': 'a' * 64}
MARKER = {'version': 1, 'quoteMeta': 'amplifier.dev/messageReply', 'privateReplySelection': True, 'maxQuoteChars': 4000}


class Transport:
    def __init__(self):
        self.calls = []
        self.failure = None
        self.gate = None
        self.revision = 1
        self.mine = []
        self.receipts = {}
        self.attached = {}

    def supports(self, name):
        return name in {'message.read', 'message.reaction', 'message.receipt'}

    def row(self):
        return {'sessionId': 'native-a', 'messageId': 'native:message', 'revision': self.revision,
                'reactions': self.mine, 'mine': self.mine, 'counts': {emoji: 1 for emoji in self.mine}}

    async def capability(self, name, args, channel, *, command_id=None):
        self.calls.append((name, deepcopy(args), channel, command_id))
        if self.gate:
            await self.gate.wait()
        if name == 'message.read':
            return {'coverage': 'selected', 'sent': False, 'items': [self.row()]}
        if name == 'message.receipt':
            return {'replayed': False, 'receipt': self.receipts.get(args['commandId'])}
        self.mine = [args['emoji']] if args['present'] else []
        self.revision += 1
        result = {**self.row(), 'commandId': command_id, 'changed': True, 'sent': False}
        self.receipts[command_id] = result
        if self.failure:
            raise self.failure
        return result


def setup(tmp_path):
    transport = Transport()
    events = []
    store = ClientState(tmp_path, 'ws://localhost/ahp', 'messages')
    bridge = UnifiedBridge(events.append, transport, store, session='ahp-session:/a')
    bridge.online = True
    bridge.session = {'id': bridge.selected, 'messages': [
        {'id': 'display-1', 'role': 'assistant', 'text': 'Original saved source', 'messageReference': LOCATOR}],
        'agentCapabilities': {'_meta': {'amplifier.dev/native': {'messageInteractions': MARKER}}}}
    store.draft(bridge.selected, 'Private unsent text')
    return bridge, transport, events


def test_private_quote_and_clear_have_no_transport_and_survive_reload(tmp_path):
    bridge, transport, events = setup(tmp_path)
    bridge.messages.select_quote('display-1')
    quote = bridge.messages.quote()
    assert quote['reference'] == {k: v for k, v in LOCATOR.items() if k != 'sessionId'}
    assert bridge.store.data['drafts'][bridge.selected] == 'Private unsent text'
    assert transport.calls == []
    bridge.store.close()
    resumed = ClientState(tmp_path, 'ws://localhost/ahp', 'messages')
    bridge.store = resumed
    assert bridge.messages.quote() == quote
    bridge.selected = 'ahp-session:/b'
    assert bridge.messages.quote() is None
    bridge.selected = 'ahp-session:/a'
    bridge.messages.clear_quote('different-id')
    assert bridge.messages.quote() == quote
    bridge.messages.clear_quote(quote['id'])
    assert bridge.messages.quote() is None and not transport.calls
    assert events[-1]['quote'] is None
    resumed.close()


@pytest.mark.parametrize('bad', [None, {**LOCATOR, 'messageId': 'archive:old'}, {**LOCATOR, 'position': True}, {**LOCATOR, 'sourceDigest': 'invalid'}])
def test_missing_or_historical_refs_refuse_without_touching_draft(tmp_path, bad):
    bridge, transport, _ = setup(tmp_path)
    bridge.session['messages'][0]['messageReference'] = bad
    with pytest.raises(ValueError, match='saved quote reference'):
        bridge.messages.select_quote('display-1')
    assert not transport.calls and bridge.store.data['drafts'][bridge.selected] == 'Private unsent text'
    bridge.store.close()


async def test_original_unknown_reaction_survives_reload_current_counts_cannot_settle(tmp_path):
    bridge, transport, events = setup(tmp_path)
    transport.failure = OSError('Lost original response after apply')
    ok, message = await bridge.messages.react('display-1', '👍', True)
    assert not ok and 'not confirmed' in message
    command, effect = next(iter(bridge.store.data['messageEffects'].items()))
    assert effect['status'] == 'unknown' and transport.calls[0][3] == command
    bridge.store.close()
    bridge.store = ClientState(tmp_path, 'ws://localhost/ahp', 'messages')
    transport.failure = None
    transport.mine, transport.revision = ['✅'], 5
    await bridge.messages.read('display-1')
    assert bridge.store.data['messageEffects'][command]['status'] == 'unknown'
    assert events[-1]['pending']['id'] == command
    with pytest.raises(ValueError, match='original reaction'):
        await bridge.messages.react('display-1', '👎', True)
    assert await bridge.messages.recover(command) == (True, 'Original reaction confirmed. Inspect shared reactions for current counts.')
    assert bridge.messages.rows[(bridge.selected, LOCATOR['messageId'])]['mine'] == ['✅']
    assert [call[0] for call in transport.calls] == ['message.reaction', 'message.read', 'message.receipt']
    assert transport.calls[-1][1] == {'commandId': command}
    assert bridge.store.data['drafts'][bridge.selected] == 'Private unsent text'
    bridge.store.close()


async def test_typed_noeffect_refusal_and_unproven_refusal_stay_distinct(tmp_path):
    bridge, transport, _ = setup(tmp_path)
    transport.failure = Rejected(422, {'error': 'No authority', 'executed': False})
    assert not (await bridge.messages.react('display-1', '👍', True))[0]
    assert next(iter(bridge.store.data['messageEffects'].values()))['status'] == 'refused'
    transport.failure = Rejected(422, {'error': 'Unknown effect'})
    assert not (await bridge.messages.react('display-1', '👎', True))[0]
    assert list(bridge.store.data['messageEffects'].values())[-1]['status'] == 'unknown'
    bridge.store.close()


async def test_late_read_does_not_show_metadata_on_new_selected_chat(tmp_path):
    bridge, transport, events = setup(tmp_path)
    transport.gate = asyncio.Event()
    reading = asyncio.create_task(bridge.messages.read('display-1'))
    await asyncio.sleep(0)
    bridge.selected = 'ahp-session:/b'
    bridge.session = {'id': bridge.selected, 'messages': []}
    before = len(events)
    transport.gate.set()
    await reading
    assert len(events) == before
    assert bridge.messages.rows[('ahp-session:/a', LOCATOR['messageId'])]['revision'] == 1
    bridge.store.close()


def test_canonical_input_and_assistant_projection_preserve_refs_and_frozen_quote():
    meta = {'amplifier.dev/history': {'messageReference': LOCATOR, 'replyTo': {'excerpt': 'Frozen source'}}}
    turn = {'id': 'turn', 'state': 'completed', 'message': {'text': 'Question', '_meta': meta},
            'responseParts': [{'id': 'part', 'kind': 'markdown', 'content': 'Answer', '_meta': meta}]}
    rows = _turn_items(turn)
    assert rows[0]['text'] == 'Quoted Amplifier · Frozen source'
    assert rows[1]['reference'] == rows[2]['reference'] == LOCATOR
    assert rows[1]['replyTo']['excerpt'] == 'Frozen source'
    assert rows[2]['kind'] == 'assistant'
    assert reference(LOCATOR, reaction=True) == LOCATOR
    bad = {'sessionId': 'native-a', 'messageId': 'native:message', 'revision': 1,
           'reactions': ['👍'], 'mine': [], 'counts': {'👍': True}}
    with pytest.raises(ValueError):
        reaction_row(bad)


@pytest.mark.parametrize('authorized', [True, False])
async def test_agent_quote_uses_renderer_guard_and_same_private_action(tmp_path, authorized):
    import json
    bridge, transport, events = setup(tmp_path)
    task = asyncio.create_task(bridge.client_tool({'session': bridge.selected, 'tool': {
        'toolCallId': 'agent-quote', 'toolName': 'amplifier_tui_action_fixture',
        'toolInput': json.dumps({'action': 'message.reply', 'expectedRevision': 7, 'args': {'message_id': 'display-1'}})}}))
    await asyncio.sleep(0)
    guard = next(event for event in events if event['type'] == 'client_ui')
    assert guard['expectedRevision'] == 7 and guard['operation'] == 'message.reply'
    bridge.ui_requests[guard['token']].set_result({'accepted': authorized, 'error': 'Client changed'})
    result = await task
    assert result['success'] is authorized
    assert bool(bridge.messages.quote()) is authorized
    assert not transport.calls and bridge.store.data['drafts'][bridge.selected] == 'Private unsent text'
    bridge.store.close()


def test_malformed_private_evidence_and_capabilities_preserve_storage(tmp_path):
    bridge, transport, _ = setup(tmp_path)
    bridge.session['agentCapabilities'] = {'_meta': None}
    assert not bridge.messages.quote_supported()
    bridge.store.data['messageEffects'] = {'original': {'args': None}}
    with pytest.raises(ValueError, match='preserved'):
        bridge.messages.effects()
    assert bridge.store.data['messageEffects'] == {'original': {'args': None}}
    assert not transport.calls
    bridge.store.close()


def test_view_reset_republishes_private_quote_after_snapshot(tmp_path):
    bridge, transport, events = setup(tmp_path)
    transport.url, transport.optional_unavailable = 'ws://localhost/ahp', {}
    bridge.messages.select_quote('display-1')
    quote = bridge.messages.quote()
    events.clear()
    bridge.initial()
    snapshot = next(i for i, row in enumerate(events) if row['type'] == 'snapshot')
    controls = next(i for i, row in enumerate(events) if row['type'] == 'message_controls')
    assert controls > snapshot and events[controls]['quote'] == quote
    bridge.store.close()


async def test_original_quoted_submission_survives_admission_unknown_and_newer_private_intent(tmp_path):
    bridge, transport, events = setup(tmp_path)
    bridge.actions = {'conversation.send'}
    bridge.messages.select_quote('display-1')
    quote = bridge.messages.quote()
    async def command(scope, action, args, identity):
        saved = bridge.messages.submissions()[identity]
        assert saved['quote'] == quote and saved['args']['text'] == 'Private unsent text'
        assert bridge.store.path.read_text().find(identity) >= 0
        transport.calls.append((action, identity))
        return {'delivery': 'unknown'}
    transport.command = command
    request = {'op': 'submit', 'session_id': bridge.selected, 'request_id': 'local-send', 'text': 'Private unsent text'}
    assert not (await bridge.dispatch(request))[0]
    identity, frozen = next(iter(bridge.messages.submissions().items()))
    assert frozen['quote'] == quote and frozen['execution'] == 'unverified'
    snapshot = {'protocolVersion': 1, 'hostInstanceId': 'fixture', 'revision': 1,
                'session': {**bridge.session, 'messages': [*bridge.session['messages'],
                    {'id': 'input:'+identity, 'inputId': identity, 'role': 'user', 'text': frozen['args']['text'], 'delivery': {'status': 'accepted'}}]}}
    bridge.reconcile(snapshot)
    assert not bridge.store.data['outbox'] and frozen['admission'] == 'accepted'
    bridge.store.draft(bridge.selected, 'Newer private text')
    bridge.messages.select_quote('display-1')
    newer = bridge.messages.quote()
    calls = deepcopy(transport.calls)
    bridge.online = False
    assert (await bridge.dispatch({'op': 'message.submissionInspect', 'session_id': bridge.selected, 'request_id': 'inspect', 'id': identity}))[0]
    assert transport.calls == calls and bridge.store.data['drafts'][bridge.selected] == 'Newer private text'
    assert bridge.messages.quote() == newer and frozen['quote'] == quote
    bridge.store.close()
    bridge.store = ClientState(tmp_path, 'ws://localhost/ahp', 'messages')
    assert bridge.messages.submissions()[identity]['quote'] == quote
    assert bridge.messages.submissions()[identity]['args']['text'] == 'Private unsent text'
    bridge.store.close()


def test_selected_watch_is_monotonic_and_never_settles_unknown_intent(tmp_path):
    bridge, transport, events = setup(tmp_path)
    scope = bridge.selected
    unknown = {'session': scope, 'operation': 'message.reaction', 'status': 'unknown',
               'args': {'reference': LOCATOR, 'emoji': '👍', 'present': True}}
    bridge.store.data['messageEffects'] = {'original': deepcopy(unknown)}
    def update(revision, message_revision, mine, target=scope):
        return {'scope': target, 'record': {'topic': 'message-metadata', 'scope': target,
                'revision': revision, 'data': {'available': True, 'changedMessage': {
                **transport.row(), 'revision': message_revision, 'reactions': mine,
                'mine': mine, 'counts': {emoji: 1 for emoji in mine}}}}}
    bridge.messages.accept(update(5, 3, ['✅']))
    assert bridge.messages.rows[(scope, LOCATOR['messageId'])]['mine'] == ['✅']
    bridge.messages.accept(update(4, 2, ['👍']))
    bridge.messages.accept(update(6, 1, ['👍']))
    assert bridge.messages.rows[(scope, LOCATOR['messageId'])]['mine'] == ['✅']
    transport.generation = 1
    bridge.messages.accept(update(0, 4, ['🎉']))
    assert bridge.messages.rows[(scope, LOCATOR['messageId'])]['mine'] == ['🎉']
    before = len(events)
    bridge.messages.accept(update(10, 100, ['👍'], 'ahp-session:/other'))
    assert len(events) == before
    assert bridge.store.data['messageEffects']['original'] == unknown and not transport.calls
    shown = bridge.messages.decorate([{'id': 'source', 'reference': LOCATOR, 'kind': 'assistant', 'text': 'saved'}])
    assert any('not confirmed' in row['text'] for row in shown)
    bridge.store.data['messageEffects']['original']['status'] = 'confirmed'
    shown = bridge.messages.decorate([{'id': 'source', 'reference': LOCATOR, 'kind': 'assistant', 'text': 'saved'}])
    assert not any('not confirmed' in row['text'] for row in shown)
    bridge.store.close()

@pytest.mark.parametrize('control', ['commit', 'cancel', 'replaced', 'reconnect'])
def test_initial_watch_waits_for_matching_selection_commit(tmp_path, control):
    bridge, transport, events = setup(tmp_path)
    target = 'ahp-session:/return'
    token = bridge.messages.begin_selection(target)
    def packet(revision, emoji):
        return {'scope': target, 'record': {'topic': 'message-metadata', 'scope': target,
            'revision': revision, 'data': {'changedMessage': {**transport.row(),
                'revision': revision, 'reactions': [emoji], 'mine': [emoji], 'counts': {emoji: 1}}}}}
    before = len(events)
    bridge.messages.accept(packet(2, '👍'))
    bridge.messages.accept(packet(3, '✅'))
    bridge.messages.accept(packet(1, '🎉'))
    assert len(events) == before and not bridge.messages.rows
    if control == 'replaced':
        bridge.messages.begin_selection('ahp-session:/newer')
    if control == 'reconnect':
        transport.generation = 1
    bridge.selected = target
    bridge.messages.finish_selection(token, committed=control != 'cancel')
    if control == 'commit':
        assert bridge.messages.rows[(target, LOCATOR['messageId'])]['mine'] == ['✅']
    else:
        assert not bridge.messages.rows and len(events) == before
    assert not transport.calls
    bridge.store.close()


async def test_cancelled_selection_discards_initial_record_and_forces_new_handshake(tmp_path):
    bridge, transport, _ = setup(tmp_path)
    gate = asyncio.Event()
    async def resolve(identity, **kwargs):
        return identity
    async def snapshot(identity):
        await gate.wait()
    transport.resolve_session, transport.snapshot = resolve, snapshot
    task = asyncio.create_task(bridge.select('ahp-session:/cancelled'))
    await asyncio.sleep(0)
    assert bridge.messages.selection_pending
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert bridge.messages.selection_pending is None and transport.selected is None
    assert bridge.selected == 'ahp-session:/a'
    bridge.store.close()


async def test_rapid_selection_commits_in_order_and_never_shows_pending_scope(tmp_path):
    bridge, transport, events = setup(tmp_path)
    gate = asyncio.Event()
    entered = []
    async def resolve(identity, **kwargs):
        return identity
    async def snapshot(identity):
        entered.append(identity)
        if identity == 'ahp-session:/first':
            await gate.wait()
        return {'protocolVersion': 1, 'hostInstanceId': 'fixture', 'revision': len(entered),
                'session': {'id': identity, 'messages': []}}
    async def watch(*args):
        await asyncio.Event().wait()
    transport.resolve_session, transport.snapshot = resolve, snapshot
    bridge.watch = watch
    transport.url, transport.optional_unavailable = 'ws://localhost/ahp', {}
    first = asyncio.create_task(bridge.select('ahp-session:/first'))
    await asyncio.sleep(0)
    last = asyncio.create_task(bridge.select('ahp-session:/last'))
    await asyncio.sleep(0)
    assert entered == ['ahp-session:/first'] and bridge.selected == 'ahp-session:/a'
    gate.set()
    await asyncio.gather(first, last)
    assert entered == ['ahp-session:/first', 'ahp-session:/last']
    assert bridge.selected == bridge.session['id'] == 'ahp-session:/last'
    assert bridge.messages.selection_pending is None
    bridge.pump.cancel()
    await asyncio.gather(bridge.pump, return_exceptions=True)
    bridge.store.close()
