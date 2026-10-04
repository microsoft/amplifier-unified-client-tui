"""Actual Ratatui PTYs talking to the independent AHP CLI; ACP model is a fixture."""
import asyncio
import os
import sys
from pathlib import Path

import pytest
from test_ahp_client import ahp_host as ahp_host  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from terminal_probe import Probe  # noqa: E402

pytestmark = pytest.mark.skipif(not os.environ.get('AHP_HOST_ENTRY') or os.environ.get('TUI_TEST_CANDIDATES') != '1', reason='Build real host and native client')


async def displayed(probes, predicate, timeout=12):
    async with asyncio.timeout(timeout):
        while True:
            for probe in probes:
                probe.read(0)
                assert probe.process.poll() is None, probe.text
            if predicate():
                return
            await asyncio.sleep(.01)


async def saved_draft_state(probe, path, session, text, timeout=12):
    """Renderer text is local; require the exact retained draft in its scope."""
    import json
    state = None
    observations = 0
    first_match = None
    started = asyncio.get_running_loop().time()

    def retained():
        nonlocal state, observations, first_match
        state = json.loads(path.read_text())
        matched = state['drafts'].get(session) == text
        observations += 1
        if first_match is None:
            first_match = matched
        return matched

    await displayed([probe], retained, timeout=timeout)
    assert probe.process.poll() is None, probe.text
    evidence = Path(os.environ.get('TUI_EVIDENCE_DIR', path.parent))
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / 'draft-persistence-observer.txt').write_text(json.dumps({
        'initialExactDraftPresent': first_match, 'observations': observations,
        'elapsedMilliseconds': round((asyncio.get_running_loop().time() - started) * 1000, 2),
        'exactSessionAndTextMatched': True, 'matchedWhileClientLive': True}))
    return state


@pytest.mark.parametrize('size', [(120, 40), (40, 20)])
async def test_real_terminal_stream_approval_private_draft_and_exit(ahp_host, size):
    url, root, log = ahp_host
    executable = os.environ.get('TUI_CONNECTED_EXECUTABLE')
    launcher = [executable] if executable else [sys.executable, '-m', 'amplifier_tui.connected']
    probe = Probe([*launcher, '--server', url, '--workspace', str(root), '--state-dir', str(root / 'client'), '--client', 'terminal'],
                  *size, guard_terminal_modes=True, env={'PYTHONPATH': ''} if executable else None)
    try:
        await displayed([probe], lambda: 'UNIFIED' in probe.text)
        probe.send(b'hello terminal\r')
        await displayed([probe], lambda: 'Echo: hello terminal' in probe.text)
        probe.send(b'approval\r')
        await displayed([probe], lambda: 'Review decision' in probe.text)
        probe.send(b'\x1bOS')
        await displayed([probe], lambda: 'Actions' in probe.text)
        probe.send(b'Decisions\r')
        await displayed([probe], lambda: 'Allow once [allow]' in probe.text)
        probe.send(b'\r')
        await displayed([probe], lambda: 'Echo: approval' in probe.text)
        probe.send(b'Private retained draft')
        await displayed([probe], lambda: 'Private retained draft' in probe.text)
        await asyncio.sleep(.3)
        evidence = Path(os.environ.get('TUI_EVIDENCE_DIR', root))
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / f'ahp-terminal-{size[0]}.txt').write_text(probe.text)
        (evidence / f'ahp-terminal-{size[0]}.ansi').write_bytes(bytes(probe.raw))
        try:
            from terminal_raster import render_terminal
            render_terminal(probe, evidence / f'ahp-terminal-{size[0]}.png', font_size=16)
        except RuntimeError:
            menlo = Path('/System/Library/Fonts/Menlo.ttc')
            if menlo.is_file():
                import terminal_raster
                from PIL import ImageFont
                terminal_raster.reference_fonts = lambda size: {(bold, italic): ImageFont.truetype(str(menlo), size, index=index) for bold, italic, index in [(False, False, 0), (True, False, 1), (False, True, 2), (True, True, 3)]}
                terminal_raster.render_terminal(probe, evidence / f'ahp-terminal-{size[0]}.png', font_size=16)
    finally:
        await asyncio.to_thread(probe.close)
    assert len(log.read_text().splitlines()) == 2
    import json
    state = json.loads((root / 'client/connections/terminal.json').read_text())
    assert 'Private retained draft' in state['drafts'].values()


@pytest.mark.skipif(not os.environ.get('AHP_HOST_MODULE'), reason='Public host API composition fixture')
async def test_agent_client_tool_reaches_actual_renderer_and_preserves_other_view(ahp_host):
    url, root, log = ahp_host
    launcher = [os.environ['TUI_CONNECTED_EXECUTABLE']] if os.environ.get('TUI_CONNECTED_EXECUTABLE') else [sys.executable, '-m', 'amplifier_tui.connected']
    a = Probe([*launcher, '--server', url, '--workspace', str(root), '--state-dir', str(root / 'a'), '--client', 'terminal'], 120, 40, guard_terminal_modes=True, env={'PYTHONPATH': ''} if os.environ.get('TUI_CONNECTED_EXECUTABLE') else None)
    b = None
    try:
        await displayed([a], lambda: 'UNIFIED' in a.text)
        a.send(b'first\r')
        await displayed([a], lambda: 'Echo: first' in a.text)
        import json
        identity = json.loads((root / 'a/connections/terminal.json').read_text())['session']
        b = Probe([*launcher, '--server', url, '--workspace', str(root), '--state-dir', str(root / 'b'), '--client', 'other-terminal', '--session', identity], 120, 40, guard_terminal_modes=True, env={'PYTHONPATH': ''} if os.environ.get('TUI_CONNECTED_EXECUTABLE') else None)
        await displayed([a, b], lambda: 'Echo: first' in b.text)
        b.send(b'Other private draft')
        await displayed([a, b], lambda: 'Other private draft' in b.text)
        a.send(b'client-ui\r')
        await displayed([a, b], lambda: 'Agent prepared draft' in a.text and 'Targeted renderer changed' in a.text and 'Other private draft' in b.text)
        assert 'Other private draft' in b.text
        assert 'Agent prepared draft' not in b.text
        assert len(log.read_text().splitlines()) == 2
    finally:
        await asyncio.gather(*(asyncio.to_thread(p.close) for p in (a, b) if p))


async def test_actual_terminal_long_stream_remains_responsive_and_exact(ahp_host):
    url, root, log = ahp_host
    executable = os.environ.get('TUI_CONNECTED_EXECUTABLE')
    launcher = [executable] if executable else [sys.executable, '-m', 'amplifier_tui.connected']
    probe = Probe([*launcher, '--server', url, '--workspace', str(root), '--state-dir', str(root / 'stream'), '--client', 'stream'], 120, 40, guard_terminal_modes=True, env={'PYTHONPATH': ''} if executable else None)
    try:
        await displayed([probe], lambda: 'UNIFIED' in probe.text)
        probe.send(b'long-stream\r')
        await displayed([probe], lambda: 'LONG-STREAM-COMPLETE' in probe.text, timeout=25)
        probe.send(b'Responsive local draft')
        await displayed([probe], lambda: 'Responsive local draft' in probe.text)
        await asyncio.sleep(.3)
        evidence = Path(os.environ.get('TUI_EVIDENCE_DIR', root))
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / 'long-stream-terminal.txt').write_text(probe.text)
        assert len(log.read_text().splitlines()) == 1
    finally:
        await asyncio.to_thread(probe.close)


async def test_actual_terminal_standard_model_picker_keeps_private_draft(ahp_host):
    import uuid

    from amplifier_tui.unified_transport import Transport
    url, root, prompt_log = ahp_host
    transport = Transport(url, '', 'model-fixture-setup')
    await transport.open()
    identity = 'ahp-session:/' + str(uuid.uuid4())
    await transport.rpc('create', session=identity, cwd=root.as_uri(), provider='fixture')
    await transport.close()
    executable = os.environ.get('TUI_CONNECTED_EXECUTABLE')
    launcher = [executable] if executable else [sys.executable, '-m', 'amplifier_tui.connected']
    probe = Probe([*launcher, '--server', url, '--workspace', str(root), '--state-dir', str(root / 'model-terminal'),
                   '--client', 'model-picker', '--session', identity], 120, 40, guard_terminal_modes=True,
                  env={'PYTHONPATH': ''} if executable else None)
    try:
        await displayed([probe], lambda: 'UNIFIED' in probe.text)
        probe.send(b'/settings\r')
        await displayed([probe], lambda: 'Model and conversation settings' in probe.text and 'OpenAI / gpt-6-sol' in probe.text)
        probe.send(b'\r')
        await displayed([probe], lambda: 'Choose Model' in probe.text and 'gpt-6-astra' in probe.text)
        probe.send(b'gpt-6-astra\r')
        await displayed([probe], lambda: 'Model and conversation settings' in probe.text and 'OpenAI / gpt-6-astra' in probe.text)
        probe.send(b'\x1b[27u')
        await displayed([probe], lambda: 'Model and conversation settings' not in probe.text)
        probe.send(b'/settings\r')
        await displayed([probe], lambda: 'Model and conversation settings' in probe.text)
        probe.send(b'\r')
        await displayed([probe], lambda: 'Choose Model' in probe.text)
        probe.send(b'Fixture model 2\r')
        await displayed([probe], lambda: 'declined the setting change' in probe.text)
        assert 'RPC' not in probe.text and 'needs-confirmation' not in probe.text
        probe.send(b'\x1b[27u')
        await displayed([probe], lambda: 'Model and conversation settings' not in probe.text)
        probe.send(b'Private unsent draft after model change')
        await displayed([probe], lambda: 'Private unsent draft after model change' in probe.text)
        state = await saved_draft_state(probe,
            root / 'model-terminal/connections/model-picker.json', identity,
            'Private unsent draft after model change')
        assert state['drafts'][identity] == 'Private unsent draft after model change'
        assert [row['status'] for row in state['configEffects'].values()] == ['confirmed', 'refused']
        assert len((root / 'settings.jsonl').read_text().splitlines()) == 2
        assert not prompt_log.exists()
        evidence = Path(os.environ.get('TUI_EVIDENCE_DIR', root))
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / 'model-picker-terminal.txt').write_text(probe.text)
        (evidence / 'model-picker-terminal.ansi').write_bytes(bytes(probe.raw))
    finally:
        await asyncio.to_thread(probe.close)
