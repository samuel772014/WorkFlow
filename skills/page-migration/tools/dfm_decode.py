#!/usr/bin/env python3
# DFM grid-column decoder for IKS ERP page migration.
#
# Delphi .dfm 的 grid 欄位定義（wwDBGrid.Selected.Strings）是「欄位/寬度/中文標題/旗標」的權威來源，
# 但中文以 Big5(cp950) 原始位元組或 #NNNN 十進位字碼儲存，直接 Read 會是亂碼/難讀。
# 本工具把每個 grid 的 Selected.Strings 解出「序號. FIELD  w=寬  [可直輸/非直輸]  中文標題」，供轉譯時核對欄位/欄序/標題。
# 第 4 碼旗標：F=格內可直接輸入、T=不可直接輸入。
# ⚠ 「非直輸(T)」不等於唯讀：該欄仍可能靠 .pas 的 CdDblClick/MqyDblClick pick 編輯（例：B512 FACTID 旗標T 但有 FACTID pick）。
#   真正可編輯＝旗標F 或 .pas 有對該欄的 pick/InCell。編輯狀態一律以 .pas 為權威，DFM 旗標僅作輔助。
#
# 用法（務必帶 PYTHONIOENCODING=utf-8，否則 Windows 管道會把中文轉成亂碼）：
#   PYTHONIOENCODING=utf-8 py .claude/skills/page-migration/tools/dfm_decode.py <path.dfm>
# 例：
#   PYTHONIOENCODING=utf-8 py .claude/skills/page-migration/tools/dfm_decode.py D:/ikserp/MT/SAL/B430Base.dfm
import re, sys

def decode_tokens(s):
    parts = []
    for q, n in re.findall(r"'([^']*)'|#(\d+)", s):
        if n:
            parts.append(chr(int(n)))                       # #NNNN 十進位字碼
        else:
            parts.append(q.encode('latin-1').decode('cp950', 'replace'))  # 引號內 Big5 原始位元組
    return ''.join(parts)

def main(path):
    with open(path, 'r', encoding='latin-1') as f:
        lines = f.readlines()
    grid = '(main)'
    i = 0
    while i < len(lines):
        m = re.search(r'object (\w+): TwwDBGrid', lines[i])
        if m:
            grid = m.group(1)
        if 'Selected.Strings = (' in lines[i]:
            print(f"\n=== {grid} (line {i+1}) ===")
            j = i + 1
            idx = 0
            while j < len(lines):
                raw = lines[j].rstrip('\n').strip()
                closing = raw.endswith(')')
                data = raw[:-1] if closing else raw
                if data.strip():
                    cols = decode_tokens(data).split('\t')
                    field = cols[0] if len(cols) > 0 else ''
                    width = cols[1] if len(cols) > 1 else ''
                    title = cols[2] if len(cols) > 2 else ''
                    flag  = cols[3].strip() if len(cols) > 3 else ''   # wwDBGrid 第4碼：F=格內可直接輸入 / T=不可直接輸入
                    ed = '可直輸' if flag == 'F' else ('非直輸' if flag == 'T' else (flag or '?'))  # 非直輸≠唯讀：可能仍靠 .pas pick 編輯
                    idx += 1
                    print(f"{idx:2}. {field:<14} w={width:<4} [{ed}] {title}")
                if closing:
                    break
                j += 1
            i = j
        i += 1

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("usage: PYTHONIOENCODING=utf-8 py dfm_decode.py <path.dfm>")
        sys.exit(1)
    main(sys.argv[1])
