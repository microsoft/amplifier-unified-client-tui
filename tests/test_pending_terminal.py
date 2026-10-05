"""Updated Ratatui routes in real PTYs; public Host and independent ACP fixture."""
import asyncio
import json
import os
from pathlib import Path

import pytest
from test_ahp_client import view
from test_ahp_terminal import Probe, displayed, saved_draft_state
from test_pending_client import pending_host as pending_host  # noqa: F401
from test_pending_client import texts

pytestmark = pytest.mark.skipif(not os.environ.get('TUI_CONNECTED_EXECUTABLE') or not os.environ.get('AHP_HOST_MODULE'), reason='Set independently built connected native client and sealed Host')


def terminal(host, root, *, client='terminal', session=None):
    args = [os.environ['TUI_CONNECTED_EXECUTABLE'], '--server', host, '--workspace', str(root),
            '--state-dir', str(root / client), '--client', client]
    if session:
        args += ['--session', session]
    return Probe(args, 120, 40, guard_terminal_modes=True, env={'PYTHONPATH': ''})


async def action(probe, query, title):
    probe.send(b'\x1bOS')
    await displayed([probe], lambda: 'Actions' in probe.text)
    probe.send(query.encode()+b'\r')
    if title:
        await displayed([probe], lambda: title in probe.text)


def escape(probe):
    probe.send(b'\x1b[27u')


def capture(probe, name):
    root = Path(os.environ.get('TUI_EVIDENCE_DIR', '.state/pending-terminal'))
    root.mkdir(parents=True, exist_ok=True)
    (root / (name+'.txt')).write_text(probe.text)
    (root / (name+'.ansi')).write_bytes(bytes(probe.raw))
    from terminal_raster import render_terminal
    render_terminal(probe, root / (name+'.png'), font_size=16)


async def seeded_terminal(host):
    url, root, _ = host
    probe = terminal(url, root)
    await displayed([probe], lambda: 'UNIFIED' in probe.text)
    probe.send(b'seed\r')
    await displayed([probe], lambda: 'Echo: seed' in probe.text)
    identity = json.loads((root / 'terminal/connections/terminal.json').read_text())['session']
    observer, _ = await view(root / 'observer', url, session=identity)
    return probe, observer


async def test_updated_terminal_queue_edit_cancel_hold_and_same_id_resume(pending_host):
    probe, observer = await seeded_terminal(pending_host)
    try:
        probe.send(b'busy-long\r')
        await displayed([probe], lambda: observer.session['status'] == 'working')
        probe.send(b'terminal follow-up')
        await action(probe, 'Queue current draft', None)
        await displayed([probe], lambda: bool(observer.session.get('queuedMessages')))
        identity = observer.session['queuedMessages'][0]['id']
        await displayed([probe], lambda: 'terminal follow-up' not in probe.text)
        probe.send(b'/pending\r')
        await displayed([probe], lambda: 'Shared follow-ups' in probe.text and 'Refresh shared follow-ups' in probe.text and 'terminal follow-up' in probe.text)
        assert 'Pause pending' not in probe.text and 'Run pending' not in probe.text
        capture(probe, 'shared-queue')
        probe.send(b'terminal follow-up\r')
        await displayed([probe], lambda: 'Follow-up · inspect' in probe.text)
        probe.send(b'Edit waiting\r')
        await displayed([probe], lambda: 'Edit waiting follow-up' in probe.text)
        probe.send(b' edited\r')
        await displayed([probe], lambda: observer.session['queuedMessages'][0]['message']['text'] == 'terminal follow-up edited')
        assert observer.session['queuedMessages'][0]['id'] == identity
        await displayed([probe], lambda: 'Edit waiting follow-up' not in probe.text)
        probe.send(b'\x03')
        await displayed([probe], lambda: observer.session['status'] == 'ready')
        assert observer.session['queuedMessages'][0]['message']['_meta']['amplifier.dev/queue']['held']
        assert texts(pending_host[2]) == ['seed', 'busy-long']
        probe.send(b'/pending\r')
        await displayed([probe], lambda: 'Shared follow-ups' in probe.text and 'held' in probe.text)
        probe.send(b'terminal follow-up\r')
        await displayed([probe], lambda: 'Resume this held follow-up' in probe.text)
        capture(probe, 'held-same-id-resume')
        probe.send(b'Resume this held\r')
        await displayed([probe], lambda: observer.session['status'] == 'ready' and len(texts(pending_host[2])) == 3)
        assert texts(pending_host[2])[-1] == 'terminal follow-up edited'
        assert (await observer.transport.receipt(observer.selected, identity))['commandId'] == identity
    finally:
        capture(probe, 'last-'+pending_host[1].name)
        await observer.close()
        await asyncio.to_thread(probe.close)


async def test_updated_terminal_private_steering_exact_applied_receipt(pending_host):
    probe, observer = await seeded_terminal(pending_host)
    log = pending_host[2]
    try:
        probe.send(b'/steer\r')
        await displayed([probe], lambda: 'Steer selected conversation' in probe.text)
        await displayed([probe], lambda: 'current or next turn' in ' '.join(probe.text.split()))
        probe.send(b'terminal correction')
        await displayed([probe], lambda: 'terminal correction' in probe.text)
        assert not observer.session.get('steeringMessage')
        assert not Path(str(log)+'.steering').exists()
        capture(probe, 'private-steering-before-submit')
        probe.send(b'\r')
        await displayed([probe], lambda: bool(observer.session.get('steeringMessage')))
        identity = observer.session['steeringMessage']['id']
        await displayed([probe], lambda: 'Steer selected conversation' not in probe.text)
        probe.send(b'busy-long\r')
        await displayed([probe], lambda: Path(str(log)+'.steering').exists())
        await asyncio.sleep(.06)
        probe.send(b'/deliveries\r')
        await displayed([probe], lambda: 'Check delivery status' in probe.text)
        probe.send(b'Check delivery status\r')
        state_path = pending_host[1] / 'terminal/connections/terminal.json'
        await displayed([probe], lambda: json.loads(state_path.read_text())['outbox'][identity].get('steeringDisposition') == 'applied')
        escape(probe)
        await displayed([probe], lambda: 'Correction applied' in probe.text and 'terminal correction' in probe.text and '[ Actions ]' in probe.text)
        capture(probe, 'steering-exact-applied')
        state = json.loads(state_path.read_text())['outbox'][identity]
        assert state['receiptLookup']['commandId'] == identity
        assert state['receiptLookup']['channel'] == observer.session['chat']
        assert texts(log) == ['seed', 'busy-long']
        assert len(Path(str(log)+'.steering').read_text().splitlines()) == 1
    finally:
        capture(probe, 'last-'+pending_host[1].name)
        await observer.close()
        await asyncio.to_thread(probe.close)


@pytest.mark.parametrize('text,expected', [('agent queue', 'agent follow-up'), ('agent steer', 'agent correction')])
async def test_updated_renderer_agent_pending_actions_preserve_other_view(pending_host, text, expected):
    a, observer = await seeded_terminal(pending_host)
    b = terminal(pending_host[0], pending_host[1], client='other-terminal', session=observer.selected)
    try:
        await displayed([a,b], lambda: 'Echo: seed' in b.text)
        b.send(b'Other private draft')
        await displayed([a,b], lambda: 'Other private draft' in b.text)
        await saved_draft_state(b, pending_host[1] / 'other-terminal/connections/other-terminal.json', observer.selected, 'Other private draft')
        a.send(text.encode()+b'\r')
        await displayed([a,b], lambda: 'Agent renderer admission confirmed' in a.text)
        if text == 'agent queue':
            await displayed([a,b], lambda: 'Echo: agent follow-up' in a.text)
            assert texts(pending_host[2]) == ['seed', text, expected]
        else:
            await displayed([a,b], lambda: Path(str(pending_host[2])+'.steering').exists())
            assert len(Path(str(pending_host[2])+'.steering').read_text().splitlines()) == 1
            assert texts(pending_host[2]) == ['seed', text]
        await displayed([a,b], lambda: 'Other private draft' in b.text)
        assert json.loads((pending_host[1] / 'other-terminal/connections/other-terminal.json').read_text())['drafts'][observer.selected] == 'Other private draft'
        await displayed([a,b], lambda: '[ Actions ]' in a.text and 'Other private draft' in b.text)
        capture(a, text.replace(' ', '-')+'-actual-renderer')
    finally:
        await observer.close()
        await asyncio.gather(asyncio.to_thread(a.close), asyncio.to_thread(b.close))
