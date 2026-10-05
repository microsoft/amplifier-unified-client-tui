"""Public AHP history projection; no runtime, provider or host effects."""
import copy
import json
import os
import sys
from pathlib import Path

import pytest

from amplifier_tui.unified_transport import Transport, _turn_items


def notification(text='  Keep this exact wording — café\nsecond line  ', identity='steer-1'):
    return {'kind': 'systemNotification', 'content': 'Steering input: ' + text,
            '_meta': {'amplifier.dev/history': {
                'inputOrigin': 'steering', 'activeInputId': 'turn-1',
                'messageId': 'row-' + identity,
                'nativeInput': {'version': 1, 'kind': 'steer', 'id': identity},
                'message': {'text': text, 'origin': {'kind': 'user'},
                            'attachments': [{'type': 'resource', 'label': 'document.pdf',
                                             'resource': 'amplifier-attachment://original/body'}]}}}}


def turn():
    return {'id': 'turn-1', 'state': 'complete',
            'message': {'text': 'Original question', 'origin': {'kind': 'user'}},
            'responseParts': [
                {'id': 'before', 'kind': 'markdown', 'content': 'Before steering'},
                {'id': 'tool', 'kind': 'toolCall', 'toolCall': {
                    'toolCallId': 'call-1', 'toolName': 'Read document',
                    'status': 'completed', 'success': True}},
                notification(), notification('A distinct correction', 'steer-2'),
                {'kind': 'error', 'error': {'message': 'Original unknown result'}},
                {'id': 'after', 'kind': 'markdown', 'content': 'After steering'}]}


def test_history_notices_preserve_order_originals_and_do_not_become_inputs():
    value = turn()
    original = copy.deepcopy(value)
    rows = _turn_items(value)
    assert [row['id'] for row in rows] == [
        'input:turn-1', 'turn-1:before', 'tool:turn-1:call-1',
        'turn-1:2', 'turn-1:3', 'turn-1:4', 'turn-1:after']
    assert len(set(row['id'] for row in rows)) == len(rows)
    assert rows[3]['text'] == 'You · Steering\n  Keep this exact wording — café\nsecond line  \nAttachment · document.pdf'
    assert rows[4]['text'] == 'You · Steering\nA distinct correction\nAttachment · document.pdf'
    for row, part in zip(rows[3:5], value['responseParts'][2:4]):
        assert row['kind'] == 'notice' and row['status'] == ''
        assert json.loads(row['detail']) == part
        assert 'reference' not in row and 'inputId' not in row
    assert value == original and _turn_items(value) == rows
    client = Transport('ws://localhost/ahp', None, 'observer')
    client.sessions_state['ahp-session:/fixture'] = {'defaultChat': 'ahp-chat:/fixture'}
    client.chat_state['ahp-chat:/fixture'] = {
        'turns': {'turn-1': value}, 'order': ['turn-1'], 'items': {'turn-1': rows}}
    session = client._snapshot('ahp-session:/fixture')['session']
    assert [row['text'] for row in session['messages']] == [
        'Original question', 'Before steering', 'After steering']
    assert [row['inputId'] for row in session['messages'] if 'inputId' in row] == ['turn-1']
    assert session['displayItems'] == rows


@pytest.mark.parametrize('metadata', [None, [], {}, {'amplifier.dev/history': []},
    {'amplifier.dev/history': {'inputOrigin': 'steering', 'message': 'invalid'}}])
def test_unknown_metadata_preserves_standard_notice_without_english_inference(metadata):
    part = {'kind': 'systemNotification', 'content': 'Steering input: this is a system notice', '_meta': metadata}
    row = _turn_items({'id': 'turn', 'responseParts': [part]})[0]
    assert row['kind'] == 'notice' and row['status'] == ''
    assert row['text'] == 'System\nSteering input: this is a system notice'
    assert json.loads(row['detail']) == part


@pytest.mark.parametrize('field,bad', [('inputOrigin', 'user'), ('activeInputId', 'other-turn'),
    ('nativeInput', {'version': 1, 'kind': 'user', 'id': 'other'}),
    ('nativeInput', {'version': 1, 'kind': 'steer', 'id': ''}),
    ('message', {'origin': {'kind': 'agent'}, 'text': 'not user'}),
    ('message', {'origin': {'kind': 'user'}, 'text': ['not text']}),
    ('message', {'origin': {'kind': 'user'}, 'text': 'text', 'attachments': 'not a list'})])
def test_malformed_or_wrong_turn_attribution_falls_back_without_losing_content(field, bad):
    part = notification()
    part['_meta']['amplifier.dev/history'][field] = bad
    row = _turn_items({'id': 'turn-1', 'responseParts': [part]})[0]
    assert row['text'] == 'System\n' + part['content']
    assert json.loads(row['detail']) == part


def test_attachment_only_steering_and_unfamiliar_standard_notice_keep_evidence():
    part = notification('')
    row = _turn_items({'id': 'turn-1', 'responseParts': [part]})[0]
    assert row['text'] == 'You · Steering\nAttachment · document.pdf'
    # The original standard notice remains retained even if it uses unfamiliar wording.
    part['content'] = 'A separately localized system description'
    row = _turn_items({'id': 'turn-1', 'responseParts': [part]})[0]
    assert json.loads(row['detail'])['content'] == part['content']
    generic = {'kind': 'systemNotification', 'content': 'Review paused\nWait for confirmation'}
    assert _turn_items({'id': 'turn', 'responseParts': [generic]})[0]['text'] == 'System\n' + generic['content']


@pytest.mark.skipif(not os.environ.get('TUI_NOTIFICATION_NATIVE'), reason='Set an independently built native renderer')
@pytest.mark.parametrize('width', [80, 40])
def test_native_pty_history_notices_keep_attribution_order_and_private_draft(tmp_path, width):
    """Real renderer, controlled public-state projection; not a live-host acceptance."""
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'scripts'))
    from terminal_probe import Probe
    from terminal_raster import render_terminal

    value = turn()
    value['responseParts'][2] = notification('Keep the original steering', 'steer-1')
    value['responseParts'].insert(5, {'kind': 'systemNotification', 'content': 'A generic system notice'})
    scene = tmp_path / 'history.json'
    scene.write_text(json.dumps({'title': 'Controlled history presentation', 'draft': 'Private unsent draft',
                                 'items': _turn_items(value), 'system': []}))
    saved = scene.read_bytes()
    evidence = Path(os.environ.get('TUI_EVIDENCE_DIR', tmp_path / 'evidence'))
    evidence.mkdir(parents=True, exist_ok=True)
    # Reopening the same retained projection must not create a turn or submit it.
    for opening in range(2):
        probe = Probe([os.environ['TUI_NOTIFICATION_NATIVE'], '--host-json', json.dumps([
            sys.executable, '-B', '-m', 'amplifier_tui.frontend_bridge', '--scene', str(scene)])],
            cols=width, rows=50, cwd=root, env={'PYTHONPATH': str(root / 'src'), 'PYTHONDONTWRITEBYTECODE': '1'})
        try:
            probe.wait('After steering')
            probe.wait('Private unsent draft')
            text = probe.text
            expected = ['Original question', 'Before steering', 'Read document', 'You · Steering',
                        'Keep the original steering', 'document.pdf', 'A distinct correction',
                        'Original unknown result', 'System', 'A generic system notice', 'After steering']
            at = 0
            for content in expected:
                at = text.index(content, at) + len(content)
            assert text.count('You · Steering') == 2
            assert 'Resource · systemNotification' not in text
            assert 'Correction applied' not in text and 'Correction unconfirmed' not in text
            (evidence / f'notification-{width}-{opening}.txt').write_text(text)
            (evidence / f'notification-{width}-{opening}.ansi').write_bytes(bytes(probe.raw))
            render_terminal(probe, evidence / f'notification-{width}-{opening}.png', font_size=14)
        finally:
            probe.close()
        assert scene.read_bytes() == saved
