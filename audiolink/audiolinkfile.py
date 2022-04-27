from mediafile import MediaFile
from mediafile import MediaField
from mediafile import MP3DescStorageStyle
from mediafile import MP4StorageStyle
from mediafile import StorageStyle
from mediafile import ASFStorageStyle
from pathlib import Path
import uuid
import os


__all__ = [
    'AudiolinkFile',
    'AudiolinkIdExistsError'
]


mediafield = MediaField(
    MP3DescStorageStyle(u'AUDIOLINK_ID'),
    MP4StorageStyle('----:com.apple.iTunes:Audiolink Id'),
    StorageStyle('AUDIOLINK_ID'),
    ASFStorageStyle('Audiolink/Id'),
)

def generate_id() -> str:
    """ Generates a new Audiolink Id.
        UUID hex + -al suffix to distinguish from other ids
    """ 
    id = uuid.uuid4().hex
    return f'{id}-al'

def id_is_valid(val) -> bool:
    """ Tests if val is a proper Audiolink Id.
    """
    if val is None:
        return None

    try:
        id_parts = val.split('-')
        uuid.UUID(id_parts[0])
        return id_parts[1] == 'al'

    except:
        return False


def link_is_valid(src, dest) -> bool:
    #TODO: Test that src and des are on same fs

    src_ino = Path(src).stat().st_ino
    dest_ino = Path(dest).stat().st_ino
    return src_ino == dest_ino


class _MediaFile(MediaFile):
    """ Class for adding Audiolink Id field. Avoids conflicts with other instances of MediaFile
    """
    def __init__(self, filething, id3v23=False) -> None:
        super().__init__(filething, id3v23)

_MediaFile.add_field('audiolink_id', mediafield)


class AudiolinkIdExistsError(Exception):
    """File has existing Audiolink Id.
    """
    def __init__(self, id, file) -> None:
        #TODO: print msg
        msg = f'Existing Audiolink Id "{id}" on file "{file}"'
        Exception.__init__(self, id, file)


class AudiolinkFile:
    """ Class for Audiolink Id operations on media files.
    """
    def __init__(self, fp) -> None:
        self.path = Path(fp)
        self.__tag = _MediaFile(self.path)


    @property
    def id(self) -> str:
        return self.__tag.audiolink_id


    @property
    def link_name(self) -> Path:
        return Path(self.id).with_suffix(self.path.suffix)


    def create_link(self, dest, overwrite=False) -> None:
        """ Creates a hard link in dest path with Audiolink Id as file name.
        """
        link_fp = Path(dest).joinpath(self.link_name)

        if not overwrite:
            if link_fp.exists():
                raise FileExistsError('Link already exists in dest.')

        os.link(self.path, link_fp)


    def delete_id(self) -> None:
        """ Removes Audiolink Id tag from file.
        """
        for style in mediafield.styles(self.__tag.mgfile):
            style.delete(self.__tag.mgfile)
        
        self.__tag.save()


    def set_id(self, val, overwrite=False) -> None:
        """ Sets Audiolink Id tag with a given value.
        """
        if not overwrite:
            if self.id is not None:
                raise AudiolinkIdExistsError(self.id, self.path)

        if not id_is_valid(val):
            raise ValueError(f'"{val}" is not a valid Audiolink Id.')

        self.__tag.audiolink_id = val
        self.__tag.save()


    def set_id_from_link_name(self, overwrite=False) -> None:
        """ Sets Audiolink Id tag using file name.
        """
        self.set_id(self.path.stem, overwrite=overwrite)


    def set_new_id(self, overwrite=False) -> None:
        """ Sets Audiolink Id tag using newly generated id.
        """
        id = generate_id()
        self.set_id(id, overwrite=overwrite)
        