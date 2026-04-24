from collections import Counter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QCheckBox, QFrame, QMessageBox, QDialog, QSpinBox,
    QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QFont, QColor, QBrush, QPainter, QPainterPath
import database as db

MAX_ROWS = 500

# ── Column indices ────────────────────────────────────────────────────────────
COL_CB    = 0   # בחירה
COL_PN    = 1   # מק"ט
COL_CAT   = 2   # חומר
COL_UOM   = 3   # יחידת מידה
COL_BATCH = 4   # סדרה
COL_WBS   = 5   # WBS
COL_STO   = 6   # אתר אחסון
COL_AREA  = 7   # סוג איחסון
COL_BIN   = 8   # איתור איחסון
COL_DEST  = 9   # אסטרטגיה ייעודית
COL_QTY   = 10  # מלאי זמין
COL_MULTI = 11  # האם > איתור אחד
COL_STOCK = 12  # קיים פיזית – native toggle
COL_DUP   = 13  # ⚠ duplicate PN+Storage
COL_PAL   = 14  # ⚑ assigned pallet
NUM_COLS  = 15

COLOR_DUP   = QColor("#E65100")
COLOR_PAL   = QColor("#1565C0")
BG_ASSIGNED = QColor("#E8F5E9")


# ── Pallet detail popup ───────────────────────────────────────────────────────

class PalletDetailPopup(QDialog):
    def __init__(self, pallet_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"משטח P-{pallet_id}")
        self.setMinimumSize(580, 440)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        hdr = QLabel(f"🗂  משטח מספר: P-{pallet_id}")
        hdr.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        lay.addWidget(hdr)

        tbl = QTableWidget()
        tbl.setColumnCount(5)
        tbl.setHorizontalHeaderLabels(["PN", "אצווה", "WBS", "איתור", "קיים פיזית"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)

        rows = db.get_pallet_items(pallet_id)
        tbl.setRowCount(len(rows))
        for r, row in enumerate(rows):
            tbl.setItem(r, 0, QTableWidgetItem(row["Pn"] or ""))
            tbl.setItem(r, 1, QTableWidgetItem(row["Batch"] or ""))
            tbl.setItem(r, 2, QTableWidgetItem(row["WBS"] or ""))
            tbl.setItem(r, 3, QTableWidgetItem(
                f"{row['Storage']}/{row['Area']}/{row['Bin']}"))
            val = "✔ כן" if row["IsInStock"] else "✗ לא"
            item = QTableWidgetItem(val)
            item.setForeground(QColor("#1B5E20") if row["IsInStock"] else QColor("#B71C1C"))
            tbl.setItem(r, 4, item)
            tbl.setRowHeight(r, 44)
        lay.addWidget(tbl)

        btn = QPushButton("סגור")
        btn.clicked.connect(self.accept)
        lay.addWidget(btn)


# ── New pallet dialog ─────────────────────────────────────────────────────────

class NewPalletDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("יצירת משטח חדש")
        self.setFixedSize(360, 230)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.pallet_id = None
        lay = QVBoxLayout(self)
        lay.setSpacing(16)
        lay.addWidget(QLabel("הזן מספר משטח (1 – 99999):"))
        self.spin = QSpinBox()
        self.spin.setRange(1, 99999)
        self.spin.setMinimumHeight(48)
        lay.addWidget(self.spin)
        row = QHBoxLayout()
        ok = QPushButton("צור משטח")
        ok.clicked.connect(self._on_ok)
        cancel = QPushButton("ביטול")
        cancel.setObjectName("btn_secondary")
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        row.addWidget(ok)
        lay.addLayout(row)

    def _on_ok(self):
        self.pallet_id = self.spin.value()
        self.accept()


# ── Toggle switch widget ──────────────────────────────────────────────────────

class ToggleSwitch(QWidget):
    """Green/red sliding toggle – emits toggled(bool) on click."""
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = True, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(90, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, value: bool):
        if self._checked != value:
            self._checked = value
            self.update()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        radius = h / 2

        bg = QColor("#2E7D32") if self._checked else QColor("#C62828")
        p.setBrush(QBrush(bg))
        p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, radius, radius)
        p.drawPath(path)

        knob_d = h - 4
        knob_x = w - knob_d - 2 if self._checked else 2
        p.setBrush(QBrush(QColor("white")))
        p.drawEllipse(int(knob_x), 2, knob_d, knob_d)

        p.setPen(QColor("white"))
        font = p.font()
        font.setPointSize(8)
        font.setBold(True)
        p.setFont(font)
        text = "קיים" if self._checked else "לא קיים"
        if self._checked:
            text_rect = QRect(2, 0, w - knob_d - 6, h)
        else:
            text_rect = QRect(knob_d + 6, 0, w - knob_d - 6, h)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
        p.end()


# ── Inventory Screen ──────────────────────────────────────────────────────────

class InventoryScreen(QWidget):
    def __init__(self, username: str):
        super().__init__()
        self.username    = username
        self._rows: list = []
        self._cb_list: list[QCheckBox | None] = []
        self._populating = False          # guard for itemChanged during populate
        self._build_ui()
        self.table.itemClicked.connect(self._on_item_clicked)
        self._refresh_filter_combos()
        self._search()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("שלב 1: בחירת איתור ושיוך מלאי למשטח")
        title.setObjectName("section_title")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        root.addWidget(title)

        # Search bar
        sf = QFrame(); sf.setObjectName("card")
        s = QHBoxLayout(sf); s.setContentsMargins(16, 12, 16, 12); s.setSpacing(10)
        self.txt_pn = QLineEdit()
        self.txt_pn.setPlaceholderText("PN – חיפוש חופשי")
        self.txt_pn.setMinimumWidth(180)
        self.txt_pn.returnPressed.connect(self._search)
        self.cmb_storage = QComboBox(); self.cmb_storage.addItem("-- אחסון --")
        self.cmb_area    = QComboBox(); self.cmb_area.addItem("-- אזור --")
        self.cmb_bin     = QComboBox(); self.cmb_bin.addItem("-- Bin --")
        self.chk_unassigned = QCheckBox("ללא משטח")
        self.chk_unassigned.toggled.connect(self._search)
        btn_search = QPushButton("חפש 🔍"); btn_search.clicked.connect(self._search)
        btn_clear  = QPushButton("נקה");    btn_clear.setObjectName("btn_secondary")
        btn_clear.clicked.connect(self._clear_filter)
        for w in [btn_clear, btn_search, self.chk_unassigned, self.cmb_bin,
                  self.cmb_area, self.cmb_storage, self.txt_pn]:
            s.addWidget(w)
        root.addWidget(sf)

        # Table
        self.table = QTableWidget(0, NUM_COLS)
        self._apply_headers()
        self.table.setAlternatingRowColors(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setStretchLastSection(False)
        # Fixed width for checkbox column so it's always fully visible
        hh.setSectionResizeMode(COL_CB, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(COL_CB, 52)
        # Stretch PN; everything else ResizeToContents
        for i in range(1, NUM_COLS):
            hh.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(COL_PN,  QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(COL_CAT, QHeaderView.ResizeMode.Stretch)
        root.addWidget(self.table, 1)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("font-size: 12px; color: #757575;")
        root.addWidget(self.lbl_count)

        # Pallet action bar
        pf = QFrame(); pf.setObjectName("card")
        p = QHBoxLayout(pf); p.setContentsMargins(16, 12, 16, 12); p.setSpacing(10)
        self.cmb_pallet = QComboBox(); self.cmb_pallet.setMinimumWidth(170)
        self._reload_pallets()
        btn_new = QPushButton("+ משטח חדש"); btn_new.setObjectName("btn_secondary")
        btn_new.clicked.connect(self._create_pallet)
        btn_assign = QPushButton("שייך מסומנים ✓")
        btn_assign.clicked.connect(self._assign_selected)
        for w in [btn_assign, self.cmb_pallet, QLabel("שיוך למשטח:")]:
            if isinstance(w, QLabel):
                w.setObjectName("section_title")
            p.addWidget(w)
        p.addStretch()
        p.addWidget(btn_new)
        root.addWidget(pf)

        # Legend
        legend = QLabel(
            "מקרא:  מתג ירוק/אדום = קיים / לא קיים פיזית  │  "
            "⚠ = פריט זהה (PN+אחסון) בשורה אחרת, לחץ לפרטי משטח  │  "
            "⚑ = שויך למשטח, לחץ לפרטים"
        )
        legend.setObjectName("warn_label")
        legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(legend)

    # ── Headers ───────────────────────────────────────────────────────────────

    def _apply_headers(self):
        self.table.setHorizontalHeaderLabels(db.get_column_headers())
        for i in range(1, NUM_COLS):
            self.table.setColumnHidden(i, db.get_col_hidden(i))
        # COL_DUP and COL_PAL are always visible (functional indicators)
        self.table.setColumnHidden(COL_DUP, False)
        self.table.setColumnHidden(COL_PAL, False)

    # ── Data helpers ──────────────────────────────────────────────────────────

    def _refresh_filter_combos(self):
        for cmb, col in [(self.cmb_storage, "Storage"),
                         (self.cmb_area,    "Area"),
                         (self.cmb_bin,     "Bin")]:
            prev = cmb.currentText()
            cmb.blockSignals(True)
            cmb.clear()
            cmb.addItem(f"-- {col} --")
            for v in db.get_distinct_values(col):
                cmb.addItem(v)
            idx = cmb.findText(prev)
            if idx >= 0:
                cmb.setCurrentIndex(idx)
            cmb.blockSignals(False)

    def _reload_pallets(self):
        self.cmb_pallet.blockSignals(True)
        self.cmb_pallet.clear()
        self.cmb_pallet.addItem("-- בחר משטח --", None)
        for p in db.get_pallets():
            self.cmb_pallet.addItem(f"P-{p['PalletID']}", p["PalletID"])
        self.cmb_pallet.blockSignals(False)

    def _search(self):
        pn      = self.txt_pn.text().strip()
        storage = "" if self.cmb_storage.currentText().startswith("--") else self.cmb_storage.currentText()
        area    = "" if self.cmb_area.currentText().startswith("--")    else self.cmb_area.currentText()
        bin_    = "" if self.cmb_bin.currentText().startswith("--")     else self.cmb_bin.currentText()
        all_rows = db.get_inventory_with_assignments(
            pn, storage, area, bin_, MAX_ROWS,
            unassigned_only=self.chk_unassigned.isChecked(),
        )
        truncated = len(all_rows) > MAX_ROWS
        self._rows = list(all_rows[:MAX_ROWS])
        self._populate_table(truncated)

    def _clear_filter(self):
        self.txt_pn.clear()
        self.cmb_storage.setCurrentIndex(0)
        self.cmb_area.setCurrentIndex(0)
        self.cmb_bin.setCurrentIndex(0)
        self.chk_unassigned.setChecked(False)
        self._search()

    # ── Table population ──────────────────────────────────────────────────────

    def _populate_table(self, truncated: bool = False):
        rows = self._rows
        n    = len(rows)

        # Duplicate indicator: same (Pn, Storage) appears > once in current results
        dup_keys: set = {
            k for k, cnt in
            Counter((r["Pn"], r["Storage"]) for r in rows).items()
            if cnt > 1
        }

        msg = f"נמצאו: {n} פריטים"
        if truncated:
            msg += f"  ← מוצגים {MAX_ROWS} הראשונים בלבד, צמצם את החיפוש"
        self.lbl_count.setText(msg)

        # Block signals during population to prevent itemChanged firing DB writes
        self._populating = True
        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.table.setRowCount(n)
        self._cb_list = [None] * n

        for r, row in enumerate(rows):
            inv_id    = row["InventoryID"]
            pallet_id = row["PalletID"]
            is_stock  = bool(row["IsInStock"])
            is_dup    = (row["Pn"], row["Storage"]) in dup_keys
            row_bg    = BG_ASSIGNED if pallet_id else None

            def mk(text, fg=None, bold=False, selectable=False):
                item = QTableWidgetItem(str(text) if text is not None else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                flags = Qt.ItemFlag.ItemIsEnabled
                if selectable:
                    flags |= Qt.ItemFlag.ItemIsSelectable
                item.setFlags(flags)
                if fg:
                    item.setForeground(QBrush(fg))
                if row_bg:
                    item.setBackground(QBrush(row_bg))
                if bold:
                    f = item.font(); f.setBold(True); item.setFont(f)
                return item

            # ── COL_CB: selection checkbox widget ─────────────────────────────
            cb = QCheckBox()
            if not is_stock:
                cb.setEnabled(False)
            cw = QWidget()
            cl = QHBoxLayout(cw)
            cl.addWidget(cb)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.setContentsMargins(4, 0, 4, 0)
            self.table.setCellWidget(r, COL_CB, cw)
            self._cb_list[r] = cb

            # ── Data cells ────────────────────────────────────────────────────
            self.table.setItem(r, COL_PN,    mk(row["Pn"],           bold=True))
            self.table.setItem(r, COL_CAT,   mk(row["Cat"]))
            self.table.setItem(r, COL_UOM,   mk(row["UnitOfMeasure"]))
            self.table.setItem(r, COL_BATCH, mk(row["Batch"]))
            self.table.setItem(r, COL_WBS,   mk(row["WBS"]))
            self.table.setItem(r, COL_STO,   mk(row["Storage"]))
            self.table.setItem(r, COL_AREA,  mk(row["Area"]))
            self.table.setItem(r, COL_BIN,   mk(row["Bin"]))
            self.table.setItem(r, COL_DEST,  mk(row["DestArea"]))
            self.table.setItem(r, COL_QTY,   mk(row["Qty"]))
            self.table.setItem(r, COL_MULTI, mk(row["MultiLocation"]))

            # ── COL_STOCK: green/red toggle switch ───────────────────────────
            toggle = ToggleSwitch(is_stock)
            toggle.toggled.connect(
                lambda val, iid=inv_id: db.set_is_in_stock(iid, val, self.username)
            )
            toggle.toggled.connect(
                lambda val, row_idx=r: self._sync_cb_to_stock(row_idx, val)
            )
            self.table.setCellWidget(r, COL_STOCK, toggle)

            # ── COL_DUP: ⚠ when same PN+Storage elsewhere ────────────────────
            if is_dup:
                dup_item = mk("⚠", fg=COLOR_DUP, selectable=True)
                dup_item.setToolTip(
                    f"קיימות שורות נוספות עם PN '{row['Pn']}' "
                    f"באחסון '{row['Storage']}'"
                )
            else:
                dup_item = mk("")
            self.table.setItem(r, COL_DUP, dup_item)

            # ── COL_PAL: ⚑ P-XXXX when assigned, clickable ───────────────────
            if pallet_id:
                pal_item = mk(f"⚑  P-{pallet_id}", fg=COLOR_PAL, bold=True, selectable=True)
                pal_item.setToolTip(f"לחץ לפרטי משטח P-{pallet_id}")
            else:
                pal_item = mk("")
            self.table.setItem(r, COL_PAL, pal_item)

            self.table.setRowHeight(r, 46)

        self.table.blockSignals(False)
        self.table.setUpdatesEnabled(True)
        self._populating = False

    # ── Signal handlers ───────────────────────────────────────────────────────

    def _sync_cb_to_stock(self, row_idx: int, in_stock: bool):
        cb = self._cb_list[row_idx] if row_idx < len(self._cb_list) else None
        if cb is None:
            return
        if not in_stock:
            cb.setChecked(False)
        cb.setEnabled(in_stock)

    def _on_item_clicked(self, item: QTableWidgetItem):
        """Fires when user clicks COL_PAL or COL_DUP indicator."""
        if item.column() not in (COL_PAL, COL_DUP):
            return
        r = item.row()
        if r >= len(self._rows):
            return

        row_data = self._rows[r]
        pid = row_data["PalletID"]

        if item.column() == COL_DUP:
            pn      = row_data["Pn"]
            storage = row_data["Storage"]
            msg = f"קיימות שורות נוספות בטבלה עם:\nPN: {pn}   אחסון: {storage}"
            if pid:
                msg += f"\n\nפריט זה שויך למשטח P-{pid}"
            QMessageBox.information(self, "פריט כפול", msg)
            return

        # COL_PAL — requires assignment
        if not pid:
            return
        inv_id = row_data["InventoryID"]
        dlg = QMessageBox(self)
        dlg.setWindowTitle("משטח מושייך")
        dlg.setText(f"פריט זה שויך למשטח  P-{pid}")
        dlg.setInformativeText("בחר פעולה:")
        btn_detach  = dlg.addButton("הפרד ממשטח",  QMessageBox.ButtonRole.DestructiveRole)
        btn_details = dlg.addButton("פרטי משטח",   QMessageBox.ButtonRole.ActionRole)
        dlg.addButton("סגור", QMessageBox.ButtonRole.RejectRole)
        dlg.exec()

        if dlg.clickedButton() == btn_detach:
            confirm = QMessageBox.question(
                self, "אישור הפרדה",
                f"להפריד פריט זה ממשטח P-{pid}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm == QMessageBox.StandardButton.Yes:
                db.detach_item_from_pallet(inv_id, self.username)
                self._search()
        elif dlg.clickedButton() == btn_details:
            PalletDetailPopup(int(pid), self).exec()

    # ── Pallet management ──────────────────────────────────────────────────────

    def _create_pallet(self):
        dlg = NewPalletDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            db.create_pallet(dlg.pallet_id, self.username)
            self._reload_pallets()
            idx = self.cmb_pallet.findData(dlg.pallet_id)
            if idx >= 0:
                self.cmb_pallet.setCurrentIndex(idx)
            QMessageBox.information(self, "הצלחה", f"משטח P-{dlg.pallet_id} נוצר ✓")
        except ValueError as e:
            QMessageBox.warning(self, "שגיאה", str(e))

    def _assign_selected(self):
        pallet_id = self.cmb_pallet.currentData()
        if pallet_id is None:
            QMessageBox.warning(self, "שגיאה", "יש לבחור משטח לפני השיוך")
            return
        selected = [
            self._rows[r]["InventoryID"]
            for r, cb in enumerate(self._cb_list)
            if cb is not None and cb.isChecked()
        ]
        if not selected:
            QMessageBox.warning(self, "שגיאה", "יש לסמן לפחות פריט אחד לשיוך")
            return
        reply = QMessageBox.question(
            self, "אישור שיוך",
            f"לשייך {len(selected)} פריטים למשטח P-{pallet_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        db.assign_items_to_pallet(selected, pallet_id, self.username)
        QMessageBox.information(self, "הצלחה", "השיוך בוצע בהצלחה ✓")
        self._search()

    def refresh(self):
        self._apply_headers()
        self._refresh_filter_combos()
        self._reload_pallets()
        self._search()
