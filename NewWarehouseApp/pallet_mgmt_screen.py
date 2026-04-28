from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCompleter, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QFrame, QGroupBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
import database as db

# Column indices
COL_PID    = 0   # מספר משטח
COL_BIN    = 1   # איתור יעד
COL_DATE   = 2   # תאריך שיוך
COL_ITEMS  = 3   # פריטים
COL_STATUS = 4   # סטטוס (combo)
NUM_COLS   = 5


class PalletItemsDialog(QDialog):
    def __init__(self, pallet_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"פריטי משטח {pallet_id}")
        self.setMinimumSize(640, 420)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        lay = QVBoxLayout(self)
        p = db.get_pallet(pallet_id)
        if p:
            info = QLabel(
                f"משטח {pallet_id}  |  סטטוס: {p['Status']}  |  "
                f"תאריך הקמה: {p['CreateDate'] or '–'}  |  איתור: {p['TargetBin'] or '–'}"
            )
            _f = QFont("Segoe UI"); _f.setPixelSize(17); _f.setBold(True); info.setFont(_f)
            lay.addWidget(info)
        tbl = QTableWidget()
        tbl.setColumnCount(7)
        tbl.setHorizontalHeaderLabels(['מק"ט', "סדרה", "WBS", "אחסון", "סוג", "Bin", "כמות"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        items = db.get_pallet_items(pallet_id)
        tbl.setRowCount(len(items))
        for r, item in enumerate(items):
            for c, key in enumerate(["Pn", "Batch", "WBS", "Storage", "StorageType", "Bin", "Qty"]):
                val = item[key] if key in item.keys() else ""
                cell = QTableWidgetItem(str(val or ""))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tbl.setItem(r, c, cell)
            tbl.setRowHeight(r, 40)
        lay.addWidget(tbl)
        btn = QPushButton("סגור")
        btn.clicked.connect(self.accept)
        lay.addWidget(btn)


class PalletManagementScreen(QWidget):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self._build_ui()
        QTimer.singleShot(0, self._load_table)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        title = QLabel("ניהול משטחים")
        title.setObjectName("section_title")
        root.addWidget(title)

        filter_lay = QHBoxLayout()
        filter_lay.setSpacing(10)
        lbl = QLabel("סינון:")
        _f = QFont("Segoe UI"); _f.setPixelSize(16); lbl.setFont(_f)
        self.cmb_status = QComboBox()
        self.cmb_status.setMinimumHeight(38)
        self.cmb_status.addItem("הכל", "")
        self.cmb_status.addItem("הוקם",  "הוקם")
        self.cmb_status.addItem("ממוקם", "ממוקם")
        self.cmb_status.addItem("יצא",   "יצא")
        self.cmb_status.setEditable(True)
        self.cmb_status.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        _cs = QCompleter(self.cmb_status.model(), self.cmb_status)
        _cs.setFilterMode(Qt.MatchFlag.MatchContains)
        _cs.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        _cs.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.cmb_status.setCompleter(_cs)
        self.cmb_status.currentIndexChanged.connect(self._load_table)
        self.chk_unassigned = QCheckBox("ללא שיוך")
        self.chk_unassigned.toggled.connect(self._load_table)
        btn_refresh = QPushButton("רענן")
        btn_refresh.setObjectName("btn_secondary")
        btn_refresh.setMinimumHeight(38)
        btn_refresh.clicked.connect(self._load_table)
        filter_lay.addWidget(btn_refresh)
        filter_lay.addWidget(self.chk_unassigned)
        filter_lay.addWidget(self.cmb_status)
        filter_lay.addWidget(lbl)
        filter_lay.addStretch()
        root.addLayout(filter_lay)

        self.tbl = QTableWidget(0, NUM_COLS)
        self.tbl.setHorizontalHeaderLabels(
            ["מספר משטח", "איתור יעד", "תאריך שיוך", "פריטים", "סטטוס"]
        )
        hh = self.tbl.horizontalHeader()
        hh.setSectionResizeMode(COL_PID,    QHeaderView.ResizeMode.Interactive); hh.resizeSection(COL_PID,   110)
        hh.setSectionResizeMode(COL_BIN,    QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(COL_DATE,   QHeaderView.ResizeMode.Interactive); hh.resizeSection(COL_DATE,  120)
        hh.setSectionResizeMode(COL_ITEMS,  QHeaderView.ResizeMode.Interactive); hh.resizeSection(COL_ITEMS, 90)
        hh.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeMode.Interactive); hh.resizeSection(COL_STATUS, 140)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.verticalHeader().setVisible(False)
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
            pid    = p["PalletID"]
            status = p["Status"] or "הוקם"

            def mk(text, color=None):
                item = QTableWidgetItem(str(text or ""))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if color:
                    item.setForeground(QColor(color))
                return item

            self.tbl.setItem(r, COL_PID,  mk(pid))
            self.tbl.setItem(r, COL_BIN,  mk(p["TargetBin"] or "–"))
            self.tbl.setItem(r, COL_DATE, mk(p["AssignDate"] or "–"))

            btn_items = QPushButton("פרטים")
            btn_items.setObjectName("btn_secondary")
            btn_items.setMinimumHeight(34)
            btn_items.clicked.connect(lambda _, pid=pid: PalletItemsDialog(pid, self).exec())
            self.tbl.setCellWidget(r, COL_ITEMS, btn_items)

            cmb_status = QComboBox()
            cmb_status.setMinimumHeight(34)
            cmb_status.addItems(["הוקם", "ממוקם", "יצא"])
            idx = cmb_status.findText(status)
            if idx >= 0:
                cmb_status.setCurrentIndex(idx)
            cmb_status.currentTextChanged.connect(
                lambda s, pid=pid: db.update_pallet_status(pid, s, self.username)
            )
            self.tbl.setCellWidget(r, COL_STATUS, cmb_status)
            self.tbl.setRowHeight(r, 44)

        self.lbl_count.setText(f'סה"כ משטחים: {len(pallets)}')

    def refresh(self):
        self._load_table()
