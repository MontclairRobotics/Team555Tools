"""A simple archiver script built for Java projects."""

__author__ = 'Team 555 (Dylan Rafael)'
__version__ = '1.0.0'

# imports
import json
import os
import re
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

ADESC_DIR = os.path.join(THIS_DIR, 'adesc')

VER_PATTERN = re.compile(r'\s*\<!ver ([0123456789\.]+)\!>\s*')


# custom exception type
class ArchiverException(Exception):
    pass


# function to build a single archive
def build_archive(
    name: str, 
    includes: list[str], 
    excludes: list[str], 
    output_folder: str, 
    all_files: list[tuple[Path, str]]
    ):

    print(f"Now building '{name}'")

    time_start = time.time()

    # get includes and excludes
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

    # copy archive description
    desc_path = os.path.join(ADESC_DIR, f'{name}.md')
    if not os.path.exists(desc_path):
        raise ArchiverException(f"Archive description not found for archive '{name}'")

    # get version from archive description
    desc_text = Path(desc_path).read_text()

    new_text = ''
    found_match = False

    for l in desc_text.splitlines():

        match = VER_PATTERN.match(l)

        if match:
            found_match = True
            version = match.group(1)
            continue
        
        new_text += l + '\n'

    if not found_match:
        raise ArchiverException(f"Archive description for archive '{name}' is invalid: no version found.")

    copy_desc_path = os.path.join(output_folder, f'{name}.md')
    Path(copy_desc_path).write_text(new_text)

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

    # get basic info
    temp = tempfile.mkdtemp()
    js = json.loads(Path(ARCHIVES_JSON).read_text())

    # get all files in java project
    all_files = [
        (f.absolute(), os.path.relpath(f, JAVA_DIR)) 
        for f in Path(JAVA_DIR).glob("**/*.*")
    ]

    try:

        # build each archive
        for proc in js:
            print()
            build_archive(
                proc['name'], 
                proc['include'], 
                proc['exclude'] if 'exclude' in proc else [],
                temp,
                all_files
            )
        
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