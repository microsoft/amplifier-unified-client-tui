"""Qualify the current AHP client with an independent host and owned test state."""
import hashlib
import json
import os
import platform
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'TUI_TEST_CANDIDATES': '1'}
    for name in ('AHP_HOST_ENTRY', 'AHP_HOST_MODULE'):
        if not environment.get(name):
            raise SystemExit(f'{name} must identify the independently built public host package')
    source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT, text=True):
        raise SystemExit('Qualification requires a clean tracked checkout')
    evidence = ROOT / '.evidence/current'
    evidence.mkdir(parents=True, exist_ok=True)
    environment['TUI_EVIDENCE_DIR'] = str(evidence)

    def run(name, command, *, env=None):
        print(name, flush=True)
        with (evidence / (name + '.txt')).open('w') as output:
            subprocess.run(command, cwd=ROOT, env=env or environment, stdout=output,
                           stderr=subprocess.STDOUT, check=True)

    run('protocol-install', ['npm', 'ci', '--prefix', 'ahp'])
    run('protocol-build', ['npm', 'run', 'build', '--prefix', 'ahp'])
    run('native-build', ['cargo', 'build', '--locked', '--release', '--manifest-path', 'frontends/ratatui/Cargo.toml'])
    run('native-tests', ['cargo', 'test', '--locked', '--release', '--manifest-path', 'frontends/ratatui/Cargo.toml'])
    run('ruff', ['uv', 'run', '--no-sync', 'ruff', 'check', '.'])
    run('direction', ['uv', 'run', '--no-sync', 'python', 'scripts/check_direction.py'])
    run('current-tests', ['uv', 'run', '--no-sync', 'pytest', '-q', '-o', 'faulthandler_timeout=45', '--basetemp', '.state/qualification-tests'])
    run('wheel-build', ['uv', 'build', '--wheel'])
    wheels = sorted((ROOT / 'dist').glob('amplifier_unified_client_tui-*.whl'), key=lambda p: p.stat().st_mtime)
    wheel = wheels[-1]
    installed = ROOT / '.state/qualified-install'
    run('install-env', ['uv', 'venv', '--clear', str(installed)])
    run('install-wheel', ['uv', 'pip', 'install', '--python', str(installed / 'bin/python'), str(wheel)])
    run('installed-isolation', [str(installed / 'bin/python'), '-I', '-c',
        "import importlib.util,amplifier_tui; assert all(importlib.util.find_spec(m) is None for m in ('amplifier_core','amplifier_foundation','amplifier_app_cli')); from pathlib import Path; p=Path(amplifier_tui.__file__).parent; assert (p/'_ahp/bridge.mjs').is_file() and (p/'_bin/amplifier-ratatui').is_file(); print(p)"])
    installed_environment = {**environment, 'TUI_CONNECTED_EXECUTABLE': str(installed / 'bin/amplifier-unified-client-tui')}
    run('installed-terminal', ['uv', 'run', '--no-sync', 'pytest', '-q', 'tests/test_ahp_terminal.py', '--basetemp', '.state/installed-terminal'], env=installed_environment)
    import zipfile
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert not any('/host.py' in name or '/composition.py' in name or 'historical/' in name for name in names)
        assert not any(str(Path.home()).encode() in archive.read(name) for name in names), 'Wheel contains builder home path'
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() != source_commit:
        raise SystemExit('Source changed during qualification')
    if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT, text=True):
        raise SystemExit('Tracked source changed during qualification')
    version = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']['version']
    node_version = subprocess.check_output([os.environ.get('AMPLIFIER_TUI_NODE', 'node'), '--version'], text=True).strip().removeprefix('v')
    if int(node_version.split('.')[0]) < 22:
        raise SystemExit('Qualified helper requires Node >=22')
    python_version = subprocess.check_output([str(installed / 'bin/python'), '-I', '-c',
        'import platform; print(platform.python_version())'], text=True).strip()
    with zipfile.ZipFile(wheel) as archive:
        wheel_metadata = next(name for name in archive.namelist() if name.endswith('.dist-info/WHEEL'))
        wheel_tag = next(line.removeprefix('Tag: ') for line in archive.read(wheel_metadata).decode().splitlines() if line.startswith('Tag: '))
    if sys.platform == 'linux':
        libc, libc_version = platform.libc_ver()
        if libc != 'glibc':
            raise SystemExit('Release qualification supports glibc Linux only')
        os_release = platform.freedesktop_os_release()
        tested_os = os_release['ID'] + ' ' + os_release['VERSION_ID']
    else:
        libc_version = None
        tested_os = 'macOS ' + platform.mac_ver()[0]
    receipt = {'sourceCommit': source_commit, 'version': version, 'bytes': wheel.stat().st_size,
               'wheelTag': wheel_tag, 'releaseQualification': {
                   'status': 'qualified', 'installedIsolation': True, 'privacy': True, 'actualPTY': True,
                   'testedPython': python_version, 'testedNode': node_version, 'testedOS': tested_os,
                   'minimumGlibc': libc_version}, 'wheel': wheel.name, 'sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(),
               'installed': True, 'actualTerminal': True,
               'limits': ['ACP provider is a deterministic fixture', 'No real provider account, production host, physical terminal or release qualification on other platforms']}
    (evidence / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
