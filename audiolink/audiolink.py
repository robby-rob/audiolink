from mediafile import MediaFile
from mediafile import MediaField
from mediafile import MP3DescStorageStyle
from mediafile import MP4StorageStyle
from mediafile import StorageStyle
from mediafile import ASFStorageStyle
from mediafile import UnreadableFileError
from pathlib import Path
import uuid
import os

__version__ = '0.1.0'

__all__ = [
    'AudiolinkId',
    'AudiolinkFile',
    'AudiolinkFileLink',
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


class AudiolinkId:
    """ Class for Audiolink Id.
    """
    _suffix = '-al'

    def __init__(self, val:str = None) -> None:
        self._uuid = None
        self.val = val

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
        n = len(AudiolinkId.suffix)

        if id[-n:] != AudiolinkId.suffix:
            raise ValueError(f'must end with "{AudiolinkId.suffix}"')

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
    def __init__(self, fp:str = None) -> None:
        self._path = None
        self._tag = None
        self.path = fp

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, fp:str) -> None:
        if fp is None:
            self._path = None
            self._tag = None
            return

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

    @id.deleter
    def id(self) -> None:
        """ Removes Audiolink Id tag from file.
        """
        #TODO: explore only using specific file style rather than all
        for style in mediafield.styles(self._tag.mgfile):
            style.delete(self._tag.mgfile)

        self._tag.save()


class AudiolinkFileLink:
    """ Class for Audiolink operations on media files.
    """
    def __init__(self, file:AudiolinkFile = None, dest:str = None) -> None:
        self._file = None
        self._dest = None
        
        self.file = file
        self.dest = dest

    @property
    def file(self) -> AudiolinkFile:
        return self._file

    @file.setter
    def file(self, file) -> None:
        if file is None:
            self._file = None
            return

        if not isinstance(file, AudiolinkFile):
            raise ValueError('file is not of class AudiolinkFile')

        self._file = file

    @property
    def dest(self) -> Path:
        return self._dest

    @dest.setter
    def dest(self, dest:str) -> None:
        if dest is None:
            self._dest = None
            return

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


class AudiolinkFolder:
    """ Class for bulk Audiolink operations for files in a folder.
    """
    def __init__(self, path:str = None, link_path:str = None) -> None:
        self._path = None
        self._link_path = None

        self.path = path
        self.link_path = link_path

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, path:str) -> None:
        if path is None:
            self._path = None
            return

        new_path = Path(path)

        #path cannot be a parent of link_path or subdir of link_path
        if self.link_path is not None and (self.link_path.is_relative_to(new_path) or new_path.is_relative_to(self.link_path)):
            raise ValueError('path cannot be a parent or subdir of link_path')

        self._path = new_path

    @property
    def link_path(self) -> Path:
        return self._link_path

    @link_path.setter
    def link_path(self, path:str) -> Path:
        #TODO link_path must be on the same volume as path
        if path is None:
            self._link_path = None
            return
        
        new_path = Path(path)

        #link_path cannot be a subdir of path
        if self.path is not None and new_path.is_relative_to(self.path):
            raise ValueError('link_path cannot be a subdir of path')

        self._link_path = new_path

    def scan(self) -> None:
        #TODO: look into warning for softlinks if found

        al_file = AudiolinkFile()
        al_id = AudiolinkId()
        al_link = AudiolinkFileLink()

        def analyze(fp):
            try:
                al_file.path = fp
                al_id.val = al_file.id
            except UnreadableFileError as e:
                print(e)
                return None

            try:
                id_valid = True if al_id.val is not None else False
            except ValueError:
                id_valid = False

            output = {
                    'path': str(fp), #TODO resolve path?
                    'id': al_id.val,
                    'id_valid': id_valid,
                }

            if self.link_path:
                al_link.file = al_file
                al_link.link_path = self.link_path
                output['link_status'] = al_link.link_status
                
            return output

        files = (fp for fp in self.path.rglob('*') if fp.is_file and fp.suffix in set(file_types))

        print('Scanning...')
        self._cache = [analyze(fp) for fp in files]
        
        count_files = len(self._cache)
        count_id_missing = len([1 for _ in self._cache if _.get('id') is None])
        count_id_valid = len([1 for _ in self._cache if _.get('id_valid')])
        count_id_not_valid = len([1 for _ in self._cache if _.get('id') is not None and not _.get('id_valid')])
        
        print(f'Scan Results: \n'
            + f'  Files........ {count_files} \n'
            + f'  Id Valid:.... {count_id_valid} \n'
            + f'  Id Invalid... {count_id_not_valid} \n'
            + f'  Id Missing... {count_id_missing}'
        )

    def scan_links(self):
        pass

    def set_ids(self, status:str='missing') -> None:
        al_file = AudiolinkFile()

        def operate_on_file(val:dict):
            if status == 'missing':
                if val.get('id') is None:
                    return True
            
            if status == 'invalid':
                if val.get('id') is not None and not val.get('id_valid'):
                    return True
            
            return False

        for i, elem in enumerate(self._cache):
            if operate_on_file(elem):
                al_file.path = elem.get('path')
                al_file.id = AudiolinkId.new()
                self._cache[i]['id'] = al_file.id


    def delete_ids(self) -> None:
        response = input('Warning: This will remove all Audiolink Ids from files. Continue: Y?')
        if response != 'Y':
            return

        al_file = AudiolinkFile()

        for i, elem in enumerate(self._cache):
            al_file.path = elem.get('path')
            del al_file.id
            self._cache[i]['id'] = None


    def update_links(self):
        if self.link_path is None:
            raise ValueError('link path not set')

        #TODO: scan links
        self.scan_links()
        #TODO: delete all that are not active (move to alternate folder)

        al_file = AudiolinkFile()
        al_link = AudiolinkFileLink()
        
        #TODO: Skip Active
        for i, elem in enumerate(self._cache):
            al_file.path = elem.get('path')
            al_link.file = al_file
            al_link.link_path = self.link_path
            al_link.create_link()
            self._cache[i]['link_status'] = al_link.link_status
