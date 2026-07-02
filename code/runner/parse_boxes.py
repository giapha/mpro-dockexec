#!/usr/bin/env python3
"""Parse reported docking box centre + size from audit text spans (method-fix:
replace the 25 A default with each paper's actually-reported box). Centre/size are
read from reporting_fields_long.csv grid_center/grid_size spans by regex. Sizes
> SIZE_CAP A (blind whole-protein docks) are capped and flagged. Output box_table.csv.
Span-parsed boxes are NOT human-verified (disclosed limitation, R7)."""
import csv, re, os
HERE=os.path.dirname(os.path.abspath(__file__))
LONG=os.path.join(HERE,"..","..","_CONTROL","audit_candidate","reporting_fields_long.csv")
OUT=os.path.join(HERE,"out","box_table.csv")
SIZE_CAP=40.0   # cap blind-dock boxes; flag as capped

def nums(s):
    return [float(x) for x in re.findall(r'[-−–]?\d+\.?\d*', s.replace('−','-').replace('–','-'))]

def parse_center(span):
    s=span.replace('−','-').replace('–','-')
    # X = .. Y = .. Z = ..  /  X: .. Y: .. Z: ..
    m=re.search(r'[Xx]\s*[=:]\s*(-?\d+\.?\d*).{0,12}?[Yy]\s*[=:]\s*(-?\d+\.?\d*).{0,12}?[Zz]\s*[=:]\s*(-?\d+\.?\d*)', s)
    if m: return tuple(float(g) for g in m.groups())
    # (a, b, c)
    m=re.search(r'\(\s*(-?\d+\.?\d+)\s*,\s*(-?\d+\.?\d+)\s*,\s*(-?\d+\.?\d+)\s*\)', s)
    if m: return tuple(float(g) for g in m.groups())
    # "centered at a, b, c"
    m=re.search(r'cent[er]+ed?\s+at\s+(-?\d+\.?\d+)\s*,\s*(-?\d+\.?\d+)\s*,\s*(-?\d+\.?\d+)', s, re.I)
    if m: return tuple(float(g) for g in m.groups())
    return None

def parse_size(span):
    s=span.replace('−','-').replace('–','-').replace('×','x').replace('X','x')
    # A x B x C  (Angstrom dimensions)
    m=re.search(r'(\d+\.?\d*)\s*(?:Å|A|angstrom)?\s*x\s*(\d+\.?\d*)\s*(?:Å|A|angstrom)?\s*x\s*(\d+\.?\d*)', s, re.I)
    if m: return tuple(float(g) for g in m.groups())
    # (30, 30, 30)
    m=re.search(r'\(\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*\)', s)
    if m and 'size' in s.lower() or (m and 'dimension' in s.lower()): return tuple(float(g) for g in m.groups())
    # dimensions x = .. y = .. z = ..
    if 'dimension' in s.lower():
        m=re.search(r'x\s*[=:]\s*(\d+\.?\d*).{0,12}?y\s*[=:]\s*(\d+\.?\d*).{0,12}?z\s*[=:]\s*(\d+\.?\d*)', s, re.I)
        if m: return tuple(float(g) for g in m.groups())
    # radius R -> box = 2R + 8 buffer
    m=re.search(r'radius\s+(?:of\s+)?(?:set\s+to\s+be\s+)?(\d+\.?\d*)\s*Å', s, re.I)
    if m: r=float(m.group(1)); v=2*r+8; return (v,v,v)
    return None

rows=list(csv.DictReader(open(LONG)))
byp={}
for x in rows:
    pid=x.get('paper_id','')
    byp.setdefault(pid,{})[x.get('field','')]=x.get('span','') or ''

out=[]
for pid,f in sorted(byp.items()):
    c=parse_center(f.get('grid_center','')); sz=parse_size(f.get('grid_size','')) or parse_size(f.get('grid_center',''))
    capped=False
    if sz:
        sz=tuple(min(v,SIZE_CAP) for v in sz)
        capped=any(v>=SIZE_CAP for v in (parse_size(f.get('grid_size',''))or parse_size(f.get('grid_center',''))or(0,0,0)))
    out.append({"paper_id":pid,
                "cx":c[0] if c else "","cy":c[1] if c else "","cz":c[2] if c else "",
                "sx":sz[0] if sz else "","sy":sz[1] if sz else "","sz":sz[2] if sz else "",
                "size_capped":capped,"center_found":bool(c),"size_found":bool(sz)})
os.makedirs(os.path.dirname(OUT),exist_ok=True)
with open(OUT,"w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=["paper_id","cx","cy","cz","sx","sy","sz","size_capped","center_found","size_found"]); w.writeheader(); w.writerows(out)
nc=sum(1 for o in out if o["center_found"]); ns=sum(1 for o in out if o["size_found"])
print(f"parsed {len(out)} papers | centers {nc} | sizes {ns} | -> {OUT}")
for o in out:
    if o["paper_id"] in ("P0001","P0005","P0006","P0012","P0014","P0016","P0017","P0023","P0039","P0053"):
        print(f"  {o['paper_id']}: c=({o['cx']},{o['cy']},{o['cz']}) s=({o['sx']},{o['sy']},{o['sz']}) capped={o['size_capped']}")
