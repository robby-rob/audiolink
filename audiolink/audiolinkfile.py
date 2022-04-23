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
        self.tag = _MediaFile(self.path)


    @property
    def id(self) -> str:
        return self.tag.audiolink_id


    @staticmethod
    def id_is_valid(val) -> bool:
        """ Tests if val is a proper Audiolink Id.
        """
        # 'UUID Hex' + '_al' suffix to distinguish from other ids
        try:
            id_parts = val.split('_')
            uuid.UUID(id_parts[0])
            return id_parts[1] == 'al'
    
        except:
            return False


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
        for style in mediafield.styles(self.tag.mgfile):
            style.delete(self.tag.mgfile)
        
        self.tag.save()


    def set_id(self, val, overwrite=False) -> None:
        """ Sets Audiolink Id tag with a given value.
        """
        if not overwrite:
            if self.id is not None:
                raise AudiolinkIdExistsError(self.id, self.path)

        if not AudiolinkFile.id_is_valid(val):
            raise ValueError(f'"{val}" is not a valid Audiolink Id.')

        self.tag.audiolink_id = val
        self.tag.save()


    def set_id_from_link_name(self, overwrite=False) -> None:
        """ Sets Audiolink Id tag using file name.
        """
        self.set_id(self.path.stem, overwrite=overwrite)


    def set_new_id(self, overwrite=False) -> None:
        """ Sets Audiolink Id tag using newly generated id.
        """
        id = f'{uuid.uuid4().hex}_al'
        self.set_id(id, overwrite=overwrite)
        