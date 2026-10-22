"""扫描一个文件夹（含子目录）下所有 BG3 .pak，列出文件数与「等级上限相关」条目。

用法:
    python scan_paks.py "C:\\Users\\wenso\\Downloads\\博德3Mod-B站-在下夜独 2026.7.26\\【必下】整合包"

输出示例:
    [命中] 等级拓展.pak  12.3 MB  v18  48 文件
           Shared/Progressions/Progressions.lsx
           Public/Shared/Levelmaps/LevelMapValues.lsx

依赖: pip install lz4
"""
import os
import sys

from lspk import read_pak

# 强判定：只有真正的全局等级/经验/上限改动才会命中
STRONG = (
    'shared/progressions',
    'shared/levelmaps',
    'levelcurve',
    'level_cap',
    'levelcap',
    'maxlevel',
    'experience',
    'xpcurve',
)
# 弱判定：各职业自带的 Levelmaps 也会命中，仅作提示
WEAK = ('levelmap',)


def scan(root):
    hits = []
    paks = []
    for dp, dns, fns in os.walk(root):
        for fn in fns:
            if fn.lower().endswith('.pak'):
                paks.append(os.path.join(dp, fn))
    paks.sort()
    print('发现 %d 个 pak，开始读取文件列表...\n' % len(paks))
    for p in paks:
        size = os.path.getsize(p)
        try:
            ver, files, _ = read_pak(p)
        except Exception as e:
            print('[跳过] %s  %s' % (os.path.basename(p), e))
            continue
        strong = []
        weak = []
        for name, *_ in files:
            low = name.lower()
            if any(k in low for k in STRONG):
                strong.append(name)
            elif any(k in low for k in WEAK):
                weak.append(name)
        flag = '命中' if strong else ('提示' if weak else '    ')
        print('[%s] %s  %.1f MB  v%d  %d 文件' % (
            flag, os.path.basename(p), size / 1048576.0, ver, len(files)))
        if strong:
            hits.append((p, size, ver, strong))
            for m in strong[:12]:
                print('        ' + m)
            if len(strong) > 12:
                print('        ... 另有 %d 条' % (len(strong) - 12))
    print('\n==== 结论 ====')
    if not hits:
        print('没有任何 pak 命中等级上限关键字。')
        return
    print('可能是等级扩展的 pak（按体积从小到大，优先传最小的）：')
    for p, size, ver, matched in sorted(hits, key=lambda x: x[1]):
        print('  %.1f MB  %s  (%d 条相关文件)' % (size / 1048576.0, p, len(matched)))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    scan(sys.argv[1])
