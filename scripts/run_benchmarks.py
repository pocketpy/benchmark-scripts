import os
import sys
import time
import pandas as pd


def test_file(filepath, cpython=False, prefix='.'):
    start_time = time.perf_counter()
    if cpython:
        code = os.system("python " + filepath)
    if sys.platform == 'win32':
        code = os.system(f"{prefix}\\main.exe " + filepath)
    else:
        code = os.system(f"{prefix}/main " + filepath)
    elapsed_time = time.perf_counter() - start_time
    return (code == 0), elapsed_time


def iter_outputs(root='output'):
    entries = os.listdir(root)
    entries.sort()
    for entry in entries:
        path = os.path.join(root, entry)
        if os.path.isdir(path):
            tag = entry.split('-')[-1]
            yield tag, path


def test_dir(path, prefix: str):
    print("Testing directory:", path, prefix)

    result = {}
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


if __name__ == "__main__":
    print('CPython:', str(sys.version).replace('\n', ''))
    print('System:', '64-bit' if sys.maxsize > 2**32 else '32-bit')

    data = []

    for tag, output_path in iter_outputs():
        print(f"  {tag}: {output_path}")
        result = test_dir('benchmarks/', prefix=output_path)
        result['tag'] = tag
        data.append(result)

    # tag as index
    df = pd.DataFrame(data)
    df.set_index('tag', inplace=True, drop=True)
    df.to_csv('benchmark_results.csv', index=True)

    print("ALL TESTS PASSED")
