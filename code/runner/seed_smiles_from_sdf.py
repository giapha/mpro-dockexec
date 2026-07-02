#!/usr/bin/env python3
"""
Offline SMILES seeding — populate smiles_cache.csv from already-prepared ligand
SDF files (Paper 1 reruns + this runner's cache), WITHOUT touching PubChem.

Use when PubChem is throttled/unreachable. Run with the dock env python (rdkit):
  /tmp/mm/envs/dock/bin/python seed_smiles_from_sdf.py

Maps SDF filename -> normalized ligand name -> manifest ligand_key, extracts the
canonical SMILES via RDKit, and merges into runner/out/smiles_cache.csv.
"""
import csv, glob, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
CACHE = os.path.join(OUT, "smiles_cache.csv")
SDF_DIRS = [
    os.path.normpath(os.path.join(HERE, "..", "..", "Paper1_Audit", "08_manuscript_v0.3", "reexecution", "ligands")),
    os.path.join(OUT, "ligands"),
]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def main():
    from rdkit import Chem
    # manifest ligand keys (runnable) -> normalized
    man = [r for r in csv.DictReader(open(os.path.join(HERE, "manifest.csv"), encoding="utf-8")) if not r["needs"]]
    key_by_norm = {}
    for r in man:
        k = r["ligand_name"] or r["ligand_id"]
        key_by_norm.setdefault(norm(k), k)

    # extract SMILES from every SDF, mapping filename (minus Pxxxx_ prefix) -> norm
    found = {}
    for d in SDF_DIRS:
        for sdf in glob.glob(os.path.join(d, "*.sdf")):
            base = os.path.splitext(os.path.basename(sdf))[0]
            base = re.sub(r"^P\d+[a-z]?_", "", base)          # strip P0016_ etc.
            base = re.sub(r"_[0-9a-f]{6,}$", "", base)         # strip hash suffix
            try:
                m = next(iter(Chem.SDMolSupplier(sdf, removeHs=False)))
                if m is None: continue
                smi = Chem.MolToSmiles(Chem.RemoveHs(m))
            except Exception:
                continue
            n = norm(base)
            if n and n not in found:
                found[n] = smi

    # merge into cache (don't overwrite existing non-empty)
    existing = {}
    if os.path.exists(CACHE):
        for r in csv.DictReader(open(CACHE, encoding="utf-8")):
            existing[r["ligand_key"]] = (r["smiles"], r["source"])

    added = 0
    for n, smi in found.items():
        key = key_by_norm.get(n)
        if key and (key not in existing or not existing[key][0]):
            existing[key] = (smi, "offline_sdf")
            added += 1

    with open(CACHE, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["ligand_key", "smiles", "source"]); w.writeheader()
        for k, (s, src) in existing.items():
            w.writerow({"ligand_key": k, "smiles": s, "source": src})
    ok = sum(1 for v in existing.values() if v[0])
    print(f"Seeded {added} SMILES from offline SDFs; cache now {ok}/{len(existing)} resolved -> out/smiles_cache.csv")
    print(f"  matched manifest ligands: {sorted(key_by_norm[n] for n in found if n in key_by_norm)[:20]}")


if __name__ == "__main__":
    main()
