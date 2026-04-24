import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime


INVENTORY_COLUMNS = ["Cat", "Pn", "Batch", "WBS", "Storage", "Area", "Bin", "DestArea", "Qty"]

HEADER_FILL   = PatternFill("solid", fgColor="1976D2")
HEADER_FONT   = Font(bold=True, color="FFFFFF", size=11)
HEADER_ALIGN  = Alignment(horizontal="center", vertical="center")
ALT_FILL      = PatternFill("solid", fgColor="F5F9FF")
THIN_BORDER   = Border(
    left=Side(style="thin", color="E0E0E0"),
    right=Side(style="thin", color="E0E0E0"),
    top=Side(style="thin", color="E0E0E0"),
    bottom=Side(style="thin", color="E0E0E0"),
)


def _style_header(ws, headers: list):
    for col_idx, hdr in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=hdr)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = HEADER_ALIGN
        cell.border = THIN_BORDER
    ws.row_dimensions[1].height = 28


def _auto_width(ws):
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                max_len = max(max_len, len(str(cell.value or "")))
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max_len + 4, 40)


def load_inventory_xlsx(path: str) -> list[dict]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    header = [str(h).strip() if h else "" for h in rows[0]]
    result = []
    for row in rows[1:]:
        if all(v is None for v in row):
            continue
        d = {}
        for col in INVENTORY_COLUMNS:
            idx = next((i for i, h in enumerate(header) if h.lower() == col.lower()), None)
            d[col] = str(row[idx]).strip() if idx is not None and row[idx] is not None else ""
        try:
            d["Qty"] = float(d["Qty"]) if d["Qty"] else 0.0
        except ValueError:
            d["Qty"] = 0.0
        result.append(d)
    wb.close()
    return result


def export_inventory_xlsx(rows, path: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "InventoryOld"
    all_cols = INVENTORY_COLUMNS + ["PalletID", "IsInStock", "AssignDate", "TargetBin"]
    _style_header(ws, all_cols)
    for r_idx, row in enumerate(rows, 2):
        fill = ALT_FILL if r_idx % 2 == 0 else None
        for c_idx, col in enumerate(all_cols, 1):
            val = row[col] if col in row.keys() else ""
            if col == "IsInStock":
                val = "כן" if val else "לא"
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.border = THIN_BORDER
            if fill:
                cell.fill = fill
    _auto_width(ws)
    wb.save(path)


def export_pallet_xlsx(pallet_rows: list, path: str):
    """Export pallet list (for NewWarehouseApp import)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pallets"
    headers = ["PalletID", "CreateDate", "CreateUser", "Status",
               "PN", "Batch", "WBS", "Storage", "Area", "Bin", "Qty", "IsInStock"]
    _style_header(ws, headers)
    for r_idx, row in enumerate(pallet_rows, 2):
        fill = ALT_FILL if r_idx % 2 == 0 else None
        vals = [row[h] if h in row.keys() else "" for h in headers]
        for c_idx, val in enumerate(vals, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.border = THIN_BORDER
            if fill:
                cell.fill = fill
    _auto_width(ws)
    wb.save(path)


def load_pallet_import_xlsx(path: str) -> list[dict]:
    """Read a pallet-import Excel. Skips rows where PalletID is not numeric (e.g. instruction rows)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    header = [str(h).strip() if h else "" for h in rows[0]]
    result = []
    for row in rows[1:]:
        if all(v is None for v in row):
            continue
        d = {header[i]: (str(row[i]).strip() if row[i] is not None else "")
             for i in range(len(header)) if i < len(header)}
        try:
            int(float(d.get("PalletID", "")))
        except (ValueError, TypeError):
            continue   # instruction row or empty
        result.append(d)
    wb.close()
    return result


def create_pallet_import_sample(path: str):
    """Create a sample Excel showing the expected pallet-import format."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "PalletImport"

    headers = ["PalletID", "PN", "Batch", "WBS",
               "Storage", "Area", "Bin",
               "CreateDate", "CreateUser", "Status"]
    _style_header(ws, headers)

    instr_fill = PatternFill("solid", fgColor="FFF9C4")
    instr_font = Font(italic=True, size=9, color="5D4037")
    instructions = [
        "מספר שלם (חובה)",
        "PN מהמלאי (חובה)",
        "אצווה",
        "WBS",
        "קוד אחסון",
        "אזור",
        "Bin",
        "YYYY-MM-DD HH:MM:SS",
        "שם יוצר",
        "הוקם / ממוקם / יצא",
    ]
    for c_idx, txt in enumerate(instructions, 1):
        cell = ws.cell(row=2, column=c_idx, value=txt)
        cell.fill = instr_fill
        cell.font = instr_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = THIN_BORDER
    ws.row_dimensions[2].height = 38

    samples = [
        [1001, "PN-123456", "LOT-001", "WBS-A1", "STOR-1", "A", "BIN-01",
         "2024-01-15 08:00:00", "admin", "הוקם"],
        [1001, "PN-789012", "LOT-002", "WBS-A2", "STOR-1", "B", "BIN-02",
         "2024-01-15 08:00:00", "admin", "הוקם"],
        [1002, "PN-345678", "LOT-003", "WBS-B1", "STOR-2", "A", "BIN-03",
         "", "", "הוקם"],
    ]
    for r_idx, row_data in enumerate(samples, 3):
        fill = ALT_FILL if r_idx % 2 == 0 else None
        for c_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.border = THIN_BORDER
            if fill:
                cell.fill = fill

    _auto_width(ws)
    wb.save(path)


def archive_path(archive_dir: str, prefix: str) -> str:
    os.makedirs(archive_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(archive_dir, f"{prefix}_{ts}.xlsx")
