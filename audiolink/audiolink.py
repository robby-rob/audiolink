from mediafile import MediaFile
from mediafile import MediaField
from mediafile import MP3DescStorageStyle
from mediafile import MP4StorageStyle
from mediafile import StorageStyle
from mediafile import ASFStorageStyle
from pathlib import Path
import uuid
import os

__version__ = '0.1.0'

__all__ = [
    'AudiolinkId',
    'AudiolinkFile',
    'AudiolinkFolder'
]

file_types = [
    '.aiff',
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

al_id_suffix = '-al'

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


class AudiolinkId:
    """ Class for Audiolink Id.
    """
    suffix = '-al'

    def __init__(self, val:str) -> None:
        n = len(AudiolinkId.suffix)
        val = str(val)
        if val[-n:] != AudiolinkId.suffix:
            raise ValueError(f'must end with "{AudiolinkId.suffix}"')
        
        self.uuid = uuid.UUID(val[:-n])
    
    def __str__(self) -> str:
        return self.uuid.hex + AudiolinkId.suffix

    def __repr__(self) -> str:
        return self.uuid.hex + AudiolinkId.suffix

    @classmethod
    def new(cls):
        """ Creates instance with newly generated id
        """
        return AudiolinkId(uuid.uuid4().hex + cls.suffix)


class AudiolinkFile:
    """ Class for Audiolink operations on media files.
    """
    def __init__(self, fp) -> None:
        self.path = Path(fp)
        self.__tag = _MediaFile(self.path)


    @property
    def id(self) -> str:
        return self.__tag.audiolink_id


    @property
    def link_name(self) -> str:
        if self.id:
            return str(Path(self.id).with_suffix(self.path.suffix))


    def get_link_status(self, dir) -> str:
        """ Checks the dir for a link file and returns the status.
        """
        fp = Path(dir) / self.link_name
        
        if not fp.exists():
            return None

        if fp.stat().st_ino == self.path.stat().st_ino:
            return 'active'
        
        elif AudiolinkFile(fp).id == self.id:
            return 'inactive'

        raise Exception


    def create_link(self, dest:str, overwrite=False) -> None:
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


    def delete_link(self, dest:str) -> None:
        """ Removes hard link in dest path if exists with file Audiolink Id.
            If a file path is given, the file will be checked, if a dir is given, the filename will be the Audiolink Id
        """
        link_fp = Path(dest)
        
        if link_fp.is_dir():
            link_fp = link_fp.joinpath(self.link_name)

        if link_fp.exists() and self.get_link_status(link_fp) == 'active':
            link_fp.unlink()


    def set_id(self, val:str, overwrite=False) -> None:
        """ Sets Audiolink Id tag with value.
        """
        if not overwrite:
            if self.id is not None:
                raise AudiolinkIdExistsError(self.id, self.path)

        if type(val) != AudiolinkId:
            val = AudiolinkId(val)

        self.__tag.audiolink_id = str(val)
        self.__tag.save()


    def set_new_id(self, overwrite=False) -> None:
        """ Sets Audiolink Id tag with newly generated id.
        """
        self.set_id(AudiolinkId.new(), overwrite=overwrite)

'''
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
        self.path_stats = [analyze(fp) for fp in Path.glob(self.path, pattern) if fp.suffix in file_types]


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
'''