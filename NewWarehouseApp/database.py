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
                LocationID INTEGER PRIMARY KEY AUTOINCREMENT,
                DestArea   TEXT NOT NULL,
                Dest_BIN   TEXT NOT NULL,
                UNIQUE (DestArea, Dest_BIN)
            );
            CREATE TABLE IF NOT EXISTS Pallets (
                PalletID   INTEGER PRIMARY KEY,
                CreateDate TEXT,
                CreateUser TEXT,
                Status     TEXT DEFAULT 'הוקם',
                TargetBin  TEXT,
                AssignDate TEXT
            );
            CREATE TABLE IF NOT EXISTS PalletItems (
                ItemID    INTEGER PRIMARY KEY AUTOINCREMENT,
                PalletID  INTEGER NOT NULL,
                Pn        TEXT,
                Batch     TEXT,
                WBS       TEXT,
                Storage   TEXT,
                Area      TEXT,
                Bin       TEXT,
                Qty       REAL,
                IsInStock INTEGER DEFAULT 0,
                FOREIGN KEY (PalletID) REFERENCES Pallets(PalletID)
            );
        """)
        _seed_settings(c)
        c.commit()


DEFAULT_ITEM_HEADERS = {
    "item_col_0": "PN",
    "item_col_1": "אצווה",
    "item_col_2": "WBS",
    "item_col_3": "אחסון",
    "item_col_4": "אזור",
    "item_col_5": "Bin",
    "item_col_6": "כמות",
}

DEFAULT_PAL_HEADERS = {
    "pal_col_0": "מספר משטח",
    "pal_col_1": "סטטוס",
    "pal_col_2": "איתור יעד",
    "pal_col_3": "תאריך שיוך",
    "pal_col_4": "פריטים",
    "pal_col_5": "עדכן סטטוס",
}


def _seed_settings(c):
    defaults = [
        ("warehouse_name", "YYY"),
        ("theme", "light"),
        ("export_path", os.path.expanduser("~/Desktop")),
        ("archive_path", os.path.join(os.path.dirname(DB_PATH), "archive")),
        ("last_load_date", ""),
        ("last_pallet_import", ""),
    ]
    for k, v in defaults:
        c.execute("INSERT OR IGNORE INTO Settings VALUES (?,?)", (k, v))
    for k, v in {**DEFAULT_ITEM_HEADERS, **DEFAULT_PAL_HEADERS}.items():
        c.execute("INSERT OR IGNORE INTO Settings VALUES (?,?)", (k, v))
    for k in {**DEFAULT_ITEM_HEADERS, **DEFAULT_PAL_HEADERS}.keys():
        c.execute("INSERT OR IGNORE INTO Settings VALUES (?,?)", (f"{k}_hidden", "0"))


def get_item_headers() -> list[str]:
    return [get_setting(f"item_col_{i}", DEFAULT_ITEM_HEADERS.get(f"item_col_{i}", ""))
            for i in range(7)]


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


def bulk_insert_locations(rows: list[dict]):
    with get_conn() as c:
        for r in rows:
            c.execute(
                "INSERT OR IGNORE INTO LocationNew (DestArea, Dest_BIN) VALUES (:DestArea, :Dest_BIN)",
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
    sql += " ORDER BY PalletID"
    with get_conn() as c:
        return c.execute(sql, params).fetchall()


def get_pallet(pallet_id: int):
    with get_conn() as c:
        return c.execute("SELECT * FROM Pallets WHERE PalletID=?", (pallet_id,)).fetchone()


def get_pallet_items(pallet_id: int):
    with get_conn() as c:
        return c.execute(
            "SELECT * FROM PalletItems WHERE PalletID=? ORDER BY Pn", (pallet_id,)
        ).fetchall()


def assign_pallet_to_bin(pallet_id: int, target_bin: str, user: str):
    pallet = get_pallet(pallet_id)
    if not pallet:
        raise ValueError(f"משטח {pallet_id} לא נמצא")
    if pallet["TargetBin"] and pallet["TargetBin"] != target_bin:
        raise ValueError(
            f"משטח {pallet_id} כבר שויך לאיתור {pallet['TargetBin']}. לא ניתן לשייך פעמיים."
        )
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as c:
        c.execute(
            "UPDATE Pallets SET TargetBin=?, Status='ממוקם', AssignDate=? WHERE PalletID=?",
            (target_bin, now, pallet_id),
        )
        c.commit()
    log(user, "ASSIGN_PALLET_BIN", f"PalletID={pallet_id} TargetBin={target_bin}")


def update_pallet_status(pallet_id: int, status: str, user: str):
    with get_conn() as c:
        c.execute("UPDATE Pallets SET Status=? WHERE PalletID=?", (status, pallet_id))
        c.commit()
    log(user, "UPDATE_PALLET_STATUS", f"PalletID={pallet_id} Status={status}")


def import_pallets_from_rows(rows: list[dict], user: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as c:
        for r in rows:
            pid = r.get("PalletID")
            if pid is None:
                continue
            try:
                pid = int(float(str(pid)))
            except (ValueError, TypeError):
                continue
            # Upsert pallet
            c.execute(
                """INSERT OR IGNORE INTO Pallets (PalletID, CreateDate, CreateUser, Status)
                   VALUES (?, ?, ?, ?)""",
                (pid, r.get("CreateDate", now), r.get("CreateUser", user),
                 r.get("Status", "הוקם")),
            )
            # Insert item
            try:
                qty = float(str(r.get("Qty", 0) or 0))
            except (ValueError, TypeError):
                qty = 0.0
            c.execute(
                """INSERT INTO PalletItems (PalletID,Pn,Batch,WBS,Storage,Area,Bin,Qty,IsInStock)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (pid, r.get("PN", r.get("Pn", "")), r.get("Batch", ""),
                 r.get("WBS", ""), r.get("Storage", ""), r.get("Area", ""),
                 r.get("Bin", ""), qty, 1 if r.get("IsInStock") else 0),
            )
        c.commit()
    set_setting("last_pallet_import", now)
    log(user, "IMPORT_PALLETS", f"יובאו {len(rows)} שורות")


def get_all_pallets_export():
    with get_conn() as c:
        return c.execute(
            """SELECT p.*, pi.Pn, pi.Batch, pi.WBS, pi.Storage, pi.Area, pi.Bin, pi.Qty, pi.IsInStock
               FROM Pallets p
               LEFT JOIN PalletItems pi ON p.PalletID = pi.PalletID
               ORDER BY p.PalletID"""
        ).fetchall()
