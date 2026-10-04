"""Temporary opaque inputs cannot silently change host source or input mode."""
import io
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_qualification_host import HTTPSOnly, choose, manifest  # noqa: E402


@pytest.mark.parametrize('inputs', [('', '', ''), ('https://example/x', '', ''),
    ('https://example/x', 'a'*64, 'b'*64), ('', 'a'*64, 'b'*64),
    ('http://example/x', 'a'*64, ''), ('https://user:pass@example/x', 'a'*64, ''),
    ('https://example/x#secret', 'a'*64, ''), ('', '', 'main')])
def test_bad_or_ambiguous_inputs_refuse(inputs):
    with pytest.raises(ValueError):
        choose(*inputs)


def test_exact_input_modes_remain_explicit():
    assert choose('https://example/artifact.tgz', 'a'*64, '') == 'https'
    assert choose('', '', 'a'*64) == 'fixture'


def test_redirect_rejects_http_before_request():
    with pytest.raises(ValueError):
        HTTPSOnly().redirect_request(None, None, 302, '', {}, 'http://example/leak')


def test_reviewed_real_opaque_package_identity():
    root = Path(__file__).resolve().parents[1]
    value = manifest(root / '.qualification-inputs/host-54e539.tgz')
    assert value['name'] == '@amplifier/unified-host' and value['version'] == '0.1.0'


@pytest.mark.parametrize('name,kind', [('../escape', None), ('package/link', tarfile.SYMTYPE),
    ('package/manifest', tarfile.FIFOTYPE)])
def test_unsafe_archive_members_refuse_before_install(tmp_path, name, kind):
    archive = tmp_path / 'host.tgz'
    with tarfile.open(archive, 'w:gz') as tar:
        item = tarfile.TarInfo(name)
        if kind:
            item.type = kind
            tar.addfile(item)
        else:
            item.size = 1
            tar.addfile(item, io.BytesIO(b'x'))
    with pytest.raises(ValueError):
        manifest(archive)
