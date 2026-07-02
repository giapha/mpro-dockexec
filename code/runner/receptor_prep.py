#!/usr/bin/env python3
"""
Generalized receptor preparation for the Arm B runner.

For each unique target PDB in the manifest (runnable rows): fetch the PDB from
RCSB, strip waters + heteroatoms (keep protein ATOM records), and run meeko
mk_prepare_receptor.py to add hydrogens + charges and write a Vina-ready PDBQT
into runner/receptors/<PDB>.pdbqt (the cache the runner reads).

Run with the dock env python (meeko + vina), e.g.:
  /tmp/mm/envs/dock/bin/python receptor_prep.py
  /tmp/mm/envs/dock/bin/python receptor_prep.py --pdb 6W63 6Y2E

Failures are reported and skipped (no fabricated receptor). meeko may fail on
PDBs with non-standard residues/gaps; those are listed for manual prep.
NOTE: this prepares the STRUCTURE only; the docking BOX center per claim is the
span-parsed value in the manifest and must be human-verified before reruns count
as scientific evidence (R7).
"""
import argparse
import csv
import os
import subprocess
import urllib.request, ssl
_RCTX=ssl._create_unverified_context()

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(HERE, "receptors")
RAW = os.path.join(REC, "_raw")
BIN = os.environ.get("DOCK_BIN", "/tmp/mm/envs/dock/bin")


def fetch_pdb(pdb, dest):
    url = f"https://files.rcsb.org/download/{pdb.upper()}.pdb"
    try:
        with urllib.request.urlopen(url, timeout=40, context=_RCTX) as r:
            data = r.read().decode("utf-8", "replace")
        open(dest, "w").write(data)
        return True
    except Exception as e:
        print(f"  [{pdb}] fetch failed: {type(e).__name__} {e}")
        return False


def clean_protein(src, dest):
    """Keep protein ATOM records (+ TER); drop HETATM (waters/ligands/ions)."""
    kept = 0
    with open(src) as fh, open(dest, "w") as out:
        for line in fh:
            if line.startswith("ATOM") or line.startswith("TER"):
                out.write(line)
                kept += line.startswith("ATOM")
            elif line.startswith("END"):
                out.write("END\n")
    return kept


def prep(pdb, py):
    os.makedirs(RAW, exist_ok=True)
    raw = os.path.join(RAW, f"{pdb}.pdb")
    clean = os.path.join(RAW, f"{pdb}_protein.pdb")
    out_pdbqt = os.path.join(REC, f"{pdb}.pdbqt")
    if os.path.exists(out_pdbqt):
        print(f"  [{pdb}] already prepped"); return "cached"
    if os.path.exists(raw) and os.path.getsize(raw) > 1000:
        print(f"  [{pdb}] using pre-downloaded raw")        # fetched out-of-band (curl)
    elif not fetch_pdb(pdb, raw):
        return "fetch_failed"
    n = clean_protein(raw, clean)
    if n == 0:
        print(f"  [{pdb}] no ATOM records after clean"); return "empty"
    base = os.path.join(REC, pdb)
    cmd = [py, os.path.join(BIN, "mk_prepare_receptor.py"),
           "--read_pdb", clean, "-o", base, "-p",
           "--charge_model", "gasteiger", "-a", "--default_altloc", "A"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(out_pdbqt):
        print(f"  [{pdb}] OK -> receptors/{pdb}.pdbqt ({n} atoms)")
        return "ok"
    # meeko sometimes writes <base>.pdbqt under a slightly different name; check
    alt = base + ".pdbqt"
    if os.path.exists(alt) and alt != out_pdbqt:
        os.rename(alt, out_pdbqt); print(f"  [{pdb}] OK (renamed) -> {pdb}.pdbqt"); return "ok"
    print(f"  [{pdb}] meeko prep FAILED. stderr tail:\n    " +
          "\n    ".join((r.stderr or r.stdout or "").strip().splitlines()[-4:]))
    return "prep_failed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(HERE, "manifest.csv"))
    ap.add_argument("--pdb", nargs="*", help="explicit PDB list; default = unique runnable PDBs in manifest")
    args = ap.parse_args()
    os.makedirs(REC, exist_ok=True)
    py = os.path.join(BIN, "python")

    if args.pdb:
        pdbs = args.pdb
    else:
        rows = [r for r in csv.DictReader(open(args.manifest, encoding="utf-8")) if not r["needs"]]
        pdbs = sorted({r["target_pdb"] for r in rows if r["target_pdb"]})
    print(f"Preparing {len(pdbs)} receptors: {pdbs}")
    res = {p: prep(p, py) for p in pdbs}
    ok = [p for p, s in res.items() if s in ("ok", "cached")]
    print(f"\nReady receptors: {len(ok)}/{len(pdbs)} -> {ok}")
    fail = {p: s for p, s in res.items() if s not in ("ok", "cached")}
    if fail:
        print(f"Need manual prep: {fail}")


if __name__ == "__main__":
    main()
