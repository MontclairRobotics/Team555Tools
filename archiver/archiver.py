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
from pathlib import Path


# constants of operation
JAVA_DIR_NAME = r'sourceproj\src\main\java\org\team555'
BUILD_FRAME = r'org\team555'

PROJ_DIR = os.path.join(__file__, r'..\..')
THIS_DIR = os.path.join(__file__, r'..')
JAVA_DIR = os.path.join(PROJ_DIR, JAVA_DIR_NAME)

OUTPUT_DIR = os.path.join(PROJ_DIR, 'archives')
ARCHIVES_JSON = os.path.join(THIS_DIR, 'archives.json')

SOURCE_DIR = THIS_DIR

TAG_PATTERN = re.compile(r'\s*\<!(\w+)(?:\s(.+))?!>\s*')
COMMENT_PATTERN = re.compile(r'\s*\<#.+#>\s*')
INT_PATTERN = re.compile(r'\-?\d+$')
FLOAT_PATTERN = re.compile(r'\-?\d+\.\d+$')

# custom exception type
class ArchiverException(Exception):
    pass


# Tag class
class Tag:

    def __init__(self, match: re.Match, line: int):

        self.line = line
        self.tag = match.group(1)

        if match.group(2).strip() != '':
            self._values = re.split(r'\s+', match.group(2))
        else:
            self._values = []
        
        print(self._values)

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

        new_text += l + '\n'

    return tags, new_text


# function to build a single archive
def build_archive(
    desc_file: str,
    output_folder: str, 
    all_files: list[tuple[Path, str]]
    ):

    # start timer
    time_start = time.time()

    # get archive name
    name_path = os.path.splitext(os.path.splitext(desc_file)[0])[0]
    name = os.path.split(name_path)[1]

    print(f"Now building '{name}'")

    # get archive information
    desc_text = Path(desc_file).read_text()

    # get tags from archive description
    tags, new_text = read_tags(desc_text)

    # parse tags
    version = None
    includes = []
    excludes = []

    for tag in tags:
        match tag.tag:
            case 'ver':
                version = tag[0]
            case 'include':
                includes.append(tag[0])
            case 'exclude':
                excludes.append(tag[0])
            case _:
                raise ArchiverException(f'Unknown tag: {tag.tag}')

    if not version:
        raise ArchiverException(f"Archive description for archive '{name}' is invalid: no version found.")

    # copy new archive description
    copy_desc_path = os.path.join(output_folder, f'{name}.md')
    Path(copy_desc_path).write_text(new_text)

    # get files
    files = [
        (f, rel) for f, rel in all_files 
        if any(rel.startswith(i) for i in includes)
    ]

    if len(excludes) != 0:
        files = [
            (f, rel) for (f, rel) in files
            if not any(rel.startswith(e) for e in excludes)
        ]

    # create temp folder
    build = tempfile.mkdtemp()

    # create java folder
    build_jav = os.path.join(build, BUILD_FRAME)
    os.makedirs(build_jav)

    print(f'Temp build path = {build_jav}')

    # create files_{name}.json
    with open(os.path.join(build, f'files_{name}.json'), 'w') as jsf:
        json.dump(
            {
                'version': version, 
                'files': [r for _, r in files]
            }, 
            jsf
        )

    # copy files to temp folder
    for f, rel_src in files:
        src = os.path.normpath(f)
        dst = os.path.normpath(os.path.join(build_jav, rel_src))

        print(f'Copying {rel_src} . . . ')

        os.makedirs(os.path.split(dst)[0], exist_ok=True)
        shutil.copyfile(src, dst)

    # create zip
    print('Now archiving!')
    output_fn = name
    output = os.path.join(output_folder, output_fn)
    shutil.make_archive(output, 'tar', build)

    # delete temp folder
    shutil.rmtree(build)
    
    print(f"Done building '{name}'! Took {time.time() - time_start:.5} seconds.")


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
        (f.absolute(), os.path.relpath(f, JAVA_DIR)) 
        for f in Path(JAVA_DIR).glob("**/*.*")
    ]

    try:

        # build each archive
        for arch in os.listdir(SOURCE_DIR):

            # skip non archive files
            if not arch.endswith('.archive.md'):
                continue

            print()
            build_archive(os.path.join(SOURCE_DIR, arch), temp, all_files)
        
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