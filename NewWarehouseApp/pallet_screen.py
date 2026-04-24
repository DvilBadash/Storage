from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import database as db


class PalletAssignmentScreen(QWidget):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self._build_ui()
        self._reload_pallets()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Title
        title = QLabel("שלב 2: שיוך משטח לאיתור יעד")
        title.setObjectName("section_title")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        root.addWidget(title)

        # Top row: pallet selection
        top = QGroupBox("בחירת משטח")
        top_lay = QHBoxLayout(top)
        top_lay.setSpacing(12)

        lbl1 = QLabel("בחר מס' משטח:")
        lbl1.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))

        self.cmb_pallet = QComboBox()
        self.cmb_pallet.setMinimumWidth(220)
        self.cmb_pallet.setEditable(True)
        self.cmb_pallet.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cmb_pallet.currentIndexChanged.connect(self._on_pallet_changed)

        top_lay.addStretch()
        top_lay.addWidget(self.cmb_pallet)
        top_lay.addWidget(lbl1)
        root.addWidget(top)

        # Pallet detail card
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("card")
        det_lay = QVBoxLayout(self.detail_frame)
        det_lay.setContentsMargins(16, 14, 16, 14)
        det_lay.setSpacing(10)

        det_title = QLabel("פרטי משטח")
        det_title.setObjectName("section_title")
        det_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        det_lay.addWidget(det_title)

        info_lay = QHBoxLayout()
        info_lay.setSpacing(30)
        self.lbl_create  = QLabel("תאריך הקמה: –")
        self.lbl_status  = QLabel("סטטוס: –")
        self.lbl_target  = QLabel("איתור נוכחי: –")
        for lbl in [self.lbl_create, self.lbl_status, self.lbl_target]:
            lbl.setFont(QFont("Segoe UI", 12))
        info_lay.addStretch()
        info_lay.addWidget(self.lbl_target)
        info_lay.addWidget(self.lbl_status)
        info_lay.addWidget(self.lbl_create)
        det_lay.addLayout(info_lay)

        # Status legend
        self.lbl_status_legend = QLabel("")
        self.lbl_status_legend.setObjectName("warn_label")
        det_lay.addWidget(self.lbl_status_legend)

        # Status checkboxes (display only)
        ck_lay = QHBoxLayout()
        ck_lay.setSpacing(20)
        self.lbl_in_stock  = QLabel("☐ ממוקם (נמצא במחסן היעד)")
        self.lbl_set_up    = QLabel("☐ הוקם")
        self.lbl_departed  = QLabel("☐ יצא (באמצע שליחה)")
        for lbl in [self.lbl_in_stock, self.lbl_set_up, self.lbl_departed]:
            lbl.setFont(QFont("Segoe UI", 12))
        ck_lay.addStretch()
        ck_lay.addWidget(self.lbl_departed)
        ck_lay.addWidget(self.lbl_set_up)
        ck_lay.addWidget(self.lbl_in_stock)
        det_lay.addLayout(ck_lay)

        # Items table (11 columns matching STOCK.xlsx fields)
        self.tbl_items = QTableWidget(0, 11)
        self.tbl_items.setHorizontalHeaderLabels(db.get_item_headers())
        hh = self.tbl_items.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)   # מק"ט
        hh.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)   # Bin
        hh.setMaximumSectionSize(180)
        self.tbl_items.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_items.setAlternatingRowColors(True)
        self.tbl_items.setMaximumHeight(210)
        self._apply_item_col_visibility()
        det_lay.addWidget(self.tbl_items)

        root.addWidget(self.detail_frame)

        # Target bin assignment
        bin_grp = QGroupBox("שיוך לאיתור יעד")
        bin_lay = QHBoxLayout(bin_grp)
        bin_lay.setSpacing(12)

        lbl_area = QLabel("אזור יעד:")
        lbl_area.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.cmb_dest_area = QComboBox()
        self.cmb_dest_area.setMinimumWidth(160)
        self.cmb_dest_area.currentIndexChanged.connect(self._on_area_changed)

        lbl_bin = QLabel("איתור יעד:")
        lbl_bin.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.cmb_dest_bin = QComboBox()
        self.cmb_dest_bin.setMinimumWidth(160)

        btn_assign = QPushButton("בצע שיוך ועדכן סטטוס ✓")
        btn_assign.setMinimumHeight(52)
        btn_assign.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        btn_assign.clicked.connect(self._do_assign)

        bin_lay.addWidget(btn_assign)
        bin_lay.addWidget(self.cmb_dest_bin)
        bin_lay.addWidget(lbl_bin)
        bin_lay.addWidget(self.cmb_dest_area)
        bin_lay.addWidget(lbl_area)
        bin_lay.addStretch()
        root.addWidget(bin_grp)

        # Legend
        leg = QLabel(
            "** מקרא סטטוסים **\n"
            "ממוקם = המשטח נמצא במחסן היעד  |  הוקם = המשטח הוקם וממתין להעברה  |  יצא = המשטח יצא מהמחסן ונמצא בדרכו"
        )
        leg.setObjectName("status_label")
        leg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(leg)

        self._load_areas()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _reload_pallets(self):
        self.cmb_pallet.blockSignals(True)
        self.cmb_pallet.clear()
        self.cmb_pallet.addItem("-- בחר משטח --", None)
        for p in db.get_pallets():
            status_icon = {"ממוקם": "✔", "יצא": "→", "הוקם": "●"}.get(p["Status"], "")
            self.cmb_pallet.addItem(f"{status_icon} {p['PalletID']}  [{p['Status']}]", p["PalletID"])
        self.cmb_pallet.blockSignals(False)

    def _load_areas(self):
        self.cmb_dest_area.blockSignals(True)
        self.cmb_dest_area.clear()
        self.cmb_dest_area.addItem("-- אזור יעד --", None)
        for area in db.get_dest_areas():
            self.cmb_dest_area.addItem(area, area)
        self.cmb_dest_area.blockSignals(False)

    def _on_area_changed(self):
        area = self.cmb_dest_area.currentData()
        self.cmb_dest_bin.clear()
        self.cmb_dest_bin.addItem("-- Bin יעד --", None)
        if area:
            for b in db.get_bins_for_area(area):
                self.cmb_dest_bin.addItem(b, b)

    def _on_pallet_changed(self):
        pallet_id = self.cmb_pallet.currentData()
        if pallet_id is None:
            self._clear_detail()
            return
        pallet = db.get_pallet(pallet_id)
        if not pallet:
            self._clear_detail()
            return

        self.lbl_create.setText(f"תאריך הקמה: {pallet['CreateDate'] or '–'}")
        self.lbl_status.setText(f"סטטוס: {pallet['Status'] or '–'}")
        self.lbl_target.setText(f"איתור נוכחי: {pallet['TargetBin'] or '–'}")

        status = pallet["Status"]
        self.lbl_in_stock.setText(f"{'☑' if status=='ממוקם' else '☐'} ממוקם (נמצא במחסן היעד)")
        self.lbl_set_up.setText(f"{'☑' if status=='הוקם'  else '☐'} הוקם")
        self.lbl_departed.setText(f"{'☑' if status=='יצא'   else '☐'} יצא (באמצע שליחה)")
        self.lbl_status_legend.setText(f"** סטטוס נוכחי: {status} **")

        items = db.get_pallet_items(pallet_id)
        self.tbl_items.setRowCount(len(items))
        ITEM_KEYS = ["Pn", "Material", "UnitOfMeasure", "Batch", "WBS",
                     "Storage", "StorageType", "Bin", "Qty",
                     "DedicatedStrategy", "MultiLocation"]
        for r, item in enumerate(items):
            for c, key in enumerate(ITEM_KEYS):
                val = item[key] if key in item.keys() else ""
                it  = QTableWidgetItem(str(val or ""))
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_items.setItem(r, c, it)
            self.tbl_items.setRowHeight(r, 44)

    def _clear_detail(self):
        self.lbl_create.setText("תאריך הקמה: –")
        self.lbl_status.setText("סטטוס: –")
        self.lbl_target.setText("איתור נוכחי: –")
        self.lbl_status_legend.setText("")
        self.tbl_items.setRowCount(0)
        for lbl in [self.lbl_in_stock, self.lbl_set_up, self.lbl_departed]:
            lbl.setText(lbl.text().replace("☑", "☐"))

    def _do_assign(self):
        pallet_id = self.cmb_pallet.currentData()
        area      = self.cmb_dest_area.currentData()
        bin_val   = self.cmb_dest_bin.currentData()

        if not pallet_id:
            QMessageBox.warning(self, "שגיאה", "יש לבחור משטח")
            return
        if not area or not bin_val:
            QMessageBox.warning(self, "שגיאה", "יש לבחור אזור יעד ו-Bin יעד")
            return

        target_bin = f"{area}/{bin_val}"
        try:
            db.assign_pallet_to_bin(pallet_id, target_bin, self.username)
            self._on_pallet_changed()
            self._reload_pallets()
            QMessageBox.information(self, "הצלחה", f"משטח {pallet_id} שויך לאיתור {target_bin} ✓")
        except ValueError as e:
            QMessageBox.critical(self, "שגיאת שיוך", str(e))

    def _apply_item_col_visibility(self):
        for i in range(11):
            self.tbl_items.setColumnHidden(i, db.get_col_hidden(f"item_col_{i}"))

    def refresh(self):
        self._reload_pallets()
        self._load_areas()
        self._apply_item_col_visibility()
