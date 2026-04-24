import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "old_warehouse.db")
APP_NAME = "OldWarehouseApp"


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
            CREATE TABLE IF NOT EXISTS InventoryOld (
                InventoryID   INTEGER PRIMARY KEY AUTOINCREMENT,
                Cat           TEXT,
                Pn            TEXT NOT NULL,
                UnitOfMeasure TEXT NOT NULL DEFAULT '',
                Batch         TEXT NOT NULL DEFAULT '',
                WBS           TEXT NOT NULL DEFAULT '',
                Storage       TEXT NOT NULL DEFAULT '',
                Area          TEXT NOT NULL DEFAULT '',
                Bin           TEXT NOT NULL DEFAULT '',
                DestArea      TEXT,
                Qty           REAL,
                MultiLocation TEXT NOT NULL DEFAULT '',
                IsInStock     INTEGER NOT NULL DEFAULT 0,
                UNIQUE (Pn, Batch, WBS, Storage, Area, Bin)
            );
            CREATE TABLE IF NOT EXISTS Pallets (
                PalletID   INTEGER PRIMARY KEY,
                CreateDate TEXT,
                CreateUser TEXT,
                Status     TEXT DEFAULT 'הוקם'
            );
            CREATE TABLE IF NOT EXISTS PALLET_Assignment (
                AssignmentID INTEGER PRIMARY KEY AUTOINCREMENT,
                InventoryID  INTEGER NOT NULL,
                PalletID     INTEGER NOT NULL,
                IsInStock    INTEGER DEFAULT 0,
                TargetBin    TEXT,
                AssignDate   TEXT,
                FOREIGN KEY (InventoryID) REFERENCES InventoryOld(InventoryID),
                FOREIGN KEY (PalletID)   REFERENCES Pallets(PalletID),
                UNIQUE (InventoryID)
            );
        """)
        _seed_settings(c)
        # Migrations for existing databases
        for col, defn in [
            ("UnitOfMeasure", "TEXT NOT NULL DEFAULT ''"),
            ("MultiLocation",  "TEXT NOT NULL DEFAULT ''"),
            ("IsInStock",      "INTEGER NOT NULL DEFAULT 0"),
        ]:
            try:
                c.execute(f"ALTER TABLE InventoryOld ADD COLUMN {col} {defn}")
            except Exception:
                pass
        c.commit()


# Columns 1-14 map to the 14 content columns (col 0 = checkbox, no header needed)
DEFAULT_COL_HEADERS = {
    "inv_col_1":  'מק"ט',
    "inv_col_2":  "חומר",
    "inv_col_3":  "יחידת מידה",
    "inv_col_4":  "סדרה",
    "inv_col_5":  "WBS",
    "inv_col_6":  "אתר אחסון",
    "inv_col_7":  "סוג איחסון",
    "inv_col_8":  "איתור איחסון",
    "inv_col_9":  "אסטרטגיה ייעודית",
    "inv_col_10": "מלאי זמין",
    "inv_col_11": "האם > איתור אחד",
    "inv_col_12": "קיים פיזית",
    "inv_col_13": "⚠",
    "inv_col_14": "משטח",
}


def _seed_settings(c):
    defaults = [
        ("warehouse_name", "XXX"),
        ("theme", "light"),
        ("export_path", os.path.expanduser("~/Desktop")),
        ("archive_path", os.path.join(os.path.dirname(DB_PATH), "archive")),
        ("last_load_date", ""),
    ]
    for k, v in defaults:
        c.execute("INSERT OR IGNORE INTO Settings VALUES (?,?)", (k, v))
    for k, v in DEFAULT_COL_HEADERS.items():
        c.execute("INSERT OR IGNORE INTO Settings VALUES (?,?)", (k, v))
    for i in range(1, 15):
        c.execute("INSERT OR IGNORE INTO Settings VALUES (?,?)", (f"inv_col_{i}_hidden", "0"))


def get_column_headers() -> list[str]:
    """Returns 15-element list: index 0 = '' (checkbox col), 1-14 = custom/default labels."""
    result = [""]
    for i in range(1, 15):
        result.append(get_setting(f"inv_col_{i}", DEFAULT_COL_HEADERS.get(f"inv_col_{i}", "")))
    return result


def set_column_header(col_index: int, label: str):
    set_setting(f"inv_col_{col_index}", label)


def get_col_hidden(col_index: int) -> bool:
    return get_setting(f"inv_col_{col_index}_hidden", "0") == "1"


def set_col_hidden(col_index: int, hidden: bool):
    set_setting(f"inv_col_{col_index}_hidden", "1" if hidden else "0")


# ── Settings ─────────────────────────────────────────────────────────────────

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


def set_user_active(user_id: int, active: bool):
    with get_conn() as c:
        c.execute("UPDATE Users SET IsActive=? WHERE UserID=?", (1 if active else 0, user_id))
        c.commit()


# ── Inventory ─────────────────────────────────────────────────────────────────

def get_inventory_with_assignments(pn="", storage="", area="", bin_="",
                                    limit=500, unassigned_only=False):
    sql = """
        SELECT i.InventoryID, i.Cat, i.Pn, i.UnitOfMeasure, i.Batch, i.WBS,
               i.Storage, i.Area, i.Bin, i.DestArea, i.Qty, i.MultiLocation,
               i.IsInStock,
               pa.PalletID, pa.AssignDate
        FROM InventoryOld i
        LEFT JOIN PALLET_Assignment pa ON i.InventoryID = pa.InventoryID
        WHERE 1=1
    """
    params: list = []
    if pn:
        sql += " AND i.Pn LIKE ?";      params.append(f"%{pn}%")
    if storage:
        sql += " AND i.Storage = ?";    params.append(storage)
    if area:
        sql += " AND i.Area = ?";       params.append(area)
    if bin_:
        sql += " AND i.Bin = ?";        params.append(bin_)
    if unassigned_only:
        sql += " AND pa.PalletID IS NULL"
    sql += f" ORDER BY i.Pn, i.Batch LIMIT {int(limit) + 1}"
    with get_conn() as c:
        return c.execute(sql, params).fetchall()


def get_inventory(pn="", storage="", area="", bin_=""):
    return get_inventory_with_assignments(pn, storage, area, bin_, limit=500)


def get_distinct_values(col: str):
    allowed = {"Storage", "Area", "Bin", "Pn"}
    if col not in allowed:
        return []
    with get_conn() as c:
        rows = c.execute(
            f"SELECT DISTINCT {col} FROM InventoryOld "
            f"WHERE {col} IS NOT NULL AND {col}!='' ORDER BY {col}"
        ).fetchall()
    return [r[0] for r in rows]


def set_is_in_stock(inv_id: int, value: bool, user: str):
    with get_conn() as c:
        c.execute("UPDATE InventoryOld SET IsInStock=? WHERE InventoryID=?",
                  (1 if value else 0, inv_id))
        c.commit()
    log(user, "UPDATE_ISINSTOCK", f"InventoryID={inv_id} IsInStock={value}")


def upsert_is_in_stock(inv_id: int, value: bool, user: str):
    set_is_in_stock(inv_id, value, user)


# ── Pallets ───────────────────────────────────────────────────────────────────

def pallet_exists(pallet_id: int) -> bool:
    with get_conn() as c:
        return bool(c.execute("SELECT 1 FROM Pallets WHERE PalletID=?", (pallet_id,)).fetchone())


def create_pallet(pallet_id: int, user: str):
    if pallet_exists(pallet_id):
        raise ValueError(f"משטח {pallet_id} כבר קיים במערכת")
    with get_conn() as c:
        c.execute(
            "INSERT INTO Pallets (PalletID, CreateDate, CreateUser) VALUES (?,?,?)",
            (pallet_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user),
        )
        c.commit()
    log(user, "CREATE_PALLET", f"PalletID={pallet_id}")


def get_pallets():
    with get_conn() as c:
        return c.execute("SELECT * FROM Pallets ORDER BY PalletID").fetchall()


def import_pallets_from_rows(rows: list[dict], user: str) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    assigned = 0
    not_found = []
    with get_conn() as c:
        for r in rows:
            try:
                pid = int(float(str(r.get("PalletID", ""))))
            except (ValueError, TypeError):
                continue
            pn      = str(r.get("PN",      r.get("Pn", "")) or "").strip()
            batch   = str(r.get("Batch",   "") or "").strip()
            wbs     = str(r.get("WBS",     "") or "").strip()
            storage = str(r.get("Storage", "") or "").strip()
            area    = str(r.get("Area",    "") or "").strip()
            bin_    = str(r.get("Bin",     "") or "").strip()
            inv_row = c.execute(
                """SELECT InventoryID FROM InventoryOld
                   WHERE Pn=? AND Batch=? AND WBS=? AND Storage=? AND Area=? AND Bin=?""",
                (pn, batch, wbs, storage, area, bin_),
            ).fetchone()
            if not inv_row:
                not_found.append(f"PN={pn}  Batch={batch}  Storage={storage}/{area}/{bin_}")
                continue
            inv_id = inv_row[0]
            c.execute(
                """INSERT OR IGNORE INTO Pallets (PalletID, CreateDate, CreateUser, Status)
                   VALUES (?, ?, ?, ?)""",
                (pid,
                 r.get("CreateDate", now) or now,
                 r.get("CreateUser", user) or user,
                 r.get("Status", "הוקם") or "הוקם"),
            )
            c.execute(
                """INSERT OR IGNORE INTO PALLET_Assignment
                   (InventoryID, PalletID, AssignDate)
                   VALUES (?, ?, ?)""",
                (inv_id, pid, now),
            )
            assigned += 1
        c.commit()
    log(user, "IMPORT_PALLETS",
        f"שויכו: {assigned} | לא נמצאו: {len(not_found)}")
    return {"assigned": assigned, "not_found": not_found}


def detach_item_from_pallet(inv_id: int, user: str):
    with get_conn() as c:
        c.execute("DELETE FROM PALLET_Assignment WHERE InventoryID=?", (inv_id,))
        c.commit()
    log(user, "DETACH_FROM_PALLET", f"InventoryID={inv_id}")


def assign_items_to_pallet(inv_ids: list, pallet_id: int, user: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as c:
        for inv_id in inv_ids:
            row = c.execute("SELECT IsInStock FROM InventoryOld WHERE InventoryID=?", (inv_id,)).fetchone()
            is_in = row["IsInStock"] if row else 0
            existing = c.execute("SELECT AssignmentID FROM PALLET_Assignment WHERE InventoryID=?", (inv_id,)).fetchone()
            if existing:
                c.execute(
                    "UPDATE PALLET_Assignment SET PalletID=?, IsInStock=?, AssignDate=? WHERE InventoryID=?",
                    (pallet_id, is_in, now, inv_id),
                )
            else:
                c.execute(
                    "INSERT INTO PALLET_Assignment (InventoryID,PalletID,IsInStock,AssignDate) VALUES (?,?,?,?)",
                    (inv_id, pallet_id, is_in, now),
                )
        c.commit()
    log(user, "ASSIGN_PALLET", f"PalletID={pallet_id} items={inv_ids}")


def get_pallet_items(pallet_id: int):
    with get_conn() as c:
        return c.execute(
            """SELECT i.*, pa.IsInStock, pa.AssignDate
               FROM PALLET_Assignment pa
               JOIN InventoryOld i ON pa.InventoryID = i.InventoryID
               WHERE pa.PalletID=?
               ORDER BY i.Pn""",
            (pallet_id,),
        ).fetchall()


# ── Inventory load / export ────────────────────────────────────────────────────

def clear_inventory():
    with get_conn() as c:
        c.execute("DELETE FROM PALLET_Assignment")
        c.execute("DELETE FROM InventoryOld")
        c.commit()


def bulk_insert_inventory(rows: list[dict]):
    with get_conn() as c:
        for r in rows:
            c.execute(
                """INSERT OR IGNORE INTO InventoryOld
                   (Cat,Pn,UnitOfMeasure,Batch,WBS,Storage,Area,Bin,DestArea,Qty,MultiLocation)
                   VALUES (:Cat,:Pn,:UnitOfMeasure,:Batch,:WBS,:Storage,:Area,:Bin,:DestArea,:Qty,:MultiLocation)""",
                r,
            )
        c.commit()


def get_all_inventory_with_assignments():
    with get_conn() as c:
        return c.execute(
            """SELECT i.*, pa.PalletID, pa.IsInStock, pa.AssignDate, pa.TargetBin
               FROM InventoryOld i
               LEFT JOIN PALLET_Assignment pa ON i.InventoryID = pa.InventoryID
               ORDER BY i.Pn, i.Batch"""
        ).fetchall()


def update_last_load_date():
    set_setting("last_load_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
