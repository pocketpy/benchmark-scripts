import os
import sys
import shutil
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
    
def build_repo(pkpy_repo:repo.Repo, tag: TagReference | BranchAsTag) -> None:
    """Build the repo with specific tag/branch static, copy excutable into
    the corresponding folder
    """
    pkpy_repo.git.checkout('-f', tag.name)
    # build dir All_in_one/{tag}
    assert os.path.exists('pocketpy')
    if not os.path.exists('All_in_one'):
        os.mkdir('All_in_one')
    if os.path.exists(f'All_in_one/{tag.name}'):
        shutil.rmtree(f'All_in_one/{tag.name}')
    os.mkdir(f'All_in_one/{tag.name}')
    # build the current version of pkpy
    os.chdir('pocketpy')
    assert os.system('python prebuild.py') == 0
    
    if os.path.exists('build'):
        shutil.rmtree('build')
    os.mkdir('build')
        
    os.chdir('build')
    code = os.system('cmake .. -DPK_ENABLE_OS=ON -DPK_ENABLE_THREADS=OFF -DPK_ENABLE_DETERMINISM=OFF -DPK_ENABLE_WATCHDOG=OFF -DPK_ENABLE_CUSTOM_SNAME=OFF -DPK_ENABLE_MIMALLOC=OFF -DPK_BUILD_MODULE_LZ4=OFF -DPK_BUILD_MODULE_LIBHV=OFF -DCMAKE_BUILD_TYPE=Release')
    assert code == 0
    code = os.system(f'cmake --build . --config Release')
    assert code == 0
    
    if sys.platform == 'win32':
        shutil.copy(f'Release/main.exe', f'../../All_in_one/{tag.name}/main.exe')
        dll_path = f'Release/pocketpy.dll'
        if os.path.exists(dll_path):
            shutil.copy(dll_path, f'../../All_in_one/{tag.name}/pocketpy.dll')
    elif sys.platform == 'darwin':
        shutil.copy('main', '../All_in_one/{tag.name}/main')
        dll_path = 'libpocketpy.dylib'
        if os.path.exists(dll_path):
            shutil.copy(dll_path, f'../All_in_one/{tag.name}/libpocketpy.dylib')
    else:
        shutil.copy('main', f'../All_in_one/{tag.name}/main')
        dll_path = 'libpocketpy.so'
        if os.path.exists(dll_path):
            shutil.copy(dll_path, f'../All_in_one/{tag.name}/libpocketpy.so')
    
    os.chdir('../..')


pkpy_repo = clone_pkpy_repo()

tag_list = tags_filter(pkpy_repo.tags)
for tag in reversed(tag_list):
    build_repo(pkpy_repo, tag)