import pytest
import audiolink.audiolink as al
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


@pytest.fixture
def audiolink_folder_empty(media_file_empty):
    for ft in file_types:
        media_file_empty(ft)

@pytest.fixture
def audiolink_folder(media_file_full, media_file_empty):
    for ft in file_types:
        media_file_full(ft)
        media_file_empty(ft)

    return


# Tests
# General
def test_version():
    assert al.__version__ == version


# AudiolinkId
class TestAudiolinkId:
    class TestClass:
        def test_AudiolinkId_suffix(self):
            assert al.AudiolinkId.suffix == al_id_suffix

        def test_AudiolinkId_val_new(self):
            id = al.AudiolinkId.new().val
            n = len(al_id_suffix)
            assert id[-n:] == al_id_suffix

            try:
                assert id[:-n] == uuid.UUID(id[:-n]).hex
            
            except ValueError:
                assert False

    @pytest.mark.parametrize(
        'val, expected',
        [
            (None, True),
            (known_id.get('valid'), True),
            (known_id.get('invalid_hex'), False),
            (known_id.get('invalid_suffix'), False),
        ]
    )
    class TestInstance:
        def test_AudiolinkId_init(self, val:str, expected:bool):
            try:
                al.AudiolinkId(val)
                assert True is expected

            except ValueError:
                assert False is expected

        def test_AudiolinkId_val_getter(self, val:str, expected:bool):
            try:
                id = al.AudiolinkId(val)
                assert id.val == val
            except ValueError:
                assert False is expected

        def test_AudiolinkId_val_setter(self, val:str, expected:bool):
            try:
                id = al.AudiolinkId(val)
                id.val = val
                assert True is expected
            except ValueError:
                assert False is expected


# AudiolinkFile
@pytest.mark.parametrize('file_type', file_types)
class TestAudiolinkFile:
    def test_AudiolinkFile_init(self, media_file_empty, file_type):
        fp = media_file_empty(file_type)
        file = al.AudiolinkFile(fp)
        assert file.path == fp

    def test_AudiolinkFile_id_getter(self, media_file_full, file_type):
        fp = media_file_full(file_type)
        file = al.AudiolinkFile(fp)
        assert file.id == known_id.get('valid')

    def test_AudiolinkFile_id_setter(self, media_file_empty, file_type, audiolinkid_valid):
        fp = media_file_empty(file_type)
        file = al.AudiolinkFile(fp)
        assert file.id is None
        file.id = audiolinkid_valid
        assert file.id == known_id.get('valid')

    def test_AudiolinkFile_id_deleter(self, media_file_full, file_type):
        fp = media_file_full(file_type)
        file = al.AudiolinkFile(fp)
        assert file.id == known_id.get('valid')
        del file.id
        assert file.id is None


# AudiolinkFileLink
@pytest.mark.parametrize('file_type', file_types)
class TestAudiolinkFileLink:
    #TODO: file and path setter and getter, link_status, edge cases

    def test_AudiolinkFileLink_link_name(self, media_file_full, file_type, tmp_path:Path):
        fp = media_file_full(file_type)
        file = al.AudiolinkFile(fp)
        link = al.AudiolinkFileLink(file, tmp_path)
        assert link.link_name == f'{file.id}{file.path.suffix}'

    def test_AudiolinkFileLink_link_path(self, media_file_full, file_type, tmp_path:Path):
        fp = media_file_full(file_type)
        file = al.AudiolinkFile(fp)
        link = al.AudiolinkFileLink(file, tmp_path)
        assert link.link_path == tmp_path.joinpath(f'{file.id}{file.path.suffix}')

    def test_AudiolinkFileLink_create_link(self,  media_file_full, file_type, tmp_path:Path):
        fp = media_file_full(file_type)
        file = al.AudiolinkFile(fp)
        link = al.AudiolinkFileLink(file, tmp_path)
        link_fp = tmp_path.joinpath(f'{file.id}{file.path.suffix}')
        assert not link_fp.exists()
        link.create_link()
        assert link_fp.exists()

    def test_AudiolinkFileLink_delete_link(self,  media_file_full, file_type, tmp_path:Path):
        fp = media_file_full(file_type)
        file = al.AudiolinkFile(fp)
        link = al.AudiolinkFileLink(file, tmp_path)
        link_fp = tmp_path.joinpath(f'{file.id}{file.path.suffix}')
        link.create_link()
        assert link_fp.exists()
        link.delete_link()
        assert not link_fp.exists()


#AudiolinkFolder
class TestAudiolinkFolder:
    def test_AudiolinkFolder_path(self, tmp_path:Path):
        al_folder = al.AudiolinkFolder()
        al_folder.path = str(tmp_path)
        assert al_folder.path == tmp_path

    def test_AudiolinkFolder_link_path(self, tmp_path:Path):
        al_folder = al.AudiolinkFolder()
        al_folder.link_path = str(tmp_path)
        assert al_folder.link_path == tmp_path

    def test_AudiolinkFolder_path_conflict(self, tmp_path:Path):
        al_folder = al.AudiolinkFolder()
        al_folder.link_path = str(tmp_path)

        try:
            al_folder.path = str(tmp_path)
            assert False
        except ValueError:
             assert True
        
        try:
            al_folder.path = str(tmp_path.parent)
            assert False
        except ValueError:
             assert True

    def test_AudiolinkFolder_link_path_conflict(self, tmp_path:Path):
        al_folder = al.AudiolinkFolder()
        al_folder.path = str(tmp_path)
        
        try:
            al_folder.link_path = str(tmp_path)
            assert False
        except ValueError:
             assert True
        
        try:
            al_folder.link_path = str(tmp_path.joinpath('subdir'))
            assert False
        except ValueError:
            assert True

    def test_AudiolinkFolder_scan(self, audiolink_folder, tmp_path:Path):
        #audiolink_folder()
        pass

    def test_AudiolinkFolder_set_ids(self):
        pass

    def test_AudiolinkFolder_delete_ids(self):
        pass

    def test_AudiolinkFolder_create_links(self):
        pass

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