"""Prepare an independent host package for temporary same-repository CI tests."""
import argparse
import json
import re
import subprocess
import tarfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, build_opener

from release_manifest import MAX_BYTES, digest, load, regular

LIMIT = 8 * 1024 * 1024


class HTTPSOnly(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlparse(newurl).scheme != 'https':
            raise ValueError('Host artifact redirect must remain HTTPS')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def choose(url, sha256, fixture_sha):
    if fixture_sha:
        if url or sha256 or not re.fullmatch(r'[0-9a-f]{64}', fixture_sha):
            raise ValueError('Host input modes must be mutually exclusive')
        return 'fixture'
    if not url or not re.fullmatch(r'[0-9a-f]{64}', sha256 or ''):
        raise ValueError('Provide exact HTTPS tarball and SHA or exact fixture SHA')
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError('Host tarball requires credential-free HTTPS authority')
    return 'https'


def manifest(archive):
    with regular(archive, LIMIT) as (fd, _):
        import os
        with os.fdopen(os.dup(fd), 'rb') as stream, tarfile.open(fileobj=stream, mode='r|gz') as tar:
            value, members, expanded = None, 0, 0
            for item in tar:
                members += 1
                expanded += item.size
                name = PurePosixPath(item.name)
                if members > 1024 or expanded > 64 * 1024 * 1024:
                    raise ValueError('Host archive expansion exceeds bound')
                if name.is_absolute() or '..' in name.parts or '\\' in item.name or not (item.isfile() or item.isdir()):
                    raise ValueError('Unsafe host archive member')
                if item.name == 'package/package.json':
                    if value is not None or not item.isfile() or item.size > MAX_BYTES:
                        raise ValueError('Host package manifest duplicated or unbounded')
                    with tar.extractfile(item) as source:
                        value = json.loads(source.read(MAX_BYTES + 1))
    if value is None:
        raise ValueError('Host package manifest missing')
    if value.get('name') != '@amplifier/unified-host' or value.get('version') != '0.1.0':
        raise ValueError('Host package changed identity')
    return value


def prepare(root, url, sha256, fixture_sha):
    mode = choose(url, sha256, fixture_sha)
    state = root / '.state'
    state.mkdir(exist_ok=True)
    consumer = state / 'qualification-host'
    consumer.mkdir()  # Refuse reused, linked, or ambiguous owned consumers.
    archive = state / 'qualification-host.tgz'
    provenance = None
    if mode == 'fixture':
        provenance = load(root / '.qualification-inputs/provenance.json')
        if (provenance.get('format') != 'amplifier-unified-client-tui.temporary-host-input'
                or provenance.get('schemaVersion') != 1 or provenance.get('filename') != 'host-54e539.tgz'
                or provenance.get('sha256') != fixture_sha):
            raise ValueError('Reviewed host input provenance changed')
        source = root / '.qualification-inputs/host-54e539.tgz'
        if digest(source, max_bytes=LIMIT, expected_bytes=provenance['bytes']) != fixture_sha:
            raise ValueError('Reviewed opaque archive changed')
        from release_manifest import copy_asset
        copy_asset(source, archive, max_bytes=LIMIT, expected_bytes=provenance['bytes'], expected_sha=fixture_sha)
        expected = fixture_sha
    else:
        with build_opener(HTTPSOnly()).open(url, timeout=45) as response, archive.open('xb') as output:
            if urlparse(response.url).scheme != 'https':
                raise ValueError('Host artifact redirected outside HTTPS')
            total = 0
            while chunk := response.read(min(64 * 1024, LIMIT + 1 - total)):
                total += len(chunk)
                if total > LIMIT:
                    raise ValueError('Host archive exceeds byte limit')
                output.write(chunk)
        expected = sha256
    if digest(archive, max_bytes=LIMIT) != expected:
        raise ValueError('Host archive SHA mismatch; no fallback')
    package = manifest(archive)
    (consumer / 'package.json').write_text(json.dumps({'name': 'tui-independent-host-consumer', 'version': '0.0.0', 'private': True})+'\n')
    for operation, expected_path in [('prefix', consumer), ('root', consumer/'node_modules')]:
        actual = subprocess.check_output(['npm', '--prefix', str(consumer), '--global=false', '--workspaces=false', operation], text=True).strip()
        if Path(actual).resolve() != expected_path.resolve():
            raise ValueError('npm consumer scope escaped its owned directory')
    subprocess.run(['npm', 'install', '--prefix', str(consumer), '--global=false', '--workspaces=false', '--ignore-scripts', str(archive)], check=True)
    installed = json.loads((consumer/'node_modules/@amplifier/unified-host/package.json').read_text())
    if any(installed.get(key) != package.get(key) for key in ['name', 'version']):
        raise ValueError('Installed host changed package identity')
    value = {'inputMode': mode, 'archiveSHA256': expected, 'archiveBytes': archive.stat().st_size,
             'package': {key: package[key] for key in ['name', 'version']}, 'sourceProvenance': provenance,
             'installedLockSHA256': digest(consumer/'package-lock.json', max_bytes=LIMIT),
             'nodeVersion': subprocess.check_output(['node', '--version'], text=True).strip()}
    (state/'host-input-proof.json').write_text(json.dumps(value, indent=2)+'\n')
    return consumer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--url', default='')
    parser.add_argument('--sha256', default='')
    parser.add_argument('--fixture-sha256', default='')
    args = parser.parse_args()
    print(prepare(args.root.resolve(), args.url, args.sha256, args.fixture_sha256))


if __name__ == '__main__':
    main()
