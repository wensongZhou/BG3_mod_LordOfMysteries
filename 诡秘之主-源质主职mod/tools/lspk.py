"""BG3 LSPK v18 pak 读取（只读文件列表与解包）。

依赖: pip install lz4
"""
import struct
import os
import lz4.block

ENTRY = 272


def read_pak(path):
    """返回 (版本号, [(相对路径, 偏移, 压缩后大小, 原始大小), ...], 原始字节)。"""
    with open(path, 'rb') as f:
        d = f.read()
    if d[:4] != b'LSPK':
        raise ValueError('不是 pak 文件: %s' % path)
    ver = struct.unpack_from('<I', d, 4)[0]
    off = struct.unpack_from('<Q', d, 8)[0]
    n, csz = struct.unpack_from('<II', d, off)
    raw = d[off + 8: off + 8 + csz]
    out = lz4.block.decompress(raw, uncompressed_size=n * ENTRY)
    assert len(out) == n * ENTRY, (len(out), n)
    files = []
    for i in range(n):
        b = out[i * ENTRY:(i + 1) * ENTRY]
        name = b[:256].split(b'\0')[0].decode('utf-8', 'replace')
        offset, _res, size, usize = struct.unpack_from('<IIII', b, 256)
        files.append((name, offset, size, usize))
    return ver, files, d


def extract(path, dest):
    """全量解包到 dest 目录。"""
    ver, files, d = read_pak(path)
    for name, offset, size, usize in files:
        target = os.path.join(dest, name.replace('/', os.sep))
        os.makedirs(os.path.dirname(target) or dest, exist_ok=True)
        blob = d[offset:offset + size]
        if size and usize:
            blob = lz4.block.decompress(blob, uncompressed_size=usize)
        with open(target, 'wb') as f:
            f.write(blob)
    return ver, len(files)
