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
    _suffix = '-al'

    def __init__(self, val=None) -> None:
        self.val = val

    '''
    def __str__(self) -> str:
        return self.val

    def __repr__(self) -> str:
        return self.val
    '''

    @property
    def val(self) -> str:
        if self._uuid is None:
            return None
        
        return f'{self._uuid.hex}{AudiolinkId.suffix}' 

    @val.setter
    def val(self, id:str) -> None:
        if id is None:
            self._uuid = None
            return

        id = str(id)
        suffix = AudiolinkId.suffix
        n = len(suffix)

        if id[-n:] != suffix:
            raise ValueError(f'must end with "{suffix}"')

        self._uuid = uuid.UUID(id[:-n])

    '''
    def set_new(self) -> None:
        self._uuid = uuid.uuid4().hex
    '''

    @classmethod
    @property
    def suffix(cls):
        return cls._suffix

    @classmethod
    def new(cls):
        """ Creates instance with newly generated id
        """
        return AudiolinkId(uuid.uuid4().hex + cls.suffix)

class AudiolinkFile:
    """ Class for Audiolink operations on media files.
        fp can be changed by using cls.fp = fp
    """
    def __init__(self, fp:str) -> None:
        self.path = fp

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, fp:str) -> None:
        self._path = Path(fp)
        self._tag = _MediaFile(self.path)

    @property
    def id(self) -> str:
        return self._tag.audiolink_id

    @id.setter
    def id(self, audiolinkid) -> None:
        '''
        if not issubclass(id, AudiolinkId):
            raise ValueError('id is not of class AudiolinkId')
        '''
        try:
            id = audiolinkid.val

        except AttributeError:
            raise ValueError('id is not of class AudiolinkId')
        
        if id is None:
            raise ValueError('AudiolinkId has no value')

        self._tag.audiolink_id = str(id)
        self._tag.save()

    def delete_audiolink_id_tag(self) -> None:
        """ Removes Audiolink Id tag from file.
        """
        for style in mediafield.styles(self._tag.mgfile):
            style.delete(self._tag.mgfile)

        self._tag.save()


class AudiolinkFileLink:
    """ Class for Audiolink operations on media files.
    """
    def __init__(self, file:AudiolinkFile, dest:str) -> None:
        self.file = file
        self.dest = dest

    @property
    def file(self) -> AudiolinkFile:
        return self._file

    @file.setter
    def file(self, file) -> None:
        if not isinstance(file, AudiolinkFile):
            raise ValueError('file is not of class AudiolinkFile')

        self._file = file

    @property
    def dest(self) -> Path:
        return self._dest

    @dest.setter
    def dest(self, dest:str) -> None:
        link_dir = Path(dest)

        if not link_dir.is_dir():
            raise ValueError('dest is not a dir')

        self._dest = link_dir
        
    @property
    def link_name(self) -> str:
        return f'{self.file.id}{self.file.path.suffix}'

    @property
    def link_path(self) -> Path:
        return self.dest.joinpath(self.link_name)

    @property
    def link_status(self) -> str:
        """ Checks the dir for a link file and returns the status.
        """
        if not self.link_path.exists():
            return None

        if self.link_path.stat().st_ino == self.file.path.stat().st_ino:
            return 'active'
        
        elif AudiolinkFile(self.link_path).id == self.file.id:
            return 'inactive'

        return 'conflict'

    def create_link(self, overwrite:bool = False) -> None:
        """ Creates a hard link in dest path with Audiolink Id as file name.
        """
        if self.link_status is None:
            pass

        elif self.link_status == 'active':
            return
        
        elif self.link_status == 'inactive':
            if not overwrite:
                raise FileExistsError('file exists in dest with link name and id')

        else:
            raise FileExistsError('file exists in dest with link name')

        os.link(self.file.path, self.link_path)

    def delete_link(self, force:bool = True) -> None:
        """ Removes hard link in dest path if exists with file Audiolink Id.
        """
        if self.link_status is None:
            return #TODO: Warning no link detected

        elif self.link_status == 'active':
            self.link_path.unlink()

        elif self.link_status == 'inactive':
            if not force:
                raise FileExistsError('file exists in dest with link name and id')
        
        else:
            raise FileExistsError('file exists in dest with link name')



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