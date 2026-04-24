from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QFrame, QGroupBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import database as db


class PalletItemsDialog(QDialog):
    def __init__(self, pallet_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"פריטי משטח P-{pallet_id}")
        self.setMinimumSize(600, 400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        lay = QVBoxLayout(self)
        p = db.get_pallet(pallet_id)
        if p:
            info = QLabel(
                f"משטח P-{pallet_id}  |  סטטוס: {p['Status']}  |  "
                f"תאריך הקמה: {p['CreateDate'] or '–'}  |  איתור: {p['TargetBin'] or '–'}"
            )
            info.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            lay.addWidget(info)
        tbl = QTableWidget()
        tbl.setColumnCount(7)
        tbl.setHorizontalHeaderLabels(["PN", "אצווה", "WBS", "אחסון", "אזור", "Bin", "כמות"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        items = db.get_pallet_items(pallet_id)
        tbl.setRowCount(len(items))
        for r, item in enumerate(items):
            for c, key in enumerate(["Pn", "Batch", "WBS", "Storage", "Area", "Bin", "Qty"]):
                val = item[key] if key in item.keys() else ""
                cell = QTableWidgetItem(str(val or ""))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tbl.setItem(r, c, cell)
            tbl.setRowHeight(r, 44)
        lay.addWidget(tbl)
        btn = QPushButton("סגור")
        btn.clicked.connect(self.accept)
        lay.addWidget(btn)


class PalletManagementScreen(QWidget):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self._build_ui()
        self._load_table()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("ניהול משטחים")
        title.setObjectName("section_title")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        root.addWidget(title)

        filter_lay = QHBoxLayout()
        lbl = QLabel("סינון לפי סטטוס:")
        self.cmb_status = QComboBox()
        self.cmb_status.addItem("הכל", "")
        self.cmb_status.addItem("הוקם", "הוקם")
        self.cmb_status.addItem("ממוקם", "ממוקם")
        self.cmb_status.addItem("יצא", "יצא")
        self.cmb_status.currentIndexChanged.connect(self._load_table)
        self.chk_unassigned = QCheckBox("ללא שיוך לאיתור")
        self.chk_unassigned.toggled.connect(self._load_table)
        btn_refresh = QPushButton("רענן")
        btn_refresh.setObjectName("btn_secondary")
        btn_refresh.clicked.connect(self._load_table)
        filter_lay.addWidget(btn_refresh)
        filter_lay.addWidget(self.chk_unassigned)
        filter_lay.addWidget(self.cmb_status)
        filter_lay.addWidget(lbl)
        filter_lay.addStretch()
        root.addLayout(filter_lay)

        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels(db.get_pal_headers())
        hh = self.tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.verticalHeader().setVisible(False)
        self._apply_pal_col_visibility()
        root.addWidget(self.tbl)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("font-size: 12px; color: #757575;")
        root.addWidget(self.lbl_count)

    def _load_table(self):
        status_filter = self.cmb_status.currentData()
        pallets = db.get_pallets(status_filter, self.chk_unassigned.isChecked())
        self.tbl.setRowCount(0)

        STATUS_COLORS = {"ממוקם": "#1B5E20", "הוקם": "#E65100", "יצא": "#1565C0"}

        for r, p in enumerate(pallets):
            self.tbl.insertRow(r)
            pid = p["PalletID"]

            def mk(text, color=None):
                item = QTableWidgetItem(str(text or ""))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if color:
                    item.setForeground(QColor(color))
                return item

            self.tbl.setItem(r, 0, mk(f"P-{pid}"))
            status = p["Status"] or "הוקם"
            self.tbl.setItem(r, 1, mk(status, STATUS_COLORS.get(status)))
            self.tbl.setItem(r, 2, mk(p["TargetBin"] or "–"))
            self.tbl.setItem(r, 3, mk(p["AssignDate"] or "–"))

            btn_items = QPushButton("📋 פרטים")
            btn_items.setObjectName("btn_secondary")
            btn_items.clicked.connect(lambda _, pid=pid: PalletItemsDialog(pid, self).exec())
            self.tbl.setCellWidget(r, 4, btn_items)

            cmb_status = QComboBox()
            cmb_status.addItems(["הוקם", "ממוקם", "יצא"])
            idx = cmb_status.findText(status)
            if idx >= 0:
                cmb_status.setCurrentIndex(idx)
            cmb_status.currentTextChanged.connect(
                lambda s, pid=pid: db.update_pallet_status(pid, s, self.username)
            )
            self.tbl.setCellWidget(r, 5, cmb_status)
            self.tbl.setRowHeight(r, 52)

        self.lbl_count.setText(f"סה\"כ משטחים: {len(pallets)}")

    def _apply_pal_col_visibility(self):
        for i in range(6):
            self.tbl.setColumnHidden(i, db.get_col_hidden(f"pal_col_{i}"))

    def refresh(self):
        self._apply_pal_col_visibility()
        self._load_table()
