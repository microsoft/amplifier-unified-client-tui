"""Public package boundary; no engine dependency or standalone launch bypass."""
import ast
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_client_has_no_runtime_imports_or_dependencies():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert config["project"]["name"] == "amplifier-unified-client-tui"
    assert config["project"]["dependencies"] == []
    assert not config["project"].get("optional-dependencies")
    for path in (ROOT / "src/amplifier_tui").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            assert not any(name.startswith(("amplifier_core", "amplifier_foundation", "amplifier_app_cli", "amplifier_agent")) for name in names), path

def test_module_and_console_have_no_standalone_bypass():
    result = subprocess.run([sys.executable, "-m", "amplifier_tui", "--standalone"], capture_output=True, text=True)
    assert result.returncode == 2
    assert "unrecognized arguments" in result.stderr
    result = subprocess.run([sys.executable, "-m", "amplifier_tui", "--version"], capture_output=True, text=True)
    assert result.returncode == 0 and "amplifier-unified-client-tui" in result.stdout


def test_private_state_locks_and_recovers_unknown_intent(tmp_path):
    import pytest

    from amplifier_tui.client_state import ClientState
    first = ClientState(tmp_path, 'ws://localhost:8765/ahp', 'one')
    try:
        with pytest.raises(ValueError, match='already open'):
            ClientState(tmp_path, 'ws://localhost:8765/ahp', 'one')
        first.data['outbox']['request'] = {'status': 'sending', 'text': 'retained'}
        first.save()
        assert first.path.stat().st_mode & 0o777 == 0o600
    finally:
        first.close()
    recovered = ClientState(tmp_path, 'ws://localhost:8765/ahp', 'one')
    assert recovered.data['outbox']['request']['status'] == 'unknown'
    recovered.close()
    with pytest.raises(ValueError, match='incompatible'):
        ClientState(tmp_path, 'wss://different.example/ahp', 'one')


def test_title_only_update_and_explicit_window_do_not_drop_items():
    from types import SimpleNamespace

    from amplifier_tui.unified_client import UnifiedBridge
    events = []
    bridge = UnifiedBridge(events.append, SimpleNamespace(), SimpleNamespace(data={'outbox': {}}))
    bridge.session = {'id': 's', 'title': 'first', 'displayItems': [
        {'id': str(i), 'kind': 'assistant', 'text': 'item', 'detail': '', 'status': ''} for i in range(150)]}
    bridge.online = True
    bridge.selected = 's'
    bridge.publish()
    assert len(bridge.items()) == 150
    events.clear()
    bridge.session['title'] = 'renamed'
    bridge.publish()
    assert any(e['type'] == 'remote_patch' and e['title'] == 'renamed' and not e['items'] for e in events)
