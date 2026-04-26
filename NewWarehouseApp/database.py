import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "new_warehouse.db")
APP_NAME = "NewWarehouseApp"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    with get_conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS Users (
                UserID   INTEGER PRIMARY KEY AUTOINCREMENT,
                FullName TEXT    NOT NULL UNIQUE,
                IsActive INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS Settings (
                SettingKey   TEXT PRIMARY KEY,
                SettingValue TEXT
            );
            CREATE TABLE IF NOT EXISTS LogEntries (
                LogID           INTEGER PRIMARY KEY AUTOINCREMENT,
                Timestamp       TEXT NOT NULL,
                UserName        TEXT,
                ApplicationName TEXT,
                ActionType      TEXT,
                Details         TEXT
            );
            CREATE TABLE IF NOT EXISTS LocationNew (
                LocationID  INTEGER PRIMARY KEY AUTOINCREMENT,
                Environment TEXT NOT NULL DEFAULT '',
                DestArea    TEXT NOT NULL,
                Dest_BIN    TEXT NOT NULL,
                UNIQUE (DestArea, Dest_BIN)
            );
            CREATE TABLE IF NOT EXISTS Pallets (
                PalletID   TEXT PRIMARY KEY,
                CreateDate TEXT,
                CreateUser TEXT,
                Status     TEXT DEFAULT 'הוקם',
                TargetBin  TEXT,
                AssignDate TEXT
            );
            CREATE TABLE IF NOT EXISTS PalletItems (
                ItemID            INTEGER PRIMARY KEY AUTOINCREMENT,
                PalletID          TEXT NOT NULL,
                Pn                TEXT,
                Material          TEXT,
                UnitOfMeasure     TEXT,
                Batch             TEXT,
                WBS               TEXT,
                Storage           TEXT,
                StorageType       TEXT,
                Bin               TEXT,
                Qty               REAL,
                DedicatedStrategy TEXT,
                MultiLocation     TEXT,
                Environment       TEXT,
                WMArea            TEXT,
                IsInStock         INTEGER DEFAULT 0,
                FOREIGN KEY (PalletID) REFERENCES Pallets(PalletID)
            );
        """)
        _seed_settings(c)
        # Migrations for existing databases
        for col, defn in [
            ("Environment",      "TEXT NOT NULL DEFAULT ''"),
            ("Material",         "TEXT DEFAULT ''"),
            ("UnitOfMeasure",    "TEXT DEFAULT ''"),
            ("StorageType",      "TEXT DEFAULT ''"),
            ("DedicatedStrategy","TEXT DEFAULT ''"),
            ("MultiLocation",    "TEXT DEFAULT ''"),
            ("WMArea",           "TEXT DEFAULT ''"),
        ]:
            try:
                c.execute(f"ALTER TABLE PalletItems ADD COLUMN {col} {defn}")
            except Exception:
                pass
        try:
            c.execute("ALTER TABLE LocationNew ADD COLUMN Environment TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass
        _migrate_pallet_id_to_text(c)
        c.commit()


# 11 item columns matching STOCK.xlsx field names
DEFAULT_ITEM_HEADERS = {
    "item_col_0":  'מק"ט',
    "item_col_1":  "חומר",
    "item_col_2":  "יחידת מידה",
    "item_col_3":  "סדרה",
    "item_col_4":  "WBS",
    "item_col_5":  "אתר אחסון",
    "item_col_6":  "סוג איחסון",
    "item_col_7":  "איתור איחסון",
    "item_col_8":  "מלאי זמין",
    "item_col_9":  "אסטרטגיה ייעודית",
    "item_col_10": "האם > איתור אחד",
}

DEFAULT_PAL_HEADERS = {
    "pal_col_0": "מספר משטח",
    "pal_col_1": "סטטוס",
    "pal_col_2": "איתור יעד",
    "pal_col_3": "תאריך שיוך",
    "pal_col_4": "פריטים",
    "pal_col_5": "עדכן סטטוס",
}


def _migrate_pallet_id_to_text(c):
    """Migrate PalletID from INTEGER to TEXT in Pallets and PalletItems."""
    cols = c.execute("PRAGMA table_info(Pallets)").fetchall()
    needs_migration = any(
        col[1] == "PalletID" and col[2].upper() == "INTEGER" for col in cols
    )
    if not needs_migration:
        return
    c.executescript("""
        ALTER TABLE PalletItems RENAME TO PalletItems_old;
        ALTER TABLE Pallets RENAME TO Pallets_old;
        CREATE TABLE Pallets (
            PalletID   TEXT PRIMARY KEY,
            CreateDate TEXT,
            CreateUser TEXT,
            Status     TEXT DEFAULT 'הוקם',
            TargetBin  TEXT,
            AssignDate TEXT
        );
        CREATE TABLE PalletItems (
            ItemID            INTEGER PRIMARY KEY AUTOINCREMENT,
            PalletID          TEXT NOT NULL,
            Pn                TEXT,
            Material          TEXT DEFAULT '',
            UnitOfMeasure     TEXT DEFAULT '',
            Batch             TEXT,
            WBS               TEXT,
            Storage           TEXT,
            StorageType       TEXT DEFAULT '',
            Bin               TEXT,
            Qty               REAL,
            DedicatedStrategy TEXT DEFAULT '',
            MultiLocation     TEXT DEFAULT '',
            Environment       TEXT DEFAULT '',
            WMArea            TEXT DEFAULT '',
            IsInStock         INTEGER DEFAULT 0,
            FOREIGN KEY (PalletID) REFERENCES Pallets(PalletID)
        );
        INSERT INTO Pallets
            SELECT CAST(PalletID AS TEXT), CreateDate, CreateUser, Status, TargetBin, AssignDate
            FROM Pallets_old;
        INSERT INTO PalletItems
            SELECT ItemID, CAST(PalletID AS TEXT), Pn,
                   COALESCE(Material,''), COALESCE(UnitOfMeasure,''),
                   Batch, WBS, Storage, COALESCE(StorageType,''), Bin, Qty,
                   COALESCE(DedicatedStrategy,''), COALESCE(MultiLocation,''),
                   COALESCE(Environment,''), COALESCE(WMArea,''), IsInStock
            FROM PalletItems_old;
        DROP TABLE PalletItems_old;
        DROP TABLE Pallets_old;
    """)


def _normalize_pid(pid) -> str | None:
    """Normalize a pallet ID to text form. Numeric 1 → 'P-001'; 'P-001' kept as-is."""
    if pid is None:
        return None
    s = str(pid).strip()
    if not s:
        return None
    if s.upper().startswith("P-"):
        return s.upper()
    try:
        return f"P-{int(float(s)):03d}"
    except (ValueError, TypeError):
        return s


def _seed_settings(c):
    defaults = [
        ("warehouse_name", "YYY"),
        ("theme", "light"),
        ("export_path",  r"C:\Temp\New_WH_EXP"),
        ("archive_path", r"C:\Temp\New_WH_Archive"),
        ("last_load_date", ""),
        ("last_pallet_import", ""),
    ]
    for k, v in defaults:
        c.execute("INSERT OR IGNORE INTO Settings VALUES (?,?)", (k, v))
    # Migrate old Desktop / local-archive paths that were seeded in earlier versions
    _old_export  = os.path.expanduser("~/Desktop")
    _old_archive = os.path.join(os.path.dirname(DB_PATH), "archive")
    c.execute("UPDATE Settings SET SettingValue=? WHERE SettingKey='export_path'  AND SettingValue=?",
              (r"C:\Temp\New_WH_EXP",     _old_export))
    c.execute("UPDATE Settings SET SettingValue=? WHERE SettingKey='archive_path' AND SettingValue=?",
              (r"C:\Temp\New_WH_Archive",  _old_archive))
    for k, v in {**DEFAULT_ITEM_HEADERS, **DEFAULT_PAL_HEADERS}.items():
        c.execute("INSERT OR IGNORE INTO Settings VALUES (?,?)", (k, v))
    for k in {**DEFAULT_ITEM_HEADERS, **DEFAULT_PAL_HEADERS}.keys():
        c.execute("INSERT OR IGNORE INTO Settings VALUES (?,?)", (f"{k}_hidden", "0"))


def get_item_headers() -> list[str]:
    return [get_setting(f"item_col_{i}", DEFAULT_ITEM_HEADERS.get(f"item_col_{i}", ""))
            for i in range(11)]


def get_pal_headers() -> list[str]:
    return [get_setting(f"pal_col_{i}", DEFAULT_PAL_HEADERS.get(f"pal_col_{i}", ""))
            for i in range(6)]


def set_col_header(key: str, label: str):
    set_setting(key, label)


def get_col_hidden(key: str) -> bool:
    return get_setting(f"{key}_hidden", "0") == "1"


def set_col_hidden(key: str, hidden: bool):
    set_setting(f"{key}_hidden", "1" if hidden else "0")


# ── Settings ──────────────────────────────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    with get_conn() as c:
        row = c.execute("SELECT SettingValue FROM Settings WHERE SettingKey=?", (key,)).fetchone()
    return row[0] if row else default


def set_setting(key: str, value: str):
    with get_conn() as c:
        c.execute("INSERT OR REPLACE INTO Settings VALUES (?,?)", (key, value))
        c.commit()


# ── Log ───────────────────────────────────────────────────────────────────────

def log(user: str, action: str, details: str = ""):
    with get_conn() as c:
        c.execute(
            "INSERT INTO LogEntries (Timestamp,UserName,ApplicationName,ActionType,Details) VALUES (?,?,?,?,?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user, APP_NAME, action, details),
        )
        c.commit()


def get_logs(from_date="", to_date="", user="", action="", search=""):
    sql = "SELECT * FROM LogEntries WHERE 1=1"
    params = []
    if from_date:
        sql += " AND Timestamp >= ?"; params.append(from_date + " 00:00:00")
    if to_date:
        sql += " AND Timestamp <= ?"; params.append(to_date + " 23:59:59")
    if user:
        sql += " AND UserName LIKE ?"; params.append(f"%{user}%")
    if action:
        sql += " AND ActionType = ?"; params.append(action)
    if search:
        sql += " AND Details LIKE ?"; params.append(f"%{search}%")
    sql += " ORDER BY LogID DESC LIMIT 500"
    with get_conn() as c:
        return c.execute(sql, params).fetchall()


# ── Users ─────────────────────────────────────────────────────────────────────

def get_active_users():
    with get_conn() as c:
        return c.execute("SELECT * FROM Users WHERE IsActive=1 ORDER BY FullName").fetchall()


def get_all_users():
    with get_conn() as c:
        return c.execute("SELECT * FROM Users ORDER BY FullName").fetchall()


def add_user(name: str):
    with get_conn() as c:
        c.execute("INSERT INTO Users (FullName) VALUES (?)", (name,))
        c.commit()


def set_user_active(uid: int, active: bool):
    with get_conn() as c:
        c.execute("UPDATE Users SET IsActive=? WHERE UserID=?", (1 if active else 0, uid))
        c.commit()


# ── Locations ────────────────────────────────────────────────────────────────

def get_dest_areas():
    with get_conn() as c:
        rows = c.execute("SELECT DISTINCT DestArea FROM LocationNew ORDER BY DestArea").fetchall()
    return [r[0] for r in rows]


def get_all_dest_bins():
    """Return all locations from LocationNew ordered by area and bin."""
    with get_conn() as c:
        return c.execute(
            "SELECT DestArea, Dest_BIN, Environment FROM LocationNew ORDER BY DestArea, Dest_BIN"
        ).fetchall()


def get_bins_for_area(area: str):
    with get_conn() as c:
        rows = c.execute(
            "SELECT Dest_BIN FROM LocationNew WHERE DestArea=? ORDER BY Dest_BIN", (area,)
        ).fetchall()
    return [r[0] for r in rows]


def clear_locations():
    with get_conn() as c:
        c.execute("DELETE FROM LocationNew")
        c.commit()


def reset_all_data():
    """Delete all pallets, pallet items and locations."""
    with get_conn() as c:
        c.execute("DELETE FROM PalletItems")
        c.execute("DELETE FROM Pallets")
        c.execute("DELETE FROM LocationNew")
        c.commit()


def bulk_insert_locations(rows: list[dict]):
    with get_conn() as c:
        for r in rows:
            c.execute(
                """INSERT OR IGNORE INTO LocationNew (Environment, DestArea, Dest_BIN)
                   VALUES (:Environment, :DestArea, :Dest_BIN)""",
                r,
            )
        c.commit()


# ── Pallets ───────────────────────────────────────────────────────────────────

def get_pallets(status_filter="", unassigned_only=False):
    conditions, params = [], []
    if status_filter:
        conditions.append("Status=?")
        params.append(status_filter)
    if unassigned_only:
        conditions.append("(TargetBin IS NULL OR TargetBin='')")
    sql = "SELECT * FROM Pallets"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY CAST(SUBSTR(PalletID, 3) AS INTEGER)"
    with get_conn() as c:
        return c.execute(sql, params).fetchall()


def get_pallet(pallet_id: str):
    with get_conn() as c:
        return c.execute("SELECT * FROM Pallets WHERE PalletID=?", (pallet_id,)).fetchone()


def get_pallet_items(pallet_id: str):
    with get_conn() as c:
        return c.execute(
            "SELECT * FROM PalletItems WHERE PalletID=? ORDER BY Pn", (pallet_id,)
        ).fetchall()


def assign_pallet_to_bin(pallet_id: str, target_bin: str, status: str, user: str):
    if not get_pallet(pallet_id):
        raise ValueError(f"משטח {pallet_id} לא נמצא")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as c:
        c.execute(
            "UPDATE Pallets SET TargetBin=?, Status=?, AssignDate=? WHERE PalletID=?",
            (target_bin, status, now, pallet_id),
        )
        c.commit()
    log(user, "ASSIGN_PALLET_BIN", f"PalletID={pallet_id} TargetBin={target_bin} Status={status}")


def update_pallet_status(pallet_id: str, status: str, user: str):
    with get_conn() as c:
        c.execute("UPDATE Pallets SET Status=? WHERE PalletID=?", (status, pallet_id))
        c.commit()
    log(user, "UPDATE_PALLET_STATUS", f"PalletID={pallet_id} Status={status}")


def import_pallets_from_rows(rows: list[dict], user: str):
    """Import pallet rows from FinalOutput.xlsx or a pallet export file. Clears existing data first."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as c:
        c.execute("DELETE FROM PalletItems")
        c.execute("DELETE FROM Pallets")
        for r in rows:
            pid = _normalize_pid(r.get("PalletID") or r.get("Pallet"))
            if pid is None:
                continue
            c.execute(
                """INSERT OR IGNORE INTO Pallets (PalletID, CreateDate, CreateUser, Status)
                   VALUES (?, ?, ?, ?)""",
                (pid, r.get("CreateDate", now), r.get("CreateUser", user),
                 r.get("Status", "הוקם")),
            )
            try:
                qty = float(str(r.get("Qty", 0) or 0))
            except (ValueError, TypeError):
                qty = 0.0
            c.execute(
                """INSERT INTO PalletItems
                   (PalletID, Pn, Material, UnitOfMeasure, Batch, WBS, Storage,
                    StorageType, Bin, Qty, DedicatedStrategy, MultiLocation,
                    Environment, WMArea, IsInStock)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    pid,
                    r.get("Pn",  r.get("PN",  r.get('מק"ט',  ""))),
                    r.get("Material",          r.get("חומר",           "")),
                    r.get("UnitOfMeasure",     r.get("יחידת מידה",     "")),
                    r.get("Batch",             r.get("סדרה",           "")),
                    r.get("WBS",               r.get("WBS",            "")),
                    r.get("Storage",           r.get("אתר אחסון",      "")),
                    r.get("StorageType",       r.get("סוג איחסון",     r.get("Area", ""))),
                    r.get("Bin",               r.get("איתור איחסון",   "")),
                    qty,
                    r.get("DedicatedStrategy", r.get("אסטרטגיה ייעודית", "")),
                    r.get("MultiLocation",     r.get("האם > איתור אחד",  "")),
                    r.get("Environment",       r.get("סביבתי / ממוזג",   "")),
                    r.get("WMArea",            r.get("אזור WM",           "")),
                    1 if r.get("IsInStock") or r.get("Is_In_Stock") else 0,
                ),
            )
        c.commit()
    set_setting("last_pallet_import", now)
    log(user, "IMPORT_PALLETS", f"יובאו {len(rows)} שורות")


def bulk_insert_pallet_codes(codes: list[str], user: str = "מערכת"):
    """Pre-populate the Pallets table with pallet IDs from Pallets.xlsx (no items). Clears existing data first."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as c:
        c.execute("DELETE FROM PalletItems")
        c.execute("DELETE FROM Pallets")
        for code in codes:
            pid = _normalize_pid(code)
            if pid:
                c.execute(
                    "INSERT OR IGNORE INTO Pallets (PalletID, CreateDate, CreateUser, Status) VALUES (?,?,?,?)",
                    (pid, now, user, "הוקם"),
                )
        c.commit()
    set_setting("last_pallet_import", now)
    log(user, "LOAD_PALLET_CODES", f"נטענו {len(codes)} קודי משטח")


def get_all_pallets_export():
    with get_conn() as c:
        return c.execute(
            """SELECT p.PalletID, p.Status, p.TargetBin, p.AssignDate,
                      pi.Pn, pi.Material, pi.UnitOfMeasure, pi.Batch, pi.WBS,
                      pi.Storage, pi.StorageType, pi.Bin, pi.Qty,
                      pi.DedicatedStrategy, pi.MultiLocation,
                      pi.Environment, pi.WMArea, pi.IsInStock
               FROM Pallets p
               LEFT JOIN PalletItems pi ON p.PalletID = pi.PalletID
               ORDER BY p.PalletID"""
        ).fetchall()
