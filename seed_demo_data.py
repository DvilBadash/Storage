"""
Seed all three WMS databases from the real SAMPLE data files.
Run from the Storage root folder:  python seed_demo_data.py

Sources:
  SampleData/STOCK.xlsx     → OldWarehouseApp InventoryOld  (2 485 rows)
  SampleData/newBIns.xlsx   → NewWarehouseApp LocationNew   (4 179 rows)
  SampleData/FinalOutput.xlsx (Merge1 sheet)
                            → NewWarehouseApp Pallets + PalletItems (787 rows)
  StagingInventory in MergeTool is populated from STOCK.xlsx as well.
"""
import sys
import os
import sqlite3
import importlib
import openpyxl
from datetime import datetime

BASE       = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(BASE, "SampleData")
OLD_DB     = os.path.join(BASE, "OldWarehouseApp",  "old_warehouse.db")
NEW_DB     = os.path.join(BASE, "NewWarehouseApp",  "new_warehouse.db")
MRG_DB     = os.path.join(BASE, "MergeTool",        "merge_tool.db")


# ── Helper: raw sqlite connection ────────────────────────────────────────────
def conn(db_path):
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


# ── Helper: load module from app directory ───────────────────────────────────
def load_app_db(app_dir: str):
    full = os.path.join(BASE, app_dir)
    if full not in sys.path:
        sys.path.insert(0, full)
    mod_name = "database"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    return importlib.import_module(mod_name)


# ── Helper: read Excel with Hebrew/English headers ───────────────────────────
def read_xlsx(path: str, sheet: str = None) -> tuple[list[str], list[tuple]]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet and sheet in wb.sheetnames else wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return [], []
    headers = [str(h).strip() if h else "" for h in rows[0]]
    data = [r for r in rows[1:] if any(v is not None for v in r)]
    return headers, data


def cell(row, idx, default=""):
    if idx is None or idx >= len(row) or row[idx] is None:
        return default
    return str(row[idx]).strip()


def float_cell(row, idx, default=0.0):
    v = cell(row, idx, "")
    try:
        return float(v) if v else default
    except ValueError:
        return default


# ── 1. Init all databases ────────────────────────────────────────────────────
def init_all():
    print("Initialising databases...")
    # Delete new_warehouse.db so PalletID schema is recreated as TEXT
    if os.path.exists(NEW_DB):
        os.remove(NEW_DB)
        print("  [NewWarehouseApp] old DB deleted (schema migration to TEXT PalletID)")
    for app_dir in ["OldWarehouseApp", "NewWarehouseApp", "MergeTool"]:
        db_mod = load_app_db(app_dir)
        db_mod.init_db()
        print(f"  [{app_dir}] OK")


# ── 2. Seed OldWarehouseApp from STOCK.xlsx ──────────────────────────────────
def seed_old():
    print("\n[OldWarehouseApp] Loading STOCK.xlsx...")
    path = os.path.join(SAMPLE_DIR, "STOCK.xlsx")
    headers, rows = read_xlsx(path)

    # Build header → index map using the same map as excel_handler
    HMAP = {
        'מק"ט': "Pn", "חומר": "Cat", "יחידת מידה": "UnitOfMeasure",
        "סדרה": "Batch", "WBS": "WBS", "אתר אחסון": "Storage",
        "סוג איחסון": "Area", "איתור איחסון": "Bin",
        "מלאי זמין": "Qty", "אסטרטגיה ייעודית": "DestArea",
        "האם לפריט קיים יותר מאיתור יחיד": "MultiLocation",
    }
    idx = {}
    for i, h in enumerate(headers):
        field = HMAP.get(h)
        if field and field not in idx:
            idx[field] = i

    c = conn(OLD_DB)
    # Clear existing inventory
    c.execute("DELETE FROM PALLET_Assignment")
    c.execute("DELETE FROM InventoryOld")
    c.commit()

    # Add a default user if none
    c.execute("INSERT OR IGNORE INTO Users (FullName, IsActive) VALUES ('מנהל מחסן', 1)")
    c.commit()

    inserted = 0
    for row in rows:
        pn  = cell(row, idx.get("Pn"))
        if not pn:
            continue
        cat   = cell(row, idx.get("Cat"))
        uom   = cell(row, idx.get("UnitOfMeasure"))
        batch = cell(row, idx.get("Batch"))
        wbs   = cell(row, idx.get("WBS"))
        sto   = cell(row, idx.get("Storage"))
        area  = cell(row, idx.get("Area"))
        bin_  = cell(row, idx.get("Bin"))
        dest  = cell(row, idx.get("DestArea"))
        qty   = float_cell(row, idx.get("Qty"))
        multi = cell(row, idx.get("MultiLocation"))
        try:
            c.execute(
                """INSERT OR IGNORE INTO InventoryOld
                   (Cat,Pn,UnitOfMeasure,Batch,WBS,Storage,Area,Bin,DestArea,Qty,MultiLocation)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (cat, pn, uom, batch, wbs, sto, area, bin_, dest, qty, multi),
            )
            inserted += 1
        except Exception as e:
            print(f"  WARN row skip: {e}")
    c.commit()
    total = c.execute("SELECT COUNT(*) FROM InventoryOld").fetchone()[0]
    print(f"  InventoryOld: {total} rows ({inserted} inserted)")
    c.execute("INSERT OR REPLACE INTO Settings VALUES ('last_load_date',?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    c.commit()
    c.close()


# ── 3. Seed NewWarehouseApp from newBIns.xlsx + FinalOutput.xlsx ─────────────
def seed_new():
    print("\n[NewWarehouseApp] Loading newBIns.xlsx + FinalOutput.xlsx...")

    c = conn(NEW_DB)
    c.execute("INSERT OR IGNORE INTO Users (FullName, IsActive) VALUES ('מנהל מחסן', 1)")
    c.commit()

    # ── Locations from newBIns.xlsx ──────────────────────────────────────────
    loc_path = os.path.join(SAMPLE_DIR, "newBIns.xlsx")
    headers, rows = read_xlsx(loc_path)

    LOC_MAP = {"סביבתי / ממוזג": "Environment", "אזור WM": "DestArea", "איתור": "Dest_BIN"}
    lidx = {}
    for i, h in enumerate(headers):
        field = LOC_MAP.get(h)
        if field and field not in lidx:
            lidx[field] = i

    c.execute("DELETE FROM LocationNew")
    loc_inserted = 0
    for row in rows:
        env  = cell(row, lidx.get("Environment"))
        area = cell(row, lidx.get("DestArea"))
        bin_ = cell(row, lidx.get("Dest_BIN"))
        if area and bin_:
            try:
                c.execute(
                    "INSERT OR IGNORE INTO LocationNew (Environment,DestArea,Dest_BIN) VALUES (?,?,?)",
                    (env, area, bin_),
                )
                loc_inserted += 1
            except Exception:
                pass
    c.commit()
    total_loc = c.execute("SELECT COUNT(*) FROM LocationNew").fetchone()[0]
    print(f"  LocationNew: {total_loc} rows ({loc_inserted} inserted)")

    # ── Pallets + PalletItems from FinalOutput.xlsx Merge1 ───────────────────
    final_path = os.path.join(SAMPLE_DIR, "FinalOutput.xlsx")
    headers, rows = read_xlsx(final_path, sheet="Merge1")

    FMAP = {
        'מק"ט': "Pn", "חומר": "Material", "יחידת מידה": "UnitOfMeasure",
        "סדרה": "Batch", "WBS": "WBS", "אתר אחסון": "Storage",
        "סוג איחסון": "StorageType", "איתור איחסון": "Bin",
        "מלאי זמין": "Qty", "אסטרטגיה ייעודית": "DedicatedStrategy",
        "האם לפריט קיים יותר מאיתור יחיד": "MultiLocation",
        "Pallet": "PalletID", "Is_In_Stock": "IsInStock",
        "סביבתי / ממוזג": "Environment", "אזור WM": "WMArea",
        "איתור": "TargetBin",
    }
    fidx = {}
    for i, h in enumerate(headers):
        field = FMAP.get(h)
        if field and field not in fidx:
            fidx[field] = i

    c.execute("DELETE FROM PalletItems")
    c.execute("DELETE FROM Pallets")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pal_inserted = 0
    item_inserted = 0
    seen_pallets: set = set()

    for row in rows:
        raw_pid = cell(row, fidx.get("PalletID"))
        try:
            pid_num = int(float(raw_pid)) if raw_pid else None
        except ValueError:
            pid_num = None
        if pid_num is None:
            continue
        pid = f"P-{pid_num:03d}"

        if pid not in seen_pallets:
            seen_pallets.add(pid)
            target_bin = cell(row, fidx.get("TargetBin"))
            try:
                c.execute(
                    "INSERT OR IGNORE INTO Pallets (PalletID,CreateDate,CreateUser,Status,TargetBin) VALUES (?,?,?,?,?)",
                    (pid, now, "מנהל מחסן", "הוקם", target_bin or None),
                )
                pal_inserted += 1
            except Exception as e:
                print(f"  WARN pallet {pid}: {e}")

        pn    = cell(row, fidx.get("Pn"))
        mat   = cell(row, fidx.get("Material"))
        uom   = cell(row, fidx.get("UnitOfMeasure"))
        bat   = cell(row, fidx.get("Batch"))
        wbs   = cell(row, fidx.get("WBS"))
        sto   = cell(row, fidx.get("Storage"))
        stype = cell(row, fidx.get("StorageType"))
        bin_  = cell(row, fidx.get("Bin"))
        qty   = float_cell(row, fidx.get("Qty"))
        ded   = cell(row, fidx.get("DedicatedStrategy"))
        mul   = cell(row, fidx.get("MultiLocation"))
        env   = cell(row, fidx.get("Environment"))
        wma   = cell(row, fidx.get("WMArea"))
        is_in = 1 if cell(row, fidx.get("IsInStock")) in ("1", "כן", "true") else 0
        try:
            c.execute(
                """INSERT INTO PalletItems
                   (PalletID,Pn,Material,UnitOfMeasure,Batch,WBS,Storage,StorageType,
                    Bin,Qty,DedicatedStrategy,MultiLocation,Environment,WMArea,IsInStock)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (pid, pn, mat, uom, bat, wbs, sto, stype, bin_, qty,
                 ded, mul, env, wma, is_in),
            )
            item_inserted += 1
        except Exception as e:
            print(f"  WARN item row: {e}")

    c.commit()
    print(f"  Pallets: {pal_inserted}  |  PalletItems: {item_inserted}")
    c.execute("INSERT OR REPLACE INTO Settings VALUES ('last_pallet_import',?)", (now,))
    c.commit()
    c.close()


# ── 4. Seed MergeTool StagingInventory from STOCK.xlsx ───────────────────────
def seed_merge():
    print("\n[MergeTool] Loading STOCK.xlsx into StagingInventory...")
    path = os.path.join(SAMPLE_DIR, "STOCK.xlsx")
    headers, rows = read_xlsx(path)

    HMAP = {
        'מק"ט': "Pn", "חומר": "Cat", "יחידת מידה": "UnitOfMeasure",
        "סדרה": "Batch", "WBS": "WBS", "אתר אחסון": "Storage",
        "סוג איחסון": "Area", "איתור איחסון": "Bin",
        "מלאי זמין": "Qty", "אסטרטגיה ייעודית": "DestArea",
        "האם לפריט קיים יותר מאיתור יחיד": "MultiLocation",
    }
    idx = {}
    for i, h in enumerate(headers):
        field = HMAP.get(h)
        if field and field not in idx:
            idx[field] = i

    c = conn(MRG_DB)
    c.execute("INSERT OR IGNORE INTO Users (FullName, IsActive) VALUES ('מנהל מערכת', 1)")
    c.execute("DELETE FROM StagingInventory")
    c.commit()

    inserted = 0
    for row in rows:
        pn = cell(row, idx.get("Pn"))
        if not pn:
            continue
        try:
            c.execute(
                """INSERT INTO StagingInventory
                   (Cat,Pn,UnitOfMeasure,Batch,WBS,Storage,Area,Bin,
                    DestArea,Qty,MultiLocation)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    cell(row, idx.get("Cat")),
                    pn,
                    cell(row, idx.get("UnitOfMeasure")),
                    cell(row, idx.get("Batch")),
                    cell(row, idx.get("WBS")),
                    cell(row, idx.get("Storage")),
                    cell(row, idx.get("Area")),
                    cell(row, idx.get("Bin")),
                    cell(row, idx.get("DestArea")),
                    float_cell(row, idx.get("Qty")),
                    cell(row, idx.get("MultiLocation")),
                ),
            )
            inserted += 1
        except Exception as e:
            print(f"  WARN: {e}")
    c.commit()
    total = c.execute("SELECT COUNT(*) FROM StagingInventory").fetchone()[0]
    print(f"  StagingInventory: {total} rows ({inserted} inserted)")
    c.close()


# ── 5. Seed NewWarehouseApp pallet codes from Pallets.xlsx ───────────────────
def seed_pallet_codes():
    print("\n[NewWarehouseApp] Loading Pallets.xlsx (pallet code list)...")
    path = os.path.join(SAMPLE_DIR, "Pallets.xlsx")
    if not os.path.exists(path):
        print("  SKIP: SampleData/Pallets.xlsx not found")
        return
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    codes = [str(r[0]).strip() for r in rows[1:] if r[0] is not None]

    c = conn(NEW_DB)
    inserted = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for code in codes:
        try:
            c.execute(
                "INSERT OR IGNORE INTO Pallets (PalletID, CreateDate, CreateUser, Status) VALUES (?,?,?,?)",
                (code, now, "מערכת", "הוקם"),
            )
            inserted += 1
        except Exception as e:
            print(f"  WARN: {e}")
    c.commit()
    total = c.execute("SELECT COUNT(*) FROM Pallets").fetchone()[0]
    print(f"  Pallets (codes): {total} rows ({inserted} inserted)")
    c.close()


# ── 6. Summary ────────────────────────────────────────────────────────────────
def summary():
    print("\n" + "=" * 60)
    print(" Summary")
    print("=" * 60)
    queries = [
        ("OldWarehouseApp", OLD_DB, [
            ("InventoryOld",     "SELECT COUNT(*) FROM InventoryOld"),
            ("Pallets",          "SELECT COUNT(*) FROM Pallets"),
            ("PALLET_Assignment","SELECT COUNT(*) FROM PALLET_Assignment"),
        ]),
        ("NewWarehouseApp", NEW_DB, [
            ("LocationNew",  "SELECT COUNT(*) FROM LocationNew"),
            ("Pallets",      "SELECT COUNT(*) FROM Pallets"),
            ("PalletItems",  "SELECT COUNT(*) FROM PalletItems"),
        ]),
        ("MergeTool", MRG_DB, [
            ("StagingInventory", "SELECT COUNT(*) FROM StagingInventory"),
        ]),
    ]

    for label, db_path, qs in queries:
        print(f"\n  {label}:")
        c = conn(db_path)
        for name, sql in qs:
            cnt = c.execute(sql).fetchone()[0]
            print(f"    {name:<25} {cnt:>6} rows")
        c.close()
    print()


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print(" WMS Seeder – loading from SampleData/")
    print("=" * 60)
    init_all()
    seed_old()
    seed_new()
    seed_pallet_codes()
    seed_merge()
    summary()
    print("Done! All databases seeded from real SAMPLE data.")
