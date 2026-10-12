"""Install the reviewed independent Host archive in a fresh qualification consumer."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture-sha256', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    archive = root / '.qualification-inputs/host-796a15.tgz'
    provenance = json.loads((archive.parent / 'provenance.json').read_text())
    if (hashlib.sha256(archive.read_bytes()).hexdigest() != args.fixture_sha256
            or provenance['sha256'] != args.fixture_sha256
            or archive.stat().st_size != provenance['bytes']):
        raise ValueError('Reviewed independent Host archive changed')
    destination = root / '.state/qualification-host'
    destination.mkdir()
    (destination / 'package.json').write_text(json.dumps({
        'name': 'managed-terminal-host-consumer', 'version': '0.0.0', 'private': True
    }) + '\n')
    subprocess.run(['npm', 'install', '--prefix', str(destination), '--global=false',
                    '--workspaces=false', '--ignore-scripts', str(archive)], check=True)


if __name__ == '__main__':
    main()
