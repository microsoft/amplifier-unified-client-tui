"""Export/validate bounded current-TUI release assets; never publish or install."""
import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import zipfile
from contextlib import contextmanager
from pathlib import Path

FORMAT = 'amplifier-unified-client-tui.release'
REPOSITORY = 'https://github.com/microsoft/amplifier-unified-client-tui'
PACKAGE = 'amplifier-unified-client-tui'
COMPATIBILITY = {'ahpVersions': ['0.9.0'], 'sdkVersion': '0.9.0',
                 'pythonRequires': '>=3.11', 'nodeRequires': '>=22'}
MAX_BYTES = 128 * 1024
MAX_ARTIFACTS = 16
MAX_WHEEL_BYTES = 256 * 1024 * 1024
MAX_LOG_BYTES = 16 * 1024 * 1024
CHUNK_BYTES = 64 * 1024
HEX = re.compile(r'[0-9a-f]{64}')
VERSION = re.compile(r'[0-9]+\.[0-9]+\.[0-9]+(?:rc[0-9]+)?')
ASSET = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,199}')
CHECKS = ['protocol-install', 'protocol-build', 'native-build', 'native-tests', 'ruff',
          'direction', 'current-tests', 'wheel-build', 'install-env', 'install-wheel',
          'installed-isolation', 'installed-terminal']


def fingerprint(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


@contextmanager
def regular(path, limit, expected_bytes=None):
    if type(limit) is not int or limit < 1 or (expected_bytes is not None
            and (type(expected_bytes) is not int or not 0 < expected_bytes <= limit)):
        raise ValueError('Invalid file byte bound')
    fd = None
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('Input must be a regular file')
        if before.st_size > limit or (expected_bytes is not None and before.st_size != expected_bytes):
            raise ValueError('File bytes exceed or differ from bound')
        yield fd, before.st_size
        if (fingerprint(os.fstat(fd)) != fingerprint(before)
                or fingerprint(os.lstat(path)) != fingerprint(before)):
            raise ValueError('Input changed during verification')
    except OSError as exc:
        raise ValueError('Input cannot be opened as a stable regular file') from exc
    finally:
        if fd is not None:
            os.close(fd)


def read_file(path, limit, *, expected_bytes=None, collect=False, sink=None):
    hasher, data, count = hashlib.sha256(), bytearray(), 0
    read_bound = expected_bytes if expected_bytes is not None else limit
    with regular(path, limit, expected_bytes) as (fd, size):
        while True:
            chunk = os.read(fd, min(CHUNK_BYTES, read_bound + 1 - count))
            if not chunk:
                break
            count += len(chunk)
            if count > read_bound:
                raise ValueError('File grew beyond byte bound')
            hasher.update(chunk)
            if collect:
                data.extend(chunk)
            if sink:
                sink.write(chunk)
        if count != size:
            raise ValueError('Input size changed during verification')
    return bytes(data), hasher.hexdigest()


def digest(path, *, max_bytes=MAX_BYTES, expected_bytes=None):
    return read_file(path, max_bytes, expected_bytes=expected_bytes)[1]


def copy_asset(source, destination, *, max_bytes, expected_sha, expected_bytes=None):
    with destination.open('xb') as sink:
        _, actual = read_file(source, max_bytes, expected_bytes=expected_bytes, sink=sink)
    if actual != expected_sha:
        raise ValueError('Asset changed before copying')


def fields(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError('Unexpected or missing manifest fields')


def asset(value):
    if not isinstance(value, str) or not ASSET.fullmatch(value):
        raise ValueError('Asset must be a bounded basename')
    return value


def sha(value):
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise ValueError('Invalid SHA256')


def target(tag):
    if not isinstance(tag, str):
        raise ValueError('Invalid wheel tag')
    match = re.fullmatch(r'py3-none-(linux_(x86_64|aarch64)|macosx_(\d+)_(\d+)_(arm64|x86_64))', tag)
    if not match:
        raise ValueError('Unqualified wheel target')
    if match[2]:
        return {'os': 'linux', 'arch': 'arm64' if match[2] == 'aarch64' else 'x86_64',
                'wheelTag': tag, 'osFloor': None}
    return {'os': 'macos', 'arch': match[5], 'wheelTag': tag, 'osFloor': f'{match[3]}.{match[4]}'}


def load(path, *, expected_sha=None):
    data, actual_sha = read_file(path, MAX_BYTES, collect=True)
    if expected_sha is not None and actual_sha != expected_sha:
        raise ValueError('Evidence bytes/hash mismatch')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def validate(value):
    fields(value, ['format', 'schemaVersion', 'package', 'source', 'compatibility', 'artifacts'])
    if value['format'] != FORMAT or type(value['schemaVersion']) is not int or value['schemaVersion'] != 1:
        raise ValueError('Unsupported manifest format/version')
    fields(value['package'], ['name', 'version'])
    version = value['package']['version']
    if value['package']['name'] != PACKAGE or not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError('Wrong package/version')
    fields(value['source'], ['repository', 'commit'])
    if value['source']['repository'] != REPOSITORY or not isinstance(value['source']['commit'], str) or not re.fullmatch(r'[0-9a-f]{40}', value['source']['commit']):
        raise ValueError('Wrong canonical source')
    if value['compatibility'] != COMPATIBILITY:
        raise ValueError('Unsupported AHP/runtime compatibility')
    artifacts = value['artifacts']
    if not isinstance(artifacts, list) or not 1 <= len(artifacts) <= MAX_ARTIFACTS:
        raise ValueError('Manifest requires bounded qualified artifacts')
    names, targets = set(), set()
    for item in artifacts:
        fields(item, ['filename', 'bytes', 'sha256', 'target', 'qualification'])
        name = asset(item['filename'])
        fields(item['target'], ['os', 'arch', 'wheelTag', 'osFloor'])
        expected = target(item['target']['wheelTag'])
        if item['target'] != expected or name != f'amplifier_unified_client_tui-{version}-{expected["wheelTag"]}.whl':
            raise ValueError('Artifact version/target/tag mismatch')
        if name in names or expected['wheelTag'] in targets:
            raise ValueError('Duplicate asset/target')
        names.add(name)
        targets.add(expected['wheelTag'])
        if type(item['bytes']) is not int or not 0 < item['bytes'] <= 256 * 1024 * 1024:
            raise ValueError('Invalid artifact bytes')
        sha(item['sha256'])
        q = item['qualification']
        fields(q, ['status', 'evidenceFilename', 'evidenceSha256', 'installedIsolation', 'privacy',
                   'actualPTY', 'testedPython', 'testedNode', 'testedOS', 'minimumGlibc'])
        if q['status'] != 'qualified' or any(q[key] is not True for key in ['installedIsolation', 'privacy', 'actualPTY']):
            raise ValueError('Artifact is not qualified')
        asset(q['evidenceFilename'])
        if q['evidenceFilename'] != name.removesuffix('.whl') + '.qualification.json':
            raise ValueError('Evidence asset does not bind wheel')
        sha(q['evidenceSha256'])
        for key, minimum in [('testedPython', (3, 11)), ('testedNode', (22, 0))]:
            v = q[key]
            if not isinstance(v, str) or not re.fullmatch(r'\d+\.\d+\.\d+', v) or tuple(map(int, v.split('.')[:2])) < minimum:
                raise ValueError('Untested/incompatible runtime')
        if not isinstance(q['testedOS'], str) or not 1 <= len(q['testedOS']) <= 120:
            raise ValueError('Missing tested OS')
        libc = q['minimumGlibc']
        if expected['os'] == 'linux':
            if not isinstance(libc, str) or not re.fullmatch(r'\d+\.\d+', libc):
                raise ValueError('Linux requires tested glibc floor')
        elif libc is not None:
            raise ValueError('macOS must not claim glibc')
    return value


def verify_assets(value, directory):
    validate(value)
    for item in value['artifacts']:
        wheel = directory / item['filename']
        q = item['qualification']
        evidence = directory / q['evidenceFilename']
        if digest(wheel, max_bytes=MAX_WHEEL_BYTES, expected_bytes=item['bytes']) != item['sha256']:
            raise ValueError('Release asset bytes/hash mismatch')
        proof = load(evidence, expected_sha=q['evidenceSha256'])
        fields(proof, ['format', 'schemaVersion', 'package', 'source', 'compatibility', 'wheel', 'qualification', 'checks', 'checkLogHashes', 'limits'])
        if proof['format'] != FORMAT + '.qualification' or type(proof['schemaVersion']) is not int or proof['schemaVersion'] != 1:
            raise ValueError('Unsupported evidence format')
        fields(proof['checkLogHashes'], CHECKS)
        for value_sha in proof['checkLogHashes'].values():
            sha(value_sha)
        if not isinstance(proof['limits'], list) or not 1 <= len(proof['limits']) <= 8 or any(not isinstance(limit, str) or len(limit) > 200 for limit in proof['limits']):
            raise ValueError('Invalid evidence scope')
        if (proof.get('source') != value['source'] or proof.get('package') != value['package']
                or proof.get('compatibility') != value['compatibility']
                or proof.get('wheel') != {key: item[key] for key in ['filename', 'bytes', 'sha256', 'target']}
                or proof.get('checks') != {name: 'passed' for name in CHECKS}
                or proof.get('qualification') != {key: q[key] for key in q if key not in ['evidenceFilename', 'evidenceSha256']}):
            raise ValueError('Qualification evidence binding mismatch')


def write(path, value):
    data = json.dumps(value, indent=2, sort_keys=True) + '\n'
    if len(data.encode()) > MAX_BYTES:
        raise ValueError('Export exceeds byte limit')
    path.write_text(data)


def export(root, output, expected_target=None):
    receipt = load(root / '.evidence/current/receipt.json')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=root, text=True)
    if dirty or receipt.get('sourceCommit') != commit:
        raise ValueError('Qualification must bind exact clean source')
    name = asset(receipt['wheel'])
    wheel = root / 'dist' / name
    if digest(wheel, max_bytes=MAX_WHEEL_BYTES, expected_bytes=receipt['bytes']) != receipt['sha256']:
        raise ValueError('Wheel changed after qualification')
    actual_target = target(receipt['wheelTag'])
    if expected_target and expected_target != actual_target['os'] + '-' + actual_target['arch']:
        raise ValueError('Runner does not match expected release target')
    q = receipt['releaseQualification']
    if q['status'] != 'qualified':
        raise ValueError('Incomplete installed qualification')
    with regular(wheel, MAX_WHEEL_BYTES, receipt['bytes']) as (fd, _), os.fdopen(os.dup(fd), 'rb') as reader, zipfile.ZipFile(reader) as archive:
        metadata = next(n for n in archive.namelist() if n.endswith('.dist-info/METADATA'))
        if archive.getinfo(metadata).file_size > MAX_BYTES:
            raise ValueError('Wheel metadata exceeds byte bound')
        headers = dict(line.split(': ', 1) for line in archive.read(metadata).decode().split('\n\n', 1)[0].splitlines() if ': ' in line)
        if headers['Name'] != PACKAGE or headers['Version'] != receipt['version'] or headers['Requires-Python'] != '>=3.11':
            raise ValueError('Wrong installed package metadata')
    summary = {'format': FORMAT + '.qualification', 'schemaVersion': 1,
               'package': {'name': PACKAGE, 'version': receipt['version']},
               'source': {'repository': REPOSITORY, 'commit': commit}, 'compatibility': COMPATIBILITY,
               'wheel': {'filename': name, 'bytes': receipt['bytes'], 'sha256': receipt['sha256'], 'target': target(receipt['wheelTag'])},
               'qualification': q, 'checks': {name: 'passed' for name in CHECKS},
               'checkLogHashes': {name: digest(root / '.evidence/current' / (name + '.txt'), max_bytes=MAX_LOG_BYTES) for name in CHECKS},
               'limits': ['Deterministic local public-host/provider fixtures', 'No real account, physical device or production deployment acceptance']}
    output.mkdir(parents=True, exist_ok=False)
    evidence_name = name.removesuffix('.whl') + '.qualification.json'
    write(output / evidence_name, summary)
    copy_asset(wheel, output / name, max_bytes=MAX_WHEEL_BYTES, expected_bytes=receipt['bytes'], expected_sha=receipt['sha256'])
    value = {'format': FORMAT, 'schemaVersion': 1, 'package': summary['package'], 'source': summary['source'],
             'compatibility': COMPATIBILITY, 'artifacts': [{**summary['wheel'], 'qualification': {
                 **q, 'evidenceFilename': evidence_name, 'evidenceSha256': digest(output / evidence_name)}}]}
    validate(value)
    verify_assets(value, output)
    write(output / 'manifest.json', value)
    return value


def assemble(inputs, output):
    values = [validate(load(path)) for path in inputs]
    first = values[0]
    result = {key: value for key, value in first.items() if key != 'artifacts'}
    result['artifacts'] = []
    for path, value in zip(inputs, values):
        if any(value[key] != first[key] for key in first if key != 'artifacts'):
            raise ValueError('Mixed source/version/compatibility fragments')
        verify_assets(value, Path(path).parent)
        result['artifacts'].extend(value['artifacts'])
    validate(result)
    output.mkdir(parents=True, exist_ok=False)
    for path, value in zip(inputs, values):
        for item in value['artifacts']:
            for name in [item['filename'], item['qualification']['evidenceFilename']]:
                is_wheel = name == item['filename']
                copy_asset(Path(path).parent / name, output / name,
                    max_bytes=MAX_WHEEL_BYTES if is_wheel else MAX_BYTES,
                    expected_bytes=item['bytes'] if is_wheel else None,
                    expected_sha=item['sha256'] if is_wheel else item['qualification']['evidenceSha256'])
    verify_assets(result, output)
    write(output / 'manifest.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('validate')
    p.add_argument('manifest', type=Path)
    p.add_argument('--verify-assets', action='store_true')
    p = sub.add_parser('export')
    p.add_argument('--root', type=Path, default=Path.cwd())
    p.add_argument('--expected-target', choices=['linux-arm64', 'linux-x86_64', 'macos-arm64', 'macos-x86_64'])
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('assemble')
    p.add_argument('manifests', nargs='+', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'export':
        value = export(args.root.resolve(), args.output.resolve(), args.expected_target)
    elif args.mode == 'assemble':
        value = assemble(args.manifests, args.output.resolve())
    else:
        value = validate(load(args.manifest))
        if args.verify_assets:
            verify_assets(value, args.manifest.parent)
    print(json.dumps({'source': value['source'], 'qualifiedArtifacts': len(value['artifacts'])}))


if __name__ == '__main__':
    main()
