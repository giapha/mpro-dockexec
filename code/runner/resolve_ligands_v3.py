#!/usr/bin/env python3
"""CID-anchored ligand resolver (max curated set for the paper).

Every ligand is resolved to a PubChem CID and the SMILES is taken from that CID,
so each structure is traceable (auditable) rather than a blind name->SMILES guess.
- cleans messy names: strip trailing '(L6)/(L_6)' lab codes, take first of 'A / B'
  synonyms, drop bracketed suffixes, normalize unicode subscripts.
- DrugBank 'DB...' and 'CID_N' handled; bare names -> PubChem name->cids -> cid.
- records InChIKey for each (provenance / later human spot-check).
Writes out/smiles_cache.csv (ligand_key, smiles, source) with source=pubchem:cid:<n>
plus out/ligand_provenance.csv (name, cid, inchikey, smiles, name_cleaned).
Unverified TLS (intercepting proxy). Run: python3 resolve_ligands_v3.py
"""
import csv, json, os, re, ssl, time, unicodedata, urllib.parse, urllib.request
_CTX = ssl._create_unverified_context()
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "out", "smiles_cache.csv")
PROV = os.path.join(HERE, "out", "ligand_provenance.csv")
MAN = os.path.join(HERE, "manifest.csv")

def get(url):
    try:
        with urllib.request.urlopen(url, timeout=20, context=_CTX) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None

def clean_name(n):
    n = unicodedata.normalize("NFKC", n or "").strip()
    n = re.split(r"\s*/\s*", n)[0]                      # 'A / B' -> 'A'
    n = re.sub(r"\s*\((?:L|cmpd|compound)?\s*\d+\)\s*$", "", n, flags=re.I)  # trailing (L6),(7)
    n = re.sub(r"\s*\[[^\]]*\]\s*$", "", n)             # trailing [..]
    return n.strip()

def cid_from(name, lid):
    lid = (lid or "").strip()
    m = re.search(r"(\d{2,})", lid) if (re.match(r"(?i)cid", lid) or lid.isdigit()) else None
    if m: return m.group(1)
    db = re.match(r"(?i)(DB\d+)", lid)
    if db:  # DrugBank -> PubChem xref
        d = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/xref/RegistryID/{db.group(1)}/cids/JSON")
        if d and d.get("IdentifierList", {}).get("CID"): return str(d["IdentifierList"]["CID"][0])
    for nm in ([name, clean_name(name)] if name else []):
        if not nm: continue
        d = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{urllib.parse.quote(nm)}/cids/JSON")
        if d and d.get("IdentifierList", {}).get("CID"): return str(d["IdentifierList"]["CID"][0])
        time.sleep(0.15)
    return None

def cid_props(cid):
    for props in ("IsomericSMILES,InChIKey", "SMILES,InChIKey", "CanonicalSMILES,InChIKey", "ConnectivitySMILES,InChIKey"):
        d = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/{props}/JSON")
        if d and "PropertyTable" in d:
            p = d["PropertyTable"]["Properties"][0]
            smi = p.get("IsomericSMILES") or p.get("SMILES") or p.get("CanonicalSMILES") or p.get("ConnectivitySMILES")
            if smi: return smi, p.get("InChIKey", "")
        time.sleep(0.15)
    return None, ""

def main():
    rows = list(csv.DictReader(open(MAN)))
    cache, prov = {}, []
    names = []
    seen = set()
    for r in rows:
        nm = r["ligand_name"].strip()
        if nm and nm not in seen:
            seen.add(nm); names.append((nm, r.get("ligand_id", "")))
    ok = 0
    for i, (nm, lid) in enumerate(names, 1):
        cid = cid_from(nm, lid)
        if cid:
            smi, ik = cid_props(cid)
            if smi:
                cache[nm] = (smi, f"pubchem:cid:{cid}")
                prov.append({"ligand_name": nm, "name_cleaned": clean_name(nm), "cid": cid, "inchikey": ik, "smiles": smi})
                ok += 1
                print(f"[{i}/{len(names)}] {nm[:30]:32s} -> CID {cid} {ik[:14]}", flush=True)
                continue
        print(f"[{i}/{len(names)}] {nm[:30]:32s} -> UNRESOLVED", flush=True)
        time.sleep(0.1)
    with open(CACHE, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["ligand_key", "smiles", "source"])
        for k, (s, src) in sorted(cache.items()): w.writerow([k, s, src])
    with open(PROV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["ligand_name", "name_cleaned", "cid", "inchikey", "smiles"]); w.writeheader(); w.writerows(prov)
    print(f"\nCID-anchored: {ok}/{len(names)} distinct ligands -> all traceable to a PubChem CID + InChIKey", flush=True)

if __name__ == "__main__":
    main()
