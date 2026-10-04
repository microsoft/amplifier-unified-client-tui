"""Supplement sealed-wheel qualification with exact managed runtime assets."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, build_opener

ROOT = Path(__file__).resolve().parents[2]


class HTTPSOnly(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, url):
        if urlparse(url).scheme != 'https':
            raise ValueError('Runtime redirect must remain HTTPS')
        return super().redirect_request(request, fp, code, message, headers, url)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(65536), b''):
            digest.update(chunk)
    return digest.hexdigest()


def extract(archive, destination, archive_root):
    # All payload bytes have already been verified. Reject special files and
    # ambiguous paths, bound expansion, and retain data-filter link checks.
    with tarfile.open(archive, 'r:gz') as tar:
        members = []
        total = 0
        for member in tar:
            name = PurePosixPath(member.name)
            total += member.size
            if (len(members) >= 25000 or total > 768 * 1024 * 1024
                    or name.is_absolute() or not name.parts
                    or name.parts[0] != archive_root or '..' in name.parts
                    or '\\' in member.name
                    or not (member.isfile() or member.isdir() or member.issym() or member.islnk())):
                raise ValueError('Unsupported managed runtime archive')
            members.append(member)
        destination.mkdir()
        tar.extractall(destination, members=members, filter='data')
    return destination / archive_root


def download(descriptor, path):
    with build_opener(HTTPSOnly()).open(descriptor['url'], timeout=45) as response:
        if urlparse(response.url).scheme != 'https':
            raise ValueError('Runtime requires HTTPS')
        remaining = descriptor['bytes']
        with path.open('xb') as output:
            while chunk := response.read(min(65536, remaining + 1)):
                remaining -= len(chunk)
                if remaining < 0:
                    raise ValueError('Runtime exceeds reviewed byte size')
                output.write(chunk)
    if remaining != 0 or sha(path) != descriptor['sha256']:
        raise ValueError('Runtime archive identity mismatch')


def run(name, command, logs, environment, cwd):
    print(name, flush=True)
    with (logs / (name + '.txt')).open('w') as output:
        subprocess.run(command, cwd=cwd, env=environment, stdout=output,
                       stderr=subprocess.STDOUT, check=True, timeout=180)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', choices=['linux-x86_64', 'macos-x86_64'], required=True)
    arguments = parser.parse_args()
    spec = json.loads((ROOT / '.github/qualification-runtimes.json').read_text())[arguments.target]
    source = ROOT / '.state/tui-source'
    assets = ROOT / '.state/sealed-wheel'
    state = ROOT / '.state/managed-runtime'
    state.mkdir()
    logs = state / 'private-logs'
    logs.mkdir()
    exported = ROOT / '.state/managed-runtime-export'
    exported.mkdir()
    environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    if head != spec['sourceCommit'] or subprocess.check_output(
            ['git', 'status', '--porcelain', '--untracked-files=no'], cwd=source, text=True):
        raise ValueError('Exact clean qualified source required')
    if sha(assets / 'manifest.json') != spec['manifestSha256']:
        raise ValueError('Sealed manifest changed')
    manifest = json.loads((assets / 'manifest.json').read_text())
    if manifest['source']['commit'] != head:
        raise ValueError('Sealed artifact source mismatch')
    wheel = assets / spec['filename']
    if sha(wheel) != spec['wheelSha256']:
        raise ValueError('Sealed wheel changed')
    run('sealed-release', [sys.executable, 'scripts/release_manifest.py', 'validate',
                          str(assets / 'manifest.json'), '--verify-assets'], logs, environment, source)
    runtimes = json.loads(json.dumps(spec['runtimes']))
    executables = {}
    for kind, runtime in runtimes.items():
        archive = state / (kind + '.tar.gz')
        download(runtime, archive)
        directory = extract(archive, state / kind, runtime['archiveRoot'])
        executable = directory / runtime['executable']
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise ValueError('Managed executable missing')
        executables[kind] = executable
        version = subprocess.check_output([str(executable), '--version'], text=True).strip()
        if version != ('Python ' if kind == 'python' else 'v') + runtime['version']:
            raise ValueError('Managed executable version mismatch')
        if kind == 'node':
            runtime['executableSha256'] = sha(executable)
            actual = json.loads(subprocess.check_output([str(executable), '-p',
                'JSON.stringify({os:process.platform,arch:process.arch})'], text=True))
            if actual != {'os': 'linux' if arguments.target.startswith('linux') else 'darwin', 'arch': 'x64'}:
                raise ValueError('Managed Node target mismatch')
        else:
            actual = subprocess.check_output([str(executable), '-I', '-c',
                                               'import platform; print(platform.machine())'], text=True).strip()
            if actual != 'x86_64':
                raise ValueError('Managed Python target mismatch')
    environment['PATH'] = str(executables['node'].parent) + os.pathsep + environment['PATH']
    environment.update(AMPLIFIER_TUI_NODE=str(executables['node']), TUI_TEST_CANDIDATES='1')
    inputs = ROOT / '.state/inputs'
    run('independent-host', [sys.executable, 'scripts/prepare_qualification_host.py',
        '--fixture-sha256', '54e53991d0acbdd3e0547379de7c41f04e65b0ff70653cd92b2d03b2d13ccb0f'],
        logs, environment, inputs)
    host = inputs / '.state/qualification-host/node_modules/@amplifier/unified-host/dist'
    environment.update(AHP_HOST_ENTRY=str(host / 'cli.js'), AHP_HOST_MODULE=(host / 'index.js').as_uri())
    for name in ['consumer', 'test-tools']:
        target = state / name
        run(name + '-venv', ['uv', 'venv', '--python', str(executables['python']), str(target)],
            logs, environment, ROOT)
        python = target / 'bin/python'
        run(name + '-wheel', ['uv', 'pip', 'install', '--python', str(python), '--no-deps', str(wheel)],
            logs, environment, ROOT)
    consumer = state / 'consumer/bin/python'
    tools = state / 'test-tools/bin/python'
    run('test-dependencies', ['uv', 'pip', 'install', '--python', str(tools), 'pytest>=8',
        'pytest-asyncio>=1', 'pyte==0.8.2', 'pillow==12.1.1'], logs, environment, ROOT)
    managed_root = executables['python'].parent.parent
    probe = """import importlib.util,platform,sys,zipfile
from pathlib import Path
import amplifier_tui
assert Path(sys.base_prefix).resolve()==Path(sys.argv[1]).resolve()
assert all(importlib.util.find_spec(n) is None for n in ('amplifier_core','amplifier_foundation','amplifier_app_cli'))
p=Path(amplifier_tui.__file__).parent
with zipfile.ZipFile(sys.argv[2]) as z:
 for n in z.namelist():
  if n.startswith('amplifier_tui/') and not n.endswith('/'):
   assert (p.parent/n).read_bytes()==z.read(n), n
print('Managed interpreter and every installed wheel payload file match')
print(platform.python_version())
"""
    run('installed-isolation-payload', [str(consumer), '-I', '-c', probe, str(managed_root), str(wheel)],
        logs, environment, ROOT)
    environment.update(TUI_CONNECTED_EXECUTABLE=str(state / 'consumer/bin/amplifier-unified-client-tui'),
                       TUI_EVIDENCE_DIR=str(logs), PYTHONPATH='')
    junit = state / 'installed-terminal.xml'
    run('installed-terminal', [str(tools), '-m', 'pytest', '-q', 'tests/test_ahp_terminal.py',
        '--basetemp', str(state / 'profiles'), '--junitxml', str(junit)], logs, environment, source)
    cases = ET.parse(junit).findall('.//testcase')
    if len(cases) != 5 or any(case.find(name) is not None for case in cases
                            for name in ['failure', 'error', 'skipped']):
        raise ValueError('All five installed PTY cases must pass without skips')
    tested_os = ('macOS ' + platform.mac_ver()[0]) if sys.platform == 'darwin' else (
        lambda release: release['ID'] + ' ' + release['VERSION_ID'])(platform.freedesktop_os_release())
    receipt = {'format': 'tui.managed-runtime-supplement.v1', 'sourceCommit': head,
        'workflowCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'platform': arguments.target, 'wheelSha256': spec['wheelSha256'], 'wheelFilename': wheel.name,
        'originalManifestSha256': spec['manifestSha256'], 'runtimes': runtimes,
        'managedArchiveDownloadsVerified': True, 'managedArchiveExtractionVerified': True,
        'managedPythonBasePrefixVerified': True, 'installedWheelPayloadFilesEqual': True,
        'runtimeExecutableHashes': {kind: sha(path) for kind, path in executables.items()},
        'installedIsolation': True, 'actualInstalledPTYPassed': 5, 'skipped': 0,
        'testedOS': tested_os, 'minimumGlibc': platform.libc_ver()[1] if sys.platform == 'linux' else None,
        'originalSourceQualificationRetained': True, 'logHashes': {f.name: sha(f) for f in logs.glob('*.txt')},
        'limits': ['Supplement to original build qualification; no source or native rebuild',
                   'Deterministic independent public-host/provider fixtures',
                   'No account, physical-device, older-OS or live deployment acceptance']}
    if sha(wheel) != spec['wheelSha256'] or subprocess.check_output(
            ['git', 'status', '--porcelain', '--untracked-files=no'], cwd=source, text=True):
        raise ValueError('Qualified inputs changed')
    (exported / 'runtime-qualification.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
