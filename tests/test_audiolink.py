import pytest
import audiolink.audiolink as al
import os
from pathlib import Path
import shutil
import uuid


# Config
version = '0.1.0'

file_types = [
    '.aiff',
    '.alac.m4a',
    '.ape',
    '.dsf',
    '.flac',
    '.m4a',
    '.mp3',
    '.mpc',
    '.ogg',
    '.opus',
    '.wav',
    '.wma',
    '.wv',
]


# Global Settings
resource_path = Path('tests/resources')
al_id_suffix = '-al'

known_id = {
    'valid': '0' * 32 + al_id_suffix,
    'invalid_hex': 'z' * 32 + al_id_suffix,
    'invalid_suffix': '0' * 32 + '-zz',
}


# Global Functions
def id_parts(val:str) -> str:
    n = len(al_id_suffix)
    return val[:-n], val[-n:]


def uuid_hex(val:str) -> str:
    try:
        return uuid.UUID(val).hex
    except ValueError:
        return None


# Fixtures
@pytest.fixture
def media_file(tmp_path:Path):
    def _file(file_state:str, file_type:str) -> Path:
        fn = f'{file_state}{file_type}'
        src = resource_path.joinpath(fn)
        dest = tmp_path.joinpath(fn)
        shutil.copy(src, dest)
        return dest

    return _file


@pytest.fixture
def media_file_empty(media_file):
    def _file(file_type:str) -> Path:
        return media_file('empty', file_type)

    return _file


@pytest.fixture
def media_file_full(media_file):
    def _file(file_type:str) -> Path:
        return media_file('full', file_type)

    return _file


@pytest.fixture
def audiolinkid_valid():
    return al.AudiolinkId(known_id.get('valid'))


# Tests
def test_version():
    assert al.__version__ == version


# AudiolinkId
@pytest.mark.parametrize(
    'val, expected',
    [
        (None, True),
        (known_id.get('valid'), True),
        (known_id.get('invalid_hex'), False),
        (known_id.get('invalid_suffix'), False),
    ]
)
def test_AudiolinkId_init(val:str, expected:bool):
    try:
        al.AudiolinkId(val)
        assert True is expected
    except ValueError:
        assert False is expected


@pytest.mark.parametrize(
    'val, expected',
    [
        (None, True),
        (known_id.get('valid'), True),
        (known_id.get('invalid_hex'), False),
        (known_id.get('invalid_suffix'), False),
    ]
)
def test_AudiolinkId_val_setter(val:str, expected:bool):
    try:
        sample = al.AudiolinkId(val)
        sample.val = val
        assert True is expected
    except ValueError:
        assert False is expected


@pytest.mark.parametrize(
    'val',
    [
        None,
        known_id.get('valid'),
    ]
)
def test_AudiolinkId_val_getter(val:str):
    id = al.AudiolinkId(val)
    assert id.val == val


# AudiolinkFile
@pytest.mark.parametrize('file_type', file_types)
def test_AudiolinkFile_init(media_file_empty, file_type):
    fp = media_file_empty(file_type)
    file = al.AudiolinkFile(fp)
    assert file.path == fp


@pytest.mark.parametrize('file_type', file_types)
def test_AudiolinkFile_id_getter(media_file_full, audiolinkid_valid, file_type):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    assert file.id == audiolinkid_valid.val


@pytest.mark.parametrize('file_type', file_types)
def test_AudiolinkFile_id_setter(media_file_empty, audiolinkid_valid, file_type):
    fp = media_file_empty(file_type)
    file = al.AudiolinkFile(fp)
    assert file.id is None
    file.id = audiolinkid_valid
    assert file.id == audiolinkid_valid.val


@pytest.mark.parametrize('file_type', file_types)
def test_AudiolinkFile_id_getter(media_file_full, audiolinkid_valid, file_type):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    assert file.id == audiolinkid_valid.val
    file.delete_audiolink_id_tag()
    assert file.id is None


# AudiolinkFileLink
@pytest.mark.parametrize('file_type', file_types)
def test_AudiolinkFile_link_name(media_file_full, file_type, tmp_path:Path):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    link = al.AudiolinkFileLink(file, tmp_path)
    assert link.link_name == f'{file.id}{file.path.suffix}'


@pytest.mark.parametrize('file_type', file_types)
def test_AudiolinkFile_link_path(media_file_full, file_type, tmp_path:Path):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    link = al.AudiolinkFileLink(file, tmp_path)
    assert link.link_path == tmp_path.joinpath(f'{file.id}{file.path.suffix}')


'''
def test_generate_id():
    id = al.generate_id()
    id_hex, id_suffix = id_parts(id)
    assert id_suffix == al_id_suffix    
    assert id_hex == uuid_hex(id_hex)


@pytest.mark.parametrize(
    'val, expected',
    [
        (known_id['valid'], True),
        (known_id['invalid_hex'], False),
        (known_id['invalid_suffix'], False),
        (None, None),
    ]
)
def test_id_is_valid(val:str, expected:bool):
    assert al.id_is_valid(val) is expected


def test_link_is_valid(tmp_path:Path):
    src_fp = tmp_path / 'src_file'
    dest_fp = tmp_path / 'dest_link'
    not_src_fp = tmp_path / 'not_src_file'
    not_dest_fp = tmp_path / 'not_dest_link'
    
    for fp in [src_fp, not_src_fp, not_dest_fp]:
        with open(fp, 'w'):
            pass

    os.link(src_fp, dest_fp)
    #TODO: add test for ino
    assert al.link_is_valid(src_fp, dest_fp) is True
    assert al.link_is_valid(not_src_fp, dest_fp) is False
    assert al.link_is_valid(src_fp, not_dest_fp) is False    
'''
'''
# AudiolinkId
def test_AudiolinkId_init_valid():
    id = al.AudiolinkId(known_id['valid'])
    assert id.suffix == al_id_suffix
    assert id.__str__() == known_id['valid']
    assert id.__repr__() == known_id['valid']
    assert id.uuid.hex + al_id_suffix == known_id['valid']


@pytest.mark.parametrize('val',
    [
        known_id['invalid_hex'],
        known_id['invalid_suffix']
    ]
)
def test_AudiolinkId_init_invalid(val:str):
    try:
        al.AudiolinkId(val)

    except ValueError:
        assert True
        return
    
    raise AssertionError


def test_AudiolinkId_new():
    id_1 = al.AudiolinkId.new()
    id_2 = al.AudiolinkId.new()
    id_hex, id_suffix = id_parts(str(id_1))
    assert id_hex == uuid_hex(id_hex)
    assert id_suffix == al_id_suffix
    assert id_1 != id_2
    assert str(id_1) != str(id_2)


# AudiolinkFile
#TODO test that a non media file is not loaded
@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_init(media_file_empty, file_type:str):
    fp = media_file_empty(file_type)
    file = al.AudiolinkFile(fp)
    assert file is not None
    assert file.path == fp
    assert file._AudiolinkFile__tag is not None


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_id(media_file_full, file_type:str):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    assert file.id == file._AudiolinkFile__tag.audiolink_id
    assert file.id == known_id['valid']


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_link_name(media_file_full, file_type:str):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    link_name = known_id['valid'] + file.path.suffix
    assert file.link_name == link_name


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_set_id(media_file_empty, file_type:str):
    fp = media_file_empty(file_type)
    file = al.AudiolinkFile(fp)
    assert file._AudiolinkFile__tag.audiolink_id is None
    file.set_id(known_id['valid'])
    del file
    file = al.AudiolinkFile(fp)
    assert file._AudiolinkFile__tag.audiolink_id == known_id['valid']
    # TODO: test setting invalid id
    # TODO: test overwrite


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_set_new_id(media_file_empty, file_type:str):
    fp = media_file_empty(file_type)
    file = al.AudiolinkFile(fp)
    assert file._AudiolinkFile__tag.audiolink_id is None
    file.set_new_id()
    assert file._AudiolinkFile__tag.audiolink_id is not None
    id_hex, id_suffix = id_parts(file._AudiolinkFile__tag.audiolink_id)
    assert id_suffix == al_id_suffix
    assert id_hex == uuid_hex(id_hex)
    # TODO: test overwrite


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_delete_id(media_file_full, file_type:str):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    assert file._AudiolinkFile__tag.audiolink_id is not None
    file.delete_id()
    assert file._AudiolinkFile__tag.audiolink_id is None


# set_id_from_link_name


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_create_link(media_file_full, file_type:str, tmp_path:Path):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    dest_fp = tmp_path / file.link_name
    assert dest_fp.exists() is False
    #TODO: validate_id 
    file.create_link(tmp_path)
    assert dest_fp.exists() is True
    assert dest_fp.name == file.id + file.path.suffix
    assert file.get_link_status(tmp_path) == 'active'
    #TODO: test that they share the same ino


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_delete_link(media_file_full, file_type:str, tmp_path:Path):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    dest_fp = tmp_path / file.link_name
    file.create_link(tmp_path)
    assert dest_fp.exists() is True
    file.delete_link(tmp_path)
    assert dest_fp.exists() is False
'''