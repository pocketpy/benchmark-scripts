import os
import sys
import time
import pandas as pd
import json


def test_file(filepath, cpython=False, prefix='.'):
    start_time = time.perf_counter()
    if cpython:
        code = os.system("python " + filepath)
    if sys.platform == 'win32':
        code = os.system(f"{prefix}\\main.exe " + filepath)
    else:
        code = os.system(f"cd {prefix} && ./main " + filepath)
    elapsed_time = time.perf_counter() - start_time
    return (code == 0), elapsed_time


def iter_outputs(root='output'):
    entries = os.listdir(root)
    entries.sort(reverse=True)
    
    entries.remove('pkpy-main')
    entries.insert(0, 'pkpy-main')  # Ensure the main version is first

    for entry in entries:
        path = os.path.join(root, entry)
        if os.path.isdir(path):
            tag = entry.split('-')[-1]
            yield tag, path


def test_dir(path, prefix: str):
    print("Testing directory:", path, prefix)

    result = {}
    with open(os.path.join(prefix, 'compile_time.json'), 'r') as f:
        compile_time = json.load(f)
        result['config'] = compile_time.get('config_time', float('nan'))
        result['build'] = compile_time.get('build_time', float('nan'))

    blacklist = {'dumps_loads_pkl.py', 'dumps_loads_json.py', 'ldtk_json.py'}
    for filename in sorted(os.listdir(path)):
        if not filename.endswith('.py'):
            continue
        if filename in blacklist:
            continue
        filepath = os.path.join(path, filename)
        print("> " + filepath, flush=True)

        ok, elapsed_time = test_file(filepath, prefix=prefix)
        if not ok:
            print('-' * 50)
            print("TEST FAILED!")
            elapsed_time = float('nan')

        result[filename] = elapsed_time

    return result


import platform
import psutil

if __name__ == "__main__":
    print('CPython:', str(sys.version).replace('\n', ''))
    print('System:', '64-bit' if sys.maxsize > 2**32 else '32-bit')
    print('CPU:', platform.processor())
    print('RAM:', f"{psutil.virtual_memory().total / (1024 ** 3):.2f} GB")

    data = []

    for tag, output_path in iter_outputs():
        print(f"  {tag}: {output_path}")
        result = test_dir('benchmarks/', prefix=output_path)
        result['tag'] = tag
        data.append(result)

    # tag as index
    df = pd.DataFrame(data)
    df.set_index('tag', inplace=True, drop=True)
    df.to_csv('output/results.csv', index=True)

    print("ALL TESTS PASSED")
