"""Current public host/native peers; isolated state and explicit fixture boundaries."""
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from test_ahp_client import request, wait_for
from test_ahp_terminal import Probe, displayed

from amplifier_tui.client_state import ClientState
from amplifier_tui.unified_client import UnifiedBridge
from amplifier_tui.unified_transport import Transport

ROOT = Path(__file__).resolve().parents[1]
NATIVE = os.environ.get('TUI_NATIVE_PYTHON')
PROVIDER = os.environ.get('TUI_NATIVE_PROVIDER')
CATALOG = os.environ.get('TUI_CATALOG_PYTHON')
PEERS = all((NATIVE, PROVIDER, CATALOG, os.environ.get('AHP_HOST_MODULE')))


def test_launch_flags_refuse_incomplete_or_resumed_overrides():
    for arguments in [['--provider', 'fixture'], ['--model', 'chosen'],
                      ['--bundle', 'approved'], ['--managed', '--session', 'ahp-session:/original']]:
        result = subprocess.run([sys.executable, '-m', 'amplifier_tui', *arguments], capture_output=True, text=True)
        assert result.returncode == 2
        assert 'error:' in result.stderr


@pytest_asyncio.fixture
async def native_host(tmp_path):
    if not PEERS:
        pytest.skip('Set installed TUI_NATIVE_PYTHON/PROVIDER/CATALOG_PYTHON and AHP_HOST_MODULE')
    home, workspace = tmp_path / 'home', tmp_path / 'workspace'
    home.mkdir()
    workspace.mkdir()
    (home / 'settings.yaml').write_text('bundle:\n  app: []\n')
    context = subprocess.check_output([NATIVE, '-I', '-c',
        'import importlib.util,pathlib;print(pathlib.Path(importlib.util.find_spec("amplifier_module_context_simple").origin).parent)'], text=True).strip()
    bundle = tmp_path / 'chosen.yaml'
    audit = tmp_path / 'selected-model.txt'
    provider_config = {'fixtureModels': [{'id': 'first-model'}, {'id': 'second-model'}], 'selectedModelAudit': str(audit)}
    bundle.write_text(f'bundle:\n  name: tui-parity\n  version: 1.0.0\nsession:\n  orchestrator:\n    module: loop-live\n  context:\n    module: context-simple\n    source: {context}\nproviders:\n  - module: provider-fixture\n    source: {PROVIDER}\n    config: {json.dumps(provider_config)}\n')
    native = tmp_path / 'native.json'
    managed = workspace / '.managed'
    native.write_text(json.dumps({'home': str(home), 'appHome': str(tmp_path / 'app'),
        'bundle': str(bundle), 'forkBundles': {'approved': str(bundle)},
        'managedSessionRoots': [str(managed)], 'adminWorkspaceRoots': [str(workspace)]}))
    config = tmp_path / 'host.json'
    settings = {'testDiagnostics': str(tmp_path / 'catalog-diagnostic.json'), 'stateDirectory': str(tmp_path / 'host'), 'port': 0,
        'defaultWorkingDirectory': str(workspace), 'allowedWorkspaceRoots': [str(workspace)],
        'managedSessionRoot': str(managed), 'fixtureManagedProtection': True,
        'catalogProcess': {'command': CATALOG, 'args': ['-I', '-m', 'amplifier_session_catalog', 'serve',
            '--db', str(tmp_path / 'catalog.sqlite'), '--home', str(home), '--app-home', str(tmp_path / 'app'),
            '--workspace', str(workspace), '--scan-on-start', '--scan-interval', '0', '--workspace-check-interval', '0'],
            'maintenanceMs': 100, 'env': {'PYTHONDONTWRITEBYTECODE': '1'}},
        'engines': [{'id': 'amplifier', 'command': NATIVE, 'args': ['-I', '-m', 'amplifier_acp', '--config', str(native)],
            'env': {'PYTHONDONTWRITEBYTECODE': '1', 'AMPLIFIER_SESSION_STATE_HOME': str(tmp_path / 'writers')}}]}
    if os.environ.get('TUI_WORKSPACES_MODULE') and os.environ.get('TUI_OWNERS_PYTHON'):
        owner = tmp_path / 'workspaces.json'
        owner.write_text(json.dumps({'stateDirectory': str(tmp_path / 'workspace-owner'),
            'allowedRoots': [str(workspace)], 'defaultRoot': str(workspace)}))
        settings['workspaceOwner'] = {'command': os.environ['TUI_OWNERS_PYTHON'],
            'args': ['-I', '-c', 'from amplifier_unified_workspaces.server import main;main()', '--config', str(owner)],
            'env': {'PYTHONDONTWRITEBYTECODE': '1'}}
    config.write_text(json.dumps(settings))
    process = await asyncio.create_subprocess_exec('node', str(ROOT / 'tests/fixtures/ahp_fixture_host.mjs'), '--config', str(config),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    async with asyncio.timeout(20):
        line = await process.stdout.readline()
    assert line, (await process.stderr.read()).decode()
    yield json.loads(line)['url'], tmp_path, workspace, audit
    process.terminate()
    await process.wait()
    (tmp_path / 'host-stderr.txt').write_bytes(await process.stderr.read())


async def native_view(native_host):
    url, root, workspace, _ = native_host
    state = ClientState(root / 'client', url, 'parity')
    transport = Transport(url, '', state.identity)
    events = []
    bridge = UnifiedBridge(events.append, transport, state, workspace=str(workspace),
        creation={'managed': True, 'agent': 'amplifier', 'bundle': 'approved', 'provider': 'fixture', 'model': 'second-model'})
    await bridge.open()
    return bridge, events


async def test_current_native_managed_flags_recovery_review_and_original_receipt(native_host):
    bridge, events = await native_view(native_host)
    _, root, _, audit = native_host
    try:
        assert not (root / 'workspace/.managed/chats').exists()  # Discovery never allocates.
        assert not audit.exists()
        assert (await bridge.dispatch(request(bridge, 'submit', text='one explicit turn')))[0]
        await wait_for(lambda: bridge.session.get('status') == 'ready' and audit.exists())
        # Native also makes one automatic naming call using provider defaults.
        # Require both exact original calls; later recovery must add neither.
        await wait_for(lambda: audit.read_text() == 'second-model\nNone\n')
        assert audit.read_text() == 'second-model\nNone\n'
        source = bridge.selected
        await bridge.dispatch(request(bridge, 'draft', text='private retained recovery draft'))
        await asyncio.sleep(1.5)  # Independent catalog completes its metadata scan.
        result = await bridge.dispatch(request(bridge, 'host_review', purpose='recovery'))
        assert result[0], result
        review = next(e for e in reversed(events) if e['type'] == 'host_review')
        assert 'historyRevision' in review['detail']
        assert (await bridge.dispatch(request(bridge, 'host_apply', token=review['token'], target=source)))[0]
        effect_id, row = next(iter(bridge.store.data['hostEffects'].items()))
        assert row['result']['workReplayed'] is False
        assert row['result']['preservedSource'] is True
        assert row['result']['uri'] != source
        assert bridge.selected == source
        assert bridge.store.data['drafts'][source] == 'private retained recovery draft'
        # Native also makes one automatic naming call using provider defaults.
        # Require both exact original calls; later recovery must add neither.
        await wait_for(lambda: audit.read_text() == 'second-model\nNone\n')
        assert audit.read_text() == 'second-model\nNone\n'
        assert not (await bridge.dispatch(request(bridge, 'host_apply', token=review['token'], target=source)))[0]
        assert (await bridge.dispatch(request(bridge, 'host_receipt', id=effect_id)))[0]
        # Native also makes one automatic naming call using provider defaults.
        # Require both exact original calls; later recovery must add neither.
        await wait_for(lambda: audit.read_text() == 'second-model\nNone\n')
        assert audit.read_text() == 'second-model\nNone\n'
        journal = bridge.store.path.with_suffix('.intent.jsonl').read_text()
        assert 'one explicit turn' in journal and effect_id in journal
    finally:
        await bridge.close()


async def test_managed_file_review_requires_same_selection_and_preserves_canonical(native_host):
    bridge, events = await native_view(native_host)
    _, root, _, audit = native_host
    try:
        result = await bridge.dispatch(request(bridge, 'submit', text='retained canonical'))
        assert result[0], result
        await wait_for(lambda: bridge.session.get('status') == 'ready' and audit.exists())
        source = bridge.selected
        generated = Path(bridge.session['workspace']) / 'generated.txt'
        generated.write_text('Owned fixture output')
        before = {str(p.relative_to(root / 'home')): p.read_bytes() for p in (root / 'home/projects').rglob('*') if p.is_file()}
        await asyncio.sleep(1.5)
        for _ in range(20):
            result = await bridge.dispatch(request(bridge, 'host_review', purpose='managed-files'))
            if result[0] or 'Indexed family coverage' not in result[1]:
                break
            await asyncio.sleep(.2)
        assert result[0], result
        review = next(e for e in reversed(events) if e['type'] == 'host_review')
        # A stale explicit target never applies even with a valid review token.
        assert not (await bridge.dispatch(request(bridge, 'host_apply', token=review['token'], target='ahp-session:/wrong')))[0]
        assert generated.exists()
        for _ in range(20):
            result = await bridge.dispatch(request(bridge, 'host_review', purpose='managed-files'))
            if result[0] or 'Indexed family coverage' not in result[1]:
                break
            await asyncio.sleep(.2)
        assert result[0], result
        review = next(e for e in reversed(events) if e['type'] == 'host_review')
        # The preview retires the idle native lifetime before capturing its review.
        # Compare disposal against that settled canonical baseline, not an earlier live flush.
        before = {str(p.relative_to(root / 'home')): p.read_bytes() for p in (root / 'home/projects').rglob('*') if p.is_file()}
        result = await bridge.dispatch(request(bridge, 'host_apply', token=review['token'], target=source))
        assert result[0], result
        assert not generated.exists()
        after = {str(p.relative_to(root / 'home')): p.read_bytes() for p in (root / 'home/projects').rglob('*') if p.is_file()}
        assert after == before
        command_id, row = next(iter(bridge.store.data['hostEffects'].items()))
        assert row['result']['status'] == 'completed'
        assert (await bridge.dispatch(request(bridge, 'host_receipt', id=command_id)))[0]
        # Native also makes one automatic naming call using provider defaults.
        # Require both exact original calls; later recovery must add neither.
        await wait_for(lambda: audit.read_text() == 'second-model\nNone\n')
        assert audit.read_text() == 'second-model\nNone\n'
    finally:
        await bridge.close()


@pytest.mark.skipif(os.environ.get('TUI_TEST_CANDIDATES') != '1', reason='Build actual renderer')
async def test_actual_native_terminal_flags_details_recovery_and_draft_preservation(native_host):
    url, root, workspace, audit = native_host
    executable = os.environ.get('TUI_CONNECTED_EXECUTABLE')
    launcher = [executable] if executable else [sys.executable, '-m', 'amplifier_tui.connected']
    probe = Probe([*launcher, '--server', url, '--workspace', str(workspace), '--state-dir', str(root / 'terminal'),
        '--client', 'terminal-parity', '--new', '--managed', '--agent', 'amplifier', '--bundle', 'approved',
        '--provider', 'fixture', '--model', 'second-model'], 120, 40, guard_terminal_modes=True,
        env={'PYTHONPATH': ''} if executable else None)
    try:
        await displayed([probe], lambda: 'UNIFIED' in probe.text)
        assert not audit.exists()
        probe.send(b'Only explicit native terminal turn\r')
        await displayed([probe], lambda: 'Native graph reply:' in probe.text, timeout=30)
        # Native also makes one automatic naming call using provider defaults.
        # Require both exact original calls; later recovery must add neither.
        await wait_for(lambda: audit.read_text() == 'second-model\nNone\n')
        assert audit.read_text() == 'second-model\nNone\n'
        probe.send(b'/details\r')
        await displayed([probe], lambda: 'Host review' in probe.text and 'Selected source only' in probe.text)
        probe.send(b'\x1b[27u')
        await displayed([probe], lambda: 'Host review' not in probe.text)
        await asyncio.sleep(1.5)
        probe.send(b'/recovery\r')
        await displayed([probe], lambda: 'Create independent recovery' in probe.text)
        probe.send(b'\r')
        await displayed([probe], lambda: 'Open confirmed recovery' in probe.text, timeout=30)
        probe.send(b'\x1b[27u')
        await displayed([probe], lambda: 'Host review' not in probe.text)
        state = json.loads((root / 'terminal/connections/terminal-parity.json').read_text())
        files = workspace / '.managed/chats' / state['session'].removeprefix('ahp-session:/') / 'files'
        generated = files / 'terminal-generated.txt'
        generated.write_text('Owned terminal fixture output')
        probe.send(b'/managed-files\r')
        await displayed([probe], lambda: 'Dispose reviewed owned files' in probe.text, timeout=30)
        canonical = {str(p): p.read_bytes() for p in (root / 'home/projects').rglob('*') if p.is_file()}
        probe.send(b'\r')
        await displayed([probe], lambda: 'Host review · result' in probe.text, timeout=30)
        assert not generated.exists()
        assert {str(p): p.read_bytes() for p in (root / 'home/projects').rglob('*') if p.is_file()} == canonical
        probe.send(b'\x1b[27u')
        await displayed([probe], lambda: 'Host review' not in probe.text)
        probe.send(b'Private draft survives the review')
        await displayed([probe], lambda: 'Private draft survives' in probe.text)
        await asyncio.sleep(.3)
        evidence = Path(os.environ.get('TUI_EVIDENCE_DIR', root))
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / 'native-parity-terminal.txt').write_text(probe.text)
        (evidence / 'native-parity-terminal.ansi').write_bytes(bytes(probe.raw))
        state = json.loads((root / 'terminal/connections/terminal-parity.json').read_text())
        assert 'Private draft survives the review' in state['drafts'].values()
        # Native also makes one automatic naming call using provider defaults.
        # Require both exact original calls; later recovery must add neither.
        await wait_for(lambda: audit.read_text() == 'second-model\nNone\n')
        assert audit.read_text() == 'second-model\nNone\n'
    finally:
        evidence = Path(os.environ.get('TUI_EVIDENCE_DIR', root))
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / 'native-parity-terminal-final.txt').write_text(probe.text)
        await asyncio.to_thread(probe.close)


@pytest.mark.skipif(not os.environ.get('TUI_WORKSPACES_MODULE') or not os.environ.get('TUI_OWNERS_PYTHON'), reason='Installed workspace owner required')
async def test_negotiated_workspace_root_sessions_search_and_cursor_scopes(native_host):
    bridge, _ = await native_view(native_host)
    _, _, workspace, audit = native_host
    try:
        for index in range(53):
            await bridge.transport.command(None, 'session.create', {'workspace': str(workspace), 'provider': 'amplifier'}, str(__import__('uuid').uuid4()))
        # These are metadata-only host resources; no prompt or dormant agent initialized.
        assert not audit.exists()
        page = await bridge.transport.workspaces()
        chosen = next(row for row in page['items'] if row['path'] == str(workspace))
        assert chosen['available'] is True
        first = await bridge.transport.sessions(workspace=str(workspace))
        assert len(first['items']) == 50 and first['nextOffset'] == 50 and first['scopedSearch']
        second = await bridge.transport.sessions(workspace=str(workspace), offset=50)
        assert len(second['items']) == 3 and second['nextOffset'] is None
        await bridge.transport.snapshot(first['items'][0]['id'])
        await bridge.transport.command(first['items'][0]['id'], 'session.rename', {'title': 'Needle unique title'}, str(__import__('uuid').uuid4()))
        matches = await bridge.transport.sessions(workspace=str(workspace), query='Needle unique title')
        assert len(matches['items']) == 1
        with pytest.raises(ValueError, match='cursor expired'):
            await bridge.transport.sessions(workspace=str(workspace), offset=50)
        assert not audit.exists()
    finally:
        await bridge.close()


async def test_current_native_model_configuration_or_truthful_unavailability(native_host):
    bridge, events = await native_view(native_host)
    _, root, _, audit = native_host
    try:
        assert (await bridge.dispatch(request(bridge, 'submit', text='Synthetic configuration fixture seed')))[0]
        await wait_for(lambda: bridge.session.get('status') == 'ready' and audit.exists())
        original_audit = audit.read_bytes()
        await bridge.dispatch(request(bridge, 'draft', text='Native setting draft remains private'))
        offered = await bridge.dispatch(request(bridge, 'setting_choices', property='model'))
        if not bridge.session.get('config', {}).get('schema', {}).get('properties', {}).get('model', {}).get('enum'):
            assert not offered[0] and 'cannot be changed' in offered[1]
            assert not bridge.store.data.get('configEffects')
            assert bridge.store.data['drafts'][bridge.selected] == 'Native setting draft remains private'
            assert audit.read_bytes() == original_audit
            return  # This installed native fixture supplied no standard model schema; no choices are guessed.
        assert offered[0], (offered, bridge.session.get('config'))
        menu = next(e for e in reversed(events) if e['type'] == 'setting_choices')
        alternative = next(row['value'] for row in menu['choices'] if row['value'] != menu['current'])
        changed = await bridge.dispatch(request(bridge, 'setting_set', property='model', value=alternative))
        assert changed[0], changed
        assert bridge.session['config']['values']['model'] == alternative
        assert bridge.store.data['drafts'][bridge.selected] == 'Native setting draft remains private'
        assert audit.read_bytes() == original_audit  # Changing the native setting did not run another completion.
        assert (root / 'client/connections/parity.intent.jsonl').exists()
    finally:
        await bridge.close()
