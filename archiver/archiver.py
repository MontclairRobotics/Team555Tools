"""A simple archiver script built for Java projects."""

__author__ = 'Team 555 (Dylan Rafael)'
__version__ = '1.0.0'

# imports
import json
import os
import re
import string
import sys
import tempfile
import shutil
import time
import traceback
from enum import Enum
from pathlib import Path


# constants of operation
JAVA_DIR_NAME = r'sourceproj\src\main\java\org\team555'
BUILD_FRAME = r'org\team555'
EXTRA_FRAME = r'toolstracker'

PROJ_DIR = os.path.join(__file__, r'..\..')
THIS_DIR = os.path.join(__file__, r'..')
JAVA_DIR = os.path.join(PROJ_DIR, JAVA_DIR_NAME)

OUTPUT_DIR = os.path.join(PROJ_DIR, 'archives')
ARCHIVES_JSON = os.path.join(THIS_DIR, 'archives.json')

SOURCE_DIR = THIS_DIR

TAG_PATTERN = re.compile(r'^\s*@([\w\d]+)\s+(.*?)$', re.MULTILINE)
COMMENT_PATTERN = re.compile(r'^\s*@:.*?$', re.MULTILINE)
ESCAPE_PATTERN = re.compile(r'^(\s*)@@(.*)$', re.MULTILINE)

INT_PATTERN = re.compile(r'\-?\d+$')
FLOAT_PATTERN = re.compile(r'\-?\d+\.\d+$')

# custom exception type
class ArchiverException(Exception):
    pass


# Tag class
class Tag:

    def __init__(self, match: re.Match, line: int):

        self.line: int = line
        self.tag: str = match.group(1)

        if match.group(2).strip() != '':
            self._values = re.split(r'\s+', match.group(2))
        else:
            self._values = []

        for i in range(len(self._values)):

            val = self._values[i]

            if INT_PATTERN.match(val):
                self._values[i] = int(val)
            elif FLOAT_PATTERN.match(val):
                self._values[i] = float(val)
    

    def __getitem__(self, i):

        if i >= len(self._values):
            raise ArchiverException(f'Tag {self.tag} has less than {i + 1} argument(s), despite requiring more.')

        return self._values[i]

    def __len__(self):
        
        return len(self._values)



# function to read all tags from text then return a list of Tag objects
# and a new version of the text without the tags
def read_tags(text: str) -> tuple[list[Tag], str]:
    
    tags = []
    new_text = ''

    for i, l in enumerate(text.splitlines()):

        match = TAG_PATTERN.match(l)

        if match:
            tags.append(Tag(match, i))
            continue

        comment = COMMENT_PATTERN.match(l)

        if comment:
            continue

        escape = ESCAPE_PATTERN.match(l)

        if escape:
            new_text += escape.group(1) + '@' + escape.group(2)
            continue

        new_text += l + '\n'

    return tags, new_text


# classes
class ArchiveState(Enum):
    UNKNOWN = 0
    UNSTARTED = 1
    BEING_BUILT = 2
    FINISHED = 3


class SourceFile:

    def __init__(self, path: Path, rel: str):
        self.path: Path = path
        self.rel: str = rel

    def __getitem__(self, i):
        if i == 0:
            return self.path
        elif i == 1:
            return self.rel
        else:
            raise IndexError(f'{i} is not a valid index for SourceFile.')


class Archive:

    def __init__(self, path: str):

        name_path = os.path.splitext(os.path.splitext(path)[0])[0]
        self.name: str = os.path.split(name_path)[1]

        self.path: str = path
        self.version: str = ''
        self.files: list[SourceFile] = []
        self.description: str = ''
        self.state: ArchiveState = ArchiveState.UNSTARTED
    
    def build(self, 
        all_files: list[SourceFile], 
        all_archives: dict[str, 'Archive']):

        # start building
        print(f"Now building '{self.name}'")
        self.state = ArchiveState.BEING_BUILT

        # get archive information
        desc_text_raw = Path(self.path).read_text()

        # get tags from archive description
        tags, desc_text = read_tags(desc_text_raw)

        # parse tags
        version = None
        req_files = []
        includes = []
        excludes = []

        for tag in tags:
            match tag.tag.lower():
                case 'ver':
                    version = tag[0]
                case 'include':
                    includes.append(tag[0])
                case 'exclude':
                    excludes.append(tag[0])
                case 'external':
                    desc_text += f"\n**NOTE**: This archive requires the external library '{tag[0]}' to be installed in order to function."
                case 'requires':

                    desc_text += f"\n**NOTE**: This archive requires the archive '{tag[0]}' to be installed in order to function.\nA copy of it will be included in the archive package, but does not need to be put in place if you already have '{tag[0]}' installed.\n"

                    # check for required archives
                    if tag[0] not in all_archives:
                        raise ArchiverException(f"Archive '{self.name}' requires non-existent archive '{tag[0]}'.")
                    
                    # check for circular dependency
                    if all_archives[tag[0]].state == ArchiveState.BEING_BUILT:
                        raise ArchiverException(f"Archive '{self.name}' is self-referencing.")
                    
                    # check for unstarted archives
                    if all_archives[tag[0]].state == ArchiveState.UNSTARTED:
                        all_archives[tag[0]].build(all_files, all_archives)

                    # add all archive files to required files
                    req_files += all_archives[tag[0]].files

                case _:
                    raise ArchiverException(f'Unknown tag: {tag.tag}')

        if not version:
            raise ArchiverException(f"Archive description for archive '{self.name}' is invalid: no version found.")

        self.version = version
        self.description = desc_text

        # get files
        files = [
            sf for sf in all_files 
            if any(sf.rel.startswith(i) for i in includes)
        ]

        if len(excludes) != 0:
            files = [
                sf for sf in files
                if not any(sf.rel.startswith(e) for e in excludes)
            ]

        files += req_files

        self.files = files
        
        # finish building
        self.state = ArchiveState.FINISHED
    

    def write_to(self, output_dir: str):

        # copy new archive description
        desc_path = os.path.join(output_dir, f'{self.name}.md')
        Path(desc_path).write_text(self.description)

        # create temp folder
        build = tempfile.mkdtemp()

        # create java folder
        build_jav = os.path.join(build, BUILD_FRAME)
        os.makedirs(build_jav)

        print(f'Temp build path = {build_jav}')

        # create files_{name}.json
        build_extra = os.path.join(build, EXTRA_FRAME)

        os.makedirs(build_extra, exist_ok=True)
        with open(os.path.join(build_extra, f'files_{self.name}.json'), 'w') as jsf:
            json.dump(
                {
                    'version': self.version, 
                    'files': [f.rel for f in self.files]
                }, 
                jsf
            )

        # copy files to temp folder
        for f, rel_src in self.files:
            src = os.path.normpath(f)
            dst = os.path.normpath(os.path.join(build_jav, rel_src))

            print(f'Copying {rel_src} . . . ')

            os.makedirs(os.path.split(dst)[0], exist_ok=True)
            shutil.copyfile(src, dst)

        # create zip
        print('Now archiving!')
        output_fn = self.name
        output = os.path.join(output_dir, output_fn)
        shutil.make_archive(output, 'tar', build)

        # delete temp folder
        shutil.rmtree(build)


# Main function
def main():

    if sys.version_info < (3, 10):
        print('This script requires Python 3.10 or higher.')
        sys.exit(1)

    print('-' * 50)
    print(f'Starting build process . . . ')
    print('-' * 50)

    time_start_all = time.time()

    # setup temporary directory
    temp = tempfile.mkdtemp()

    # get all files in java project
    all_files = [
        SourceFile(f.absolute(), os.path.relpath(f, JAVA_DIR)) 
        for f in Path(JAVA_DIR).glob("**/*.*")
    ]

    try:

        # build each archive
        all_archives = {
            a.name: a for a in 
            (Archive(os.path.join(SOURCE_DIR, f)) for f in os.listdir(SOURCE_DIR) if f.endswith('.archive.md'))
        }

        for arch in all_archives.values():

            print()
            
            time_start = time.time()

            arch.build(all_files, all_archives)
            arch.write_to(temp)

            print(f"Done building '{arch.name}'! Took {time.time() - time_start:.5} seconds.")
        
    except Exception as em:

        # print build failure messages and delete temp folder
        print()
        print('-' * 50)
        print(f'[FATAL] Build failed!')

        if isinstance(em, ArchiverException):
            print(em)
        else:
            print('-' * 50)
            traceback.print_exc()
        
        print('-' * 50)

        shutil.rmtree(temp)

        exit(1)

    # move temp folder to output folder then delete it
    print()
    print('Overriding real output folder . . . ')

    shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(temp, OUTPUT_DIR)
    shutil.rmtree(temp)

    # announce completion
    print()
    print('-' * 50)
    print(f'Build complete! Took {time.time() - time_start_all:.5} seconds.')
    print('-' * 50)


# Main
if __name__ == '__main__':
    main()