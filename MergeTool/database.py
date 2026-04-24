import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merge_tool.db")
APP_NAME = "MergeTool"


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
            -- Loaded from OldWarehouseApp export
            CREATE TABLE IF NOT EXISTS StagingInventory (
                RowID       INTEGER PRIMARY KEY AUTOINCREMENT,
                Cat         TEXT,
                Pn          TEXT,
                Batch       TEXT,
                WBS         TEXT,
                Storage     TEXT,
                Area        TEXT,
                Bin         TEXT,
                DestArea    TEXT,
                Qty         REAL,
                PalletID    INTEGER,
                IsInStock   INTEGER,
                AssignDate  TEXT,
                TargetBin   TEXT
            );
            -- Loaded from NewWarehouseApp export
            CREATE TABLE IF NOT EXISTS StagingNewWarehouse (
                RowID      INTEGER PRIMARY KEY AUTOINCREMENT,
                PalletID   INTEGER,
                Status     TEXT,
                TargetBin  TEXT,
                AssignDate TEXT
            );
            -- Previous unified (for delta logic)
            CREATE TABLE IF NOT EXISTS UnifiedPrev (
                RowID    INTEGER PRIMARY KEY AUTOINCREMENT,
                Pn       TEXT,
                Batch    TEXT,
                WBS      TEXT,
                Storage  TEXT,
                Area     TEXT,
                Bin      TEXT,
                PalletID INTEGER,
                TargetBin TEXT,
                Status   TEXT
            );
            -- Current unified output
            CREATE TABLE IF NOT EXISTS UnifiedInventory (
                RowID      INTEGER PRIMARY KEY AUTOINCREMENT,
                Cat        TEXT,
                Pn         TEXT,
                Batch      TEXT,
                WBS        TEXT,
                Storage    TEXT,
                Area       TEXT,
                Bin        TEXT,
                DestArea   TEXT,
                Qty        REAL,
                PalletID   INTEGER,
                IsInStock  INTEGER,
                TargetBin  TEXT,
                Status     TEXT,
                AssignDate TEXT,
                MergeDate  TEXT
            );
        """)
        _seed_settings(c)
        c.commit()


def _seed_settings(c):
    defaults = [
        ("theme", "light"),
        ("export_path", os.path.expanduser("~/Desktop")),
        ("archive_path", os.path.join(os.path.dirname(DB_PATH), "archive")),
        ("last_merge_date", ""),
    ]
    for k, v in defaults:
        c.execute("INSERT OR IGNORE INTO Settings VALUES (?,?)", (k, v))


def get_setting(key: str, default: str = "") -> str:
    with get_conn() as c:
        row = c.execute("SELECT SettingValue FROM Settings WHERE SettingKey=?", (key,)).fetchone()
    return row[0] if row else default


def set_setting(key: str, value: str):
    with get_conn() as c:
        c.execute("INSERT OR REPLACE INTO Settings VALUES (?,?)", (key, value))
        c.commit()


def log(user: str, action: str, details: str = ""):
    with get_conn() as c:
        c.execute(
            "INSERT INTO LogEntries (Timestamp,UserName,ApplicationName,ActionType,Details) VALUES (?,?,?,?,?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user, APP_NAME, action, details),
        )
        c.commit()


def get_logs(from_date="", to_date="", action="", search=""):
    sql = "SELECT * FROM LogEntries WHERE 1=1"
    params = []
    if from_date:
        sql += " AND Timestamp >= ?"; params.append(from_date + " 00:00:00")
    if to_date:
        sql += " AND Timestamp <= ?"; params.append(to_date + " 23:59:59")
    if action:
        sql += " AND ActionType = ?"; params.append(action)
    if search:
        sql += " AND Details LIKE ?"; params.append(f"%{search}%")
    sql += " ORDER BY LogID DESC LIMIT 1000"
    with get_conn() as c:
        return c.execute(sql, params).fetchall()


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


# ── Staging operations ────────────────────────────────────────────────────────

def clear_staging_old():
    with get_conn() as c:
        c.execute("DELETE FROM StagingInventory")
        c.commit()


def clear_staging_new():
    with get_conn() as c:
        c.execute("DELETE FROM StagingNewWarehouse")
        c.commit()


def bulk_insert_staging_old(rows: list[dict]):
    with get_conn() as c:
        for r in rows:
            c.execute(
                """INSERT INTO StagingInventory
                   (Cat,Pn,Batch,WBS,Storage,Area,Bin,DestArea,Qty,PalletID,IsInStock,AssignDate,TargetBin)
                   VALUES (:Cat,:Pn,:Batch,:WBS,:Storage,:Area,:Bin,:DestArea,:Qty,:PalletID,:IsInStock,:AssignDate,:TargetBin)""",
                r,
            )
        c.commit()


def bulk_insert_staging_new(rows: list[dict]):
    with get_conn() as c:
        for r in rows:
            c.execute(
                "INSERT INTO StagingNewWarehouse (PalletID,Status,TargetBin,AssignDate) VALUES (?,?,?,?)",
                (r.get("PalletID"), r.get("Status"), r.get("TargetBin"), r.get("AssignDate")),
            )
        c.commit()


def archive_unified_to_prev():
    """Copy current UnifiedInventory → UnifiedPrev for delta logic."""
    with get_conn() as c:
        c.execute("DELETE FROM UnifiedPrev")
        c.execute(
            """INSERT INTO UnifiedPrev (Pn,Batch,WBS,Storage,Area,Bin,PalletID,TargetBin,Status)
               SELECT Pn,Batch,WBS,Storage,Area,Bin,PalletID,TargetBin,Status FROM UnifiedInventory"""
        )
        c.commit()


def run_merge(user: str) -> int:
    """Main merge logic. Returns count of rows in UnifiedInventory."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as c:
        # Build lookup: PalletID → (Status, TargetBin, AssignDate) from new warehouse
        new_ws = {}
        for row in c.execute("SELECT * FROM StagingNewWarehouse"):
            pid = row["PalletID"]
            if pid:
                new_ws[int(pid)] = {
                    "Status": row["Status"] or "הוקם",
                    "TargetBin": row["TargetBin"] or "",
                    "AssignDate": row["AssignDate"] or "",
                }

        # Build previous unified lookup: key → (PalletID, TargetBin, Status)
        prev_lookup = {}
        for row in c.execute("SELECT * FROM UnifiedPrev"):
            key = (row["Pn"], row["Batch"], row["WBS"], row["Storage"], row["Area"], row["Bin"])
            prev_lookup[key] = {
                "PalletID": row["PalletID"],
                "TargetBin": row["TargetBin"],
                "Status": row["Status"],
            }

        # Clear current unified
        c.execute("DELETE FROM UnifiedInventory")

        staging_rows = c.execute("SELECT * FROM StagingInventory").fetchall()
        count = 0
        for row in staging_rows:
            key = (row["Pn"], row["Batch"], row["WBS"], row["Storage"], row["Area"], row["Bin"])
            pallet_id   = row["PalletID"]
            target_bin  = row["TargetBin"] or ""
            status      = "הוקם"
            assign_date = row["AssignDate"] or ""

            if pallet_id:
                pallet_id = int(float(str(pallet_id)))
                # Get status from new warehouse
                if pallet_id in new_ws:
                    nw = new_ws[pallet_id]
                    target_bin  = nw["TargetBin"] or target_bin
                    status      = nw["Status"]
                    assign_date = nw["AssignDate"] or assign_date
                # Delta: if key existed before and same location → carry forward
                elif key in prev_lookup:
                    prev = prev_lookup[key]
                    if prev["PalletID"] == pallet_id:
                        target_bin  = prev["TargetBin"] or target_bin
                        status      = prev["Status"] or status

            c.execute(
                """INSERT INTO UnifiedInventory
                   (Cat,Pn,Batch,WBS,Storage,Area,Bin,DestArea,Qty,
                    PalletID,IsInStock,TargetBin,Status,AssignDate,MergeDate)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    row["Cat"], row["Pn"], row["Batch"], row["WBS"],
                    row["Storage"], row["Area"], row["Bin"], row["DestArea"], row["Qty"],
                    pallet_id if pallet_id else None,
                    row["IsInStock"], target_bin, status, assign_date, now,
                ),
            )
            count += 1

        c.commit()

    set_setting("last_merge_date", now)
    log(user, "MERGE", f"מוזגו {count} שורות")
    return count


def get_unified_inventory(pn="", status="", pallet_id=""):
    sql = "SELECT * FROM UnifiedInventory WHERE 1=1"
    params = []
    if pn:
        sql += " AND Pn LIKE ?"; params.append(f"%{pn}%")
    if status:
        sql += " AND Status=?"; params.append(status)
    if pallet_id:
        try:
            sql += " AND PalletID=?"; params.append(int(pallet_id))
        except ValueError:
            pass
    sql += " ORDER BY Pn, Batch LIMIT 5000"
    with get_conn() as c:
        return c.execute(sql, params).fetchall()
