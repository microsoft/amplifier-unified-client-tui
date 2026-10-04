"""Release candidates fail closed on wrong source, target, or evidence."""
import copy
import json
import runpy
from pathlib import Path

import pytest

API = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/release_manifest.py'))


def fixture(directory, commit='a' * 40):
    directory.mkdir()
    filename = 'amplifier_unified_client_tui-0.5.0rc2-py3-none-macosx_11_0_arm64.whl'
    wheel = directory / filename
    wheel.write_bytes(b'synthetic wheel fixture, never a released artifact')
    qualification = {'status': 'qualified', 'installedIsolation': True, 'privacy': True,
        'actualPTY': True, 'testedPython': '3.13.11', 'testedNode': '22.20.0',
        'testedOS': 'macOS 26.0', 'minimumGlibc': None}
    identity = {'filename': filename, 'bytes': wheel.stat().st_size,
        'sha256': API['digest'](wheel), 'target': API['target']('py3-none-macosx_11_0_arm64')}
    proof = {'format': API['FORMAT'] + '.qualification', 'schemaVersion': 1,
        'package': {'name': API['PACKAGE'], 'version': '0.5.0rc2'},
        'source': {'repository': API['REPOSITORY'], 'commit': commit},
        'compatibility': copy.deepcopy(API['COMPATIBILITY']), 'wheel': identity, 'qualification': qualification,
        'checks': {name: 'passed' for name in API['CHECKS']},
        'checkLogHashes': {name: 'b' * 64 for name in API['CHECKS']},
        'limits': ['Synthetic test data only']}
    evidence_name = filename.removesuffix('.whl') + '.qualification.json'
    API['write'](directory / evidence_name, proof)
    manifest = {'format': API['FORMAT'], 'schemaVersion': 1, 'package': proof['package'],
        'source': proof['source'], 'compatibility': proof['compatibility'],
        'artifacts': [{**identity, 'qualification': {**qualification,
            'evidenceFilename': evidence_name, 'evidenceSha256': API['digest'](directory / evidence_name)}}]}
    API['write'](directory / 'manifest.json', manifest)
    return manifest


@pytest.mark.parametrize('change', [
    lambda m: m.update(schemaVersion=True),
    lambda m: m['package'].update(name='amplifier-app-tui'),
    lambda m: m['source'].update(commit='main'),
    lambda m: m['compatibility'].update(ahpVersions=['connected-protocol-v1']),
    lambda m: m['artifacts'][0].update(filename='../wheel.whl'),
    lambda m: m['artifacts'][0].update(bytes=True),
    lambda m: m['artifacts'][0]['target'].update(arch='x86_64'),
    lambda m: m['artifacts'][0]['qualification'].update(actualPTY=False),
    lambda m: m['artifacts'][0]['qualification'].update(testedNode='20.0.0'),
    lambda m: m['artifacts'][0]['qualification'].update(testedPython='3.10.9'),
    lambda m: m['artifacts'][0]['qualification'].update(evidenceFilename='https://other/evidence.json'),
    lambda m: m['artifacts'].append(copy.deepcopy(m['artifacts'][0])),
    lambda m: m['artifacts'][0].update(url='https://other/wheel.whl'),
])
def test_invalid_newest_candidate_never_passes(tmp_path, change):
    manifest = fixture(tmp_path / 'candidate')
    change(manifest)
    with pytest.raises(ValueError):
        API['validate'](manifest)


def test_exact_asset_and_evidence_binding(tmp_path):
    manifest = fixture(tmp_path / 'candidate')
    API['verify_assets'](manifest, tmp_path / 'candidate')
    wheel = tmp_path / 'candidate' / manifest['artifacts'][0]['filename']
    wheel.write_bytes(wheel.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='bytes/hash'):
        API['verify_assets'](manifest, tmp_path / 'candidate')


@pytest.mark.parametrize('change', [
    lambda p: p['source'].update(commit='c' * 40),
    lambda p: p['checks'].update(**{'installed-terminal': 'failed'}),
    lambda p: p['qualification'].update(privacy=False),
    lambda p: p.update(format='legacy.receipt'),
    lambda p: p['checkLogHashes'].update(**{'installed-isolation': 'missing'}),
])
def test_rehashed_but_wrong_evidence_refuses(tmp_path, change):
    manifest = fixture(tmp_path / 'candidate')
    q = manifest['artifacts'][0]['qualification']
    evidence = tmp_path / 'candidate' / q['evidenceFilename']
    proof = json.loads(evidence.read_text())
    change(proof)
    API['write'](evidence, proof)
    q['evidenceSha256'] = API['digest'](evidence)
    with pytest.raises(ValueError):
        API['verify_assets'](manifest, tmp_path / 'candidate')


def test_assembly_rejects_mixed_source_and_duplicate_target_before_output(tmp_path):
    fixture(tmp_path / 'first')
    fixture(tmp_path / 'second', 'c' * 40)
    inputs = [tmp_path / name / 'manifest.json' for name in ['first', 'second']]
    with pytest.raises(ValueError, match='Mixed source'):
        API['assemble'](inputs, tmp_path / 'release')
    assert not (tmp_path / 'release').exists()
    fixture(tmp_path / 'third')
    with pytest.raises(ValueError, match='Duplicate'):
        API['assemble']([inputs[0], tmp_path / 'third/manifest.json'], tmp_path / 'release')
    assert not (tmp_path / 'release').exists()


def test_one_qualified_fragment_can_be_assembled_and_reverified(tmp_path):
    original = fixture(tmp_path / 'candidate')
    result = API['assemble']([tmp_path / 'candidate/manifest.json'], tmp_path / 'release')
    assert result == original
    API['verify_assets'](API['load'](tmp_path / 'release/manifest.json'), tmp_path / 'release')


@pytest.mark.parametrize('content', [b'{"schemaVersion":1,"schemaVersion":2}', b' ' * (128 * 1024 + 1)])
def test_duplicate_keys_and_oversized_documents_refuse(tmp_path, content):
    path = tmp_path / 'manifest.json'
    path.write_bytes(content)
    with pytest.raises(ValueError):
        API['load'](path)


def test_schema_identity_matches_public_contract():
    schema = json.loads((Path(__file__).resolve().parents[1] / 'release/manifest-v1.schema.json').read_text())
    assert schema['properties']['format']['const'] == API['FORMAT']
    assert schema['properties']['compatibility']['const'] == API['COMPATIBILITY']
    assert schema['properties']['artifacts']['maxItems'] == API['MAX_ARTIFACTS']
