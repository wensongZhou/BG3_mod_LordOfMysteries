"""从单个 pak 中只抽出指定路径（关键字匹配）的文件，避免解包几个 GB 的材质。

用法:
    python extract_subset.py "C:\\...\\等级拓展.pak" "C:\\...\\out"
    python extract_subset.py "C:\\...\\等级拓展.pak" --list        # 只看清单
    python extract_subset.py "C:\\...\\等级拓展.pak" "C:\\...\\out" meta.lsx,Shared/,Progressions

不给关键字时，默认抽取与「等级/进度/经验/职业定义」相关的小文件。

依赖: pip install lz4
"""
import os
import sys

import lz4.block

from lspk import read_pak

DEFAULT = (
    'meta.lsx',
    'shared/',
    'progressions',
    'levelmap',
    'levelcurve',
    'experience',
    'classdescriptions',
    'actionresourcedefinitions',
    'lists/',
    'defaultvalues/',
)


def run(pak, out, keys):
    ver, files, d = read_pak(pak)
    keys = tuple(k.lower() for k in keys)
    picked = [f for f in files if any(k in f[0].lower() for k in keys)]
    if out is None:
        print('v%d  %d 文件，匹配 %d 条：' % (ver, len(files), len(picked)))
        for name, _, size, usize in picked:
            print('  %8d -> %8d  %s' % (size, usize, name))
        return
    total = 0
    for name, offset, size, usize in picked:
        target = os.path.join(out, name.replace('/', os.sep))
        os.makedirs(os.path.dirname(target) or out, exist_ok=True)
        blob = d[offset:offset + size]
        if size and usize:
            blob = lz4.block.decompress(blob, uncompressed_size=usize)
        with open(target, 'wb') as f:
            f.write(blob)
        total += len(blob)
    print('已抽取 %d 个文件，共 %.1f KB -> %s' % (len(picked), total / 1024.0, out))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    pak = sys.argv[1]
    if len(sys.argv) >= 3 and sys.argv[2] == '--list':
        run(pak, None, DEFAULT)
        sys.exit(0)
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    out = sys.argv[2]
    keys = sys.argv[3].split(',') if len(sys.argv) > 3 else DEFAULT
    run(pak, out, keys)
