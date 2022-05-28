# Audiolink

Audiolink is a Python script for assigning a unique identifier to the tag of audio files and creating system hard links to the file in another location using the unique id as the filename.

When storing audio files on a filesystem, the path or file name can change over time. Many software tools rely on the file name and directory for locating the audio file, or matching the file name exactly in another directory. Audiolink, combined with file system hard links, allows for an audio library to have a flexible structure for organization and stable structure for usability, while referencing the same file.

Audiolink can be ran in batch over all supported audio files to assign a unique identifier to the file tag. This id is then used as the file name in another directory and created as a hard link based on the original file.


## Use

```python
from audiolink import AudiolinkFolder

music_path = '/path/to/music'
link_path = '/path/to/links'

music = AudiolinkFolder(music_path, link_path)
music.scan()
music.set_ids()
music.update_links()

```