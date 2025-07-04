import os
import sys
import subprocess
import shutil
import time
from typing import Union
from git import repo
from git import TagReference
from packaging import version

class BranchAsTag:
    def __init__(self, branch: str) -> None:
        self.name = branch

def clone_pkpy_repo(local_path: str = './pocketpy') -> repo.Repo:
    """Clone the pkpy repo, main branch, or select the exist repo
    """
    try:
        if os.path.exists(local_path) and os.listdir(local_path):
            ret = repo.Repo(local_path)
            return ret
        
        ret = repo.Repo.clone_from('https://github.com/pocketpy/pocketpy.git', local_path)
        return ret
    except Exception as e:
        print(f'Clone pkpy failed: {e}')
        sys.exit(1)

def tags_filter(tags: list) -> list:
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
    
def build_repo(pkpy_repo:repo.Repo, tag: Union[TagReference, BranchAsTag]) -> float:
    """Build the repo with specific tag/branch static, copy excutable into
    the corresponding folder
    """
    pkpy_repo.git.checkout('-f', tag.name)
    # build dir All_in_one/{tag}
    assert os.path.exists('pocketpy')
    if os.path.exists('pocketpy/build'):
        shutil.rmtree('pocketpy/build')

    if not os.path.exists('All_in_one'):
        os.mkdir('All_in_one')
    if os.path.exists(f"All_in_one/pkpy-{tag.name.lstrip('v')}"):
        shutil.rmtree(f"All_in_one/pkpy-{tag.name.lstrip('v')}")
    os.mkdir(f"All_in_one/pkpy-{tag.name.lstrip('v')}")
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
    "-DPK_ENABLE_DETERMINISM=OFF",
    "-DPK_ENABLE_WATCHDOG=OFF",
    "-DPK_ENABLE_CUSTOM_SNAME=OFF",
    "-DPK_ENABLE_MIMALLOC=OFF",
    "-DPK_BUILD_MODULE_LZ4=OFF",
    "-DPK_BUILD_MODULE_LIBHV=OFF",
    "-DCMAKE_BUILD_TYPE=Release"
    ]

    build_cmd = [
        "cmake",
        "--build", "build",
        "--config", "Release"
    ]
    start_time = time.perf_counter()
    subprocess.run(cmake_cmd,
                   cwd='pocketpy', check=True)
    subprocess.run(build_cmd, cwd = 'pocketpy', check=True)
    elapsed_time = time.perf_counter() - start_time
    
    if sys.platform == 'win32':
        shutil.copy(f'pocketpy/build/Release/main.exe', f"All_in_one/pkpy-{tag.name.lstrip('v')}/main.exe")
        dll_path = f'pocketpy/build/Release/pocketpy.dll'
        if os.path.exists(dll_path):
            shutil.copy(dll_path, f"All_in_one/pkpy-{tag.name.lstrip('v')}/pocketpy.dll")
    elif sys.platform == 'darwin':
        shutil.copy('pocketpy/build/main', f"All_in_one/pkpy-{tag.name.lstrip('v')}/main")
        dll_path = 'pocketpy/build/libpocketpy.dylib'
        if os.path.exists(dll_path):
            shutil.copy(dll_path, f"All_in_one/pkpy-{tag.name.lstrip('v')}/libpocketpy.dylib")
    else:
        shutil.copy('pocketpy/build/main', f"All_in_one/pkpy-{tag.name.lstrip('v')}/main")
        dll_path = 'pocketpy/build/libpocketpy.so'
        if os.path.exists(dll_path):
            shutil.copy(dll_path, f"All_in_one/pkpy-{tag.name.lstrip('v')}/libpocketpy.so")
    
    return elapsed_time

pkpy_repo = clone_pkpy_repo()

tag_list = tags_filter(pkpy_repo.tags)

# build_repo also has 'All_in_one' path check, if the code run for the first time, log will need the following code
if not os.path.exists('All_in_one'):
    os.mkdir('All_in_one')

with open('All_in_one/log.txt', 'w') as fp:
    fp.write(f'Building pocketpy with shared compilation, v1.1.0 - latest release, including main branch version.\n')
    for tag in reversed(tag_list):
        elapsed_time = build_repo(pkpy_repo, tag)
        fp.write(f'{tag.name}:\t{elapsed_time:.2f}s\n')
        fp.flush()