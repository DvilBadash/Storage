import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime

HEADER_FILL  = PatternFill("solid", fgColor="1976D2")
HEADER_FONT  = Font(bold=True, color="FFFFFF", size=11)
ALT_FILL     = PatternFill("solid", fgColor="F5F9FF")
THIN_BORDER  = Border(
    left=Side(style="thin", color="E0E0E0"),
    right=Side(style="thin", color="E0E0E0"),
    top=Side(style="thin", color="E0E0E0"),
    bottom=Side(style="thin", color="E0E0E0"),
)


def _style_header(ws, headers):
    for col_idx, hdr in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=hdr)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = THIN_BORDER
    ws.row_dimensions[1].height = 28


def _auto_width(ws):
    for col in ws.columns:
        max_len = 0
        letter = col[0].column_letter
        for cell in col:
            try:
                max_len = max(max_len, len(str(cell.value or "")))
            except Exception:
                pass
        ws.column_dimensions[letter].width = min(max_len + 4, 40)


def load_pallet_xlsx(path: str) -> list[dict]:
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
        d = {header[i]: (str(row[i]).strip() if row[i] is not None else "") for i in range(len(header))}
        result.append(d)
    wb.close()
    return result


def load_locations_xlsx(path: str) -> list[dict]:
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
        for key in ["DestArea", "Dest_BIN"]:
            idx = next((i for i, h in enumerate(header) if h.lower() == key.lower()), None)
            d[key] = str(row[idx]).strip() if idx is not None and row[idx] is not None else ""
        if d.get("DestArea") and d.get("Dest_BIN"):
            result.append(d)
    wb.close()
    return result


def export_pallets_xlsx(rows, path: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "PalletAssignments"
    headers = ["PalletID", "Status", "TargetBin", "AssignDate",
               "PN", "Batch", "WBS", "Storage", "Area", "Bin", "Qty"]
    _style_header(ws, headers)
    for r_idx, row in enumerate(rows, 2):
        fill = ALT_FILL if r_idx % 2 == 0 else None
        for c_idx, col in enumerate(headers, 1):
            val = row[col] if col in row.keys() else ""
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
