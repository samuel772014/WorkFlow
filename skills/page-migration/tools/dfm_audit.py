#!/usr/bin/env python3
# DFM 篩選/頁籤/控件 稽核（indent-aware；支援 object 與 inline frame）。
# 只擷取「物件本身」直屬屬性(base_indent+2)的 Left/Top/Caption/Visible/TabVisible，避免被巢狀 EditLabel/子物件汙染。
# 用法：PYTHONIOENCODING=utf-8 py dfm_audit.py <path.dfm>
import re, sys

def dec(s):
    parts=[]
    for q,n in re.findall(r"'([^']*)'|#(\d+)", s):
        parts.append(chr(int(n)) if n else q.encode('latin-1').decode('cp950','replace'))
    return ''.join(parts)

def main(path):
    with open(path, encoding='latin-1') as f:
        lines=f.readlines()
    objs=[]; stack=[]
    for ln in lines:
        m=re.match(r'(\s*)(object|inline) (\w+): (T\w+)', ln)
        if m:
            indent=len(m.group(1))
            o={'name':m.group(3),'type':m.group(4),'indent':indent,'left':None,'top':None,'cap':None,'tabvis':None,'vis':None}
            objs.append(o); stack.append(o); continue
        if re.match(r'\s*end\b', ln) and stack:
            # pop when indentation matches the top object's indent
            ind=len(ln)-len(ln.lstrip())
            if ind==stack[-1]['indent']:
                stack.pop()
            continue
        if not stack: continue
        o=stack[-1]; base=o['indent']+2
        ind=len(ln)-len(ln.lstrip())
        if ind!=base: continue          # 只收直屬屬性
        mm=re.match(r'\s*Left = (-?\d+)',ln);  o['left']=int(mm.group(1)) if mm else o['left']
        mm=re.match(r'\s*Top = (-?\d+)',ln);   o['top']=int(mm.group(1)) if mm else o['top']
        mm=re.match(r'\s*Caption = (.+)$',ln)
        if mm and o['cap'] is None: o['cap']=dec(mm.group(1))
        if re.match(r'\s*TabVisible = False',ln): o['tabvis']=False
        if re.match(r'\s*Visible = False',ln): o['vis']=False

    def key(o): return (o['top'] if o['top'] is not None else 99999, o['left'] if o['left'] is not None else 99999)

    labels=[o for o in objs if o['type']=='TLabel' and o['cap']]
    print("=== TLabel 標題（top,left 排序）===")
    for o in sorted(labels,key=key):
        print(f"  top={o['top']:<5} left={o['left']:<5} {o['cap']}")

    ctl=('TRzButtonEdit','TRzComboBox','TRzDateTimeEdit','TMaskEdit','TRzCheckBox','TCheckBox','TEdit','TRzDBEdit')
    edt=[o for o in objs if o['type'] in ctl]
    print("\n=== 篩選/輸入控件（top,left 排序）===")
    for o in sorted(edt,key=key):
        extra=f" cap='{o['cap']}'" if o['cap'] else ""
        vis=" [Vis=False]" if o['vis'] is False else ""
        print(f"  {o['name']:<16}{o['type']:<15}top={o['top']} left={o['left']}{extra}{vis}")

    fr=[o for o in objs if o['type'].startswith('Tfm') or 'P2Date' in o['type'] or 'P2YRMN' in o['type']]
    if fr:
        print("\n=== 內嵌 frame（日期/年月區間）top,left 排序 ===")
        for o in sorted(fr,key=key):
            print(f"  {o['name']:<16}{o['type']:<18}top={o['top']} left={o['left']}")

    tabs=[o for o in objs if o['type'].endswith('TabSheet')]  # TTabSheet / TRzTabSheet 皆收
    if tabs:
        print("\n=== TabSheet 頁籤（檔案順序）===")
        for o in tabs:
            vis=" [TabVisible=False]" if o['tabvis'] is False else ""
            print(f"  {o['name']:<18}{o['cap']}{vis}")

if __name__=='__main__':
    main(sys.argv[1])
