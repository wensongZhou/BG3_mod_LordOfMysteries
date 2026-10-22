"""把一个目录打包成 BG3 可用的 LSPK v18 .pak。

用法:
    python pack_pak.py <源目录> <输出.pak>

源目录应为 pak 内的根结构，例如:
    源目录/Mods/SefirahCastle/meta.lsx
    源目录/Public/SefirahCastle/...

依赖: pip install lz4
"""
import os
import struct
import sys

import lz4.block

ENTRY = 272


def collect(root):
    out = []
    for dp, _, fns in os.walk(root):
        for fn in fns:
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, root).replace(os.sep, '/')
            out.append((rel, full))
    out.sort()
    return out


def pack(root, out_path):
    body = bytearray(b'\xAD' * 40)
    metas = []
    for rel, full in collect(root):
        with open(full, 'rb') as f:
            raw = f.read()
        comp = lz4.block.compress(raw, store_size=False) if raw else b''
        assert len(body) % 64 == 40, len(body)
        off = len(body)
        body += comp
        rem = (40 - (len(body) % 64)) % 64
        body += b'\xAD' * rem
        metas.append((rel, off, len(comp), len(raw)))

    fl_off = len(body)
    assert fl_off % 64 == 40, fl_off
    entries = bytearray()
    for rel, off, csz, usz in metas:
        e = bytearray(ENTRY)
        nb = rel.encode('utf-8')
        assert len(nb) < 256, rel
        e[0:len(nb)] = nb
        struct.pack_into('<I', e, 256, off)
        struct.pack_into('<H', e, 260, 0)
        e[262] = 0
        e[263] = 0
        struct.pack_into('<II', e, 264, csz, usz)
        entries += e

    clist = lz4.block.compress(bytes(entries), store_size=False)
    flist = struct.pack('<II', len(metas), len(clist)) + clist
    body += flist

    header = bytearray(40)
    header[0:4] = b'LSPK'
    struct.pack_into('<I', header, 4, 18)
    struct.pack_into('<Q', header, 8, fl_off)
    struct.pack_into('<I', header, 16, len(flist))
    header[20] = 0
    header[21] = 0
    struct.pack_into('<H', header, 38, 1)
    body[0:40] = header

    with open(out_path, 'wb') as f:
        f.write(bytes(body))
    return len(metas), len(body)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    n, size = pack(sys.argv[1], sys.argv[2])
    print('打包完成: %s  %d files, %d bytes' % (sys.argv[2], n, size))
