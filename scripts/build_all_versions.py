import os
import sys
import subprocess
import shutil
import time
from typing import Union
from git import repo
from git import TagReference
from packaging import version
import json


OUTPUT_DIR = "output"

class BranchAsTag:
    def __init__(self, branch: str) -> None:
        self.name = branch


def tags_filter(tags: list[TagReference]) -> list[TagReference]:
    """Filter tag version above v1.1.0(include v1.1.0)
    """
    base_ver = version.parse('1.1.0')
    ret_tags = []
    for tag in tags:
        try:
            tag_ver = version.parse(tag.name)
            if tag_ver >= base_ver:
                ret_tags.append(tag)
        except:
            continue
    main = BranchAsTag('main')
    ret_tags.append(main)
    return ret_tags
    
def build_repo(pkpy_repo: repo.Repo, tag: Union[TagReference, BranchAsTag]) -> float:
    print(f'Building {tag.name}')
    
    pkpy_repo.git.checkout('-f', tag.name)
    # build dir {OUTPUT_DIR}/{tag}
    assert os.path.exists('pocketpy')
    if os.path.exists('pocketpy/build'):
        shutil.rmtree('pocketpy/build')

    os.mkdir(f"{OUTPUT_DIR}/pkpy-{tag.name}")
    # build the current version of pkpy
    try:
        subprocess.run([sys.executable, 'prebuild.py'], cwd='pocketpy', stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f'prebuild.py run failed with return code {e.returncode}: {e.stderr}')
    cmake_cmd = [
        "cmake",
        "-B", "build",
        "-S", ".",
        "-DPK_ENABLE_OS=ON",
        "-DPK_ENABLE_THREADS=OFF",
        "-DPK_USE_BOX2D=OFF",
        "-DCMAKE_BUILD_TYPE=Release"
    ]

    build_cmd = [
        "cmake",
        "--build", "build",
        "--config", "Release",
        "--parallel", str(os.cpu_count() or 1),
    ]
    _0 = time.perf_counter()
    subprocess.run(cmake_cmd, cwd='pocketpy', check=True)
    _1 = time.perf_counter()
    subprocess.run(build_cmd, cwd='pocketpy', check=True)
    _2 = time.perf_counter()

    compile_time = {
        'config_time': _1 - _0,
        'build_time': _2 - _1,
    }

    with open(f"{OUTPUT_DIR}/pkpy-{tag.name}/compile_time.json", 'w') as f:
        json.dump(compile_time, f)

    elapsed_time = _2 - _0
    
    if sys.platform == 'win32':
        shutil.copy(f'pocketpy/build/Release/main.exe', f"{OUTPUT_DIR}/pkpy-{tag.name}/main.exe")
        dll_path = f'pocketpy/build/Release/pocketpy.dll'
        if os.path.exists(dll_path):
            shutil.copy(dll_path, f"{OUTPUT_DIR}/pkpy-{tag.name}/pocketpy.dll")
    elif sys.platform == 'darwin':
        shutil.copy('pocketpy/build/main', f"{OUTPUT_DIR}/pkpy-{tag.name}/main")
        dll_path = 'pocketpy/build/libpocketpy.dylib'
        if os.path.exists(dll_path):
            shutil.copy(dll_path, f"{OUTPUT_DIR}/pkpy-{tag.name}/libpocketpy.dylib")
    else:
        shutil.copy('pocketpy/build/main', f"{OUTPUT_DIR}/pkpy-{tag.name}/main")
        dll_path = 'pocketpy/build/libpocketpy.so'
        if os.path.exists(dll_path):
            shutil.copy(dll_path, f"{OUTPUT_DIR}/pkpy-{tag.name}/libpocketpy.so")
    
    return elapsed_time


if __name__ == "__main__":
    if not os.path.exists('pocketpy'):
        code = os.system('git clone https://github.com/pocketpy/pocketpy.git')
        if code != 0:
            print("Failed to clone the repository. Please check your network connection or the repository URL.")
            exit(1)

    pkpy_repo = repo.Repo('pocketpy')

    tag_list = tags_filter(pkpy_repo.tags)

    # build_repo also has OUTPUT_DIR path check, if the code run for the first time, log will need the following code
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    os.mkdir(OUTPUT_DIR)

    with open(f'{OUTPUT_DIR}/log.txt', 'w') as fp:
        fp.write(f'Building pocketpy with shared compilation, v1.1.0 - latest release, including main branch version.\n')
        for tag in reversed(tag_list):
            elapsed_time = build_repo(pkpy_repo, tag)
            fp.write(f'{tag.name}:\t{elapsed_time:.2f}s\n')
