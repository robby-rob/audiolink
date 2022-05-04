import pytest
import audiolink.audiolink as al
import uuid
from pathlib import Path
import shutil
import os

def test_version():
    assert al.__version__ == '0.1.0'

staging_path = Path('tests/.staging')
resource_path = Path('tests/resources')

def setup():
    staging_files = (_ for _ in staging_path.glob('**/*') if not _.is_dir())
    resource_files = (_ for _ in resource_path.glob('**/*') if not _.is_dir())

    for file in staging_files:
        file.unlink()

    ## make files and links dir if not exist

    for file in resource_files:
        shutil.copy(file, staging_path.joinpath(f'files/{file.name}'))


def test_generate_id():
    id = al.generate_id()
    id_hex = id[:-3]
    id_suffix = id[-3:]

    assert id_suffix == '-al'

    try:
        assert id_hex == uuid.UUID(id_hex).hex
    except ValueError:
        raise AssertionError


def test_id_is_valid():
    id = '00000000000000000000000000000000-al'
    assert al.id_is_valid(id) == True
    assert al.id_is_valid(id[:-3]) == False
    assert al.id_is_valid('z' + id[1:]) == False
    assert al.id_is_valid(None) == None


def test_link_is_valid():
    src0 = staging_path.joinpath('files/link_source0')
    src1 = staging_path.joinpath('files/link_source1')
    dest = staging_path.joinpath('links/link_dest')

    with open(src0, 'w'):
        pass

    with open(src1, 'w'):
        pass

    os.link(src0, dest)
    
    assert al.link_is_valid(src0, dest) == True
    assert al.link_is_valid(src1, dest) == False


def test_audiolinkFile():
    fp = staging_path.joinpath('files/empty.mp3')
    file = al.AudiolinkFile(fp)
    assert file.id == None
    assert file.link_name == None

    id = '00000000000000000000000000000000-al'
    file.set_id(id)
    link_file = id + fp.suffix
    assert file.id == id
    assert file.link_name == Path(link_file)

    dest = staging_path.joinpath('links')
    file.create_link(dest)
    link_fp = dest.joinpath(link_file)
    assert link_fp.name == link_file
    assert al.link_is_valid(fp, link_fp)

    file.delete_id()
    assert file.id == None

    file.set_new_id()
    assert file.id != None
    assert al.id_is_valid(file.id) == True



setup()
test_generate_id()
test_id_is_valid()
test_link_is_valid()
test_audiolinkFile()