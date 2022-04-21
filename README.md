# Audiolink

Audiolink is a Python script for assigning a unique identifier to the tag of audio files.

When storing audio files on a filesystem, the path or file name can change over time. Many software tools rely on the file name and directory for locating the audio file, or matching the file name exactly in another directory. Audiolink, combined with file system hard links, allows for an audio library to have both an organized, mutable directory structure and a stable file name structure, while referencing the same file.

Audiolink can be ran in batch over all supported audio files to assign a unique identifier to the file tag. This id is then used as the file name in another directory and created as a hard link based on the original file.
