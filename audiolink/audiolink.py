from typing import Iterable
from mediafile import MediaFile
from mediafile import MediaField
from mediafile import MP3DescStorageStyle
from mediafile import MP4StorageStyle
from mediafile import StorageStyle
from mediafile import ASFStorageStyle
from mediafile import TYPES
from pathlib import Path
import uuid
import os

__version__ = '0.1.0'

__all__ = [
    'AudiolinkFile',
    'AudiolinkFolder'
]

_extensions = tuple(f'.{k}' for k in TYPES.keys())

mediafield = MediaField(
    MP3DescStorageStyle(u'AUDIOLINK_ID'),
    MP4StorageStyle('----:com.apple.iTunes:Audiolink Id'),
    StorageStyle('AUDIOLINK_ID'),
    ASFStorageStyle('Audiolink/Id'),
)


def generate_id() -> str:
    """ Generates a new Audiolink Id.
        UUID_hex + -al suffix to distinguish from other ids
    """ 
    id = uuid.uuid4().hex
    return f'{id}-al'


def id_is_valid(val:str) -> bool:
    """ Tests if val is a proper Audiolink Id.
    """
    if val is None:
        return None

    try:
        uuid.UUID(val[:-3])
        return val[-3:] == '-al'

    except:
        return False


def link_is_valid(src, dest) -> bool:
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
        if self.id:
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


class AudiolinkFolder:
    def __init__(self, path, link_path=None):
        self.path = Path(path) #.resolve()
        self.link_path = Path(link_path)
        self.scan_folder()


    def scan_folder(self, recursive=True) -> list:
        def analyze(fp) -> dict:
            try:
                af = AudiolinkFile(fp)
                id = af.id
                valid_id = id_is_valid(id) if id is not None else None
                link_fp = self.link_path.joinpath(af.link_name)
                linked = link_is_valid(fp, link_fp) if valid_id else None

                return {
                    'fp': fp,
                    'id': id,
                    'valid_id': valid_id,
                    'linked': linked,
                }
            
            except Exception as e:
                print(e)


        pattern = '**/*' if recursive else '*'
        self.path_stats = [analyze(fp) for fp in Path.glob(self.path, pattern) if fp.suffix in _extensions]


    def _query_gen(self, state=None) -> Iterable:
        if state == 'missing':
            return (_['fp'] for _ in self.path_stats if _['valid_id'] is None)
        elif state == 'invalid':
            return (_['fp'] for _ in self.path_stats if _['valid_id'] is False)
        elif state == 'valid':
            return (_['fp'] for _ in self.path_stats if _['valid_id'] is True)
        elif state == 'linked':
            return (_['fp'] for _ in self.path_stats if _['valid_link'] is True)

        return (_['fp'] for _ in self.path_stats)  # any


    def file_list(self, state='any') -> list:
        """ Returns a list of files
            -------
            Options:
              - state [any (default), invalid, linked, missing]
        """
        return list(self._query_gen(state=state))


    def set_ids(self, state='missing', overwrite=False, verbose=True) -> None:
        """ Sets Audiolink Id field on files.
            -------
            Options:
              - state [missing (default), any, invalid]
              - ids [new (default), filename]
              - overwright [True (default), False]
              - verbose = [True (default), False]
        """
        files = self._fp_id_state_gen(state=state)

        for fp in files:
            try:
                af = AudiolinkFile(fp)
                af.set_new_id(overwrite=overwrite)

                #if id_source == 'new':
                #elif id_source == 'filename':
                #    af.set_id_from_link_name(overwrite=overwrite)

                if verbose:
                    print(f'"{af.id}" set on "{af.path}"')

            except Exception as e:
                print(e)

        self.scan_folder()


    def delete_ids(self, state='any', verbose=True) -> None:
        """ Removes Audiolink Id field on files.
            -------
            Options:
              - state [any (default), invalid, missing]
              - verbose = [True (default), False]
        """
        files = self._fp_id_state_gen(state=state)
        print(f'Warning: This will delete ids for files in "{self.path}".')
        resp = input('Enter Y to proceed:')

        if resp != 'Y':
            return

        for fp in files:
            try:
                af = AudiolinkFile(fp)
                af.delete_id()

                if verbose:
                    print(f'"{af.id}" removed from "{af.path}"')

            except Exception as e:
                print(e)
        
        self.scan_folder()


    def create_links(self, overwrite=True, verbose=True):
        if self.link_path is None:
            print('link_path is not set')
            return

        files = self._query_gen(state='valid')
        for fp in files:
            try:
                af = AudiolinkFile(fp)
                af.create_link(self.link_path, overwrite=overwrite)
                
                if verbose:
                    print(f'"{af.id}" link created for "{af.path}"')

            except Exception as e:
                print(e)

        self.scan_folder()
