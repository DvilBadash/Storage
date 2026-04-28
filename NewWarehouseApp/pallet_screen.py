from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCompleter, QFrame, QCheckBox, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import database as db


class PalletAssignmentScreen(QWidget):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self._blocking = False
        self._build_ui()
        self.detail_frame.hide()
        self.btn_assign.setEnabled(False)
        QTimer.singleShot(0, self.refresh)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(14)

        # ── Title ─────────────────────────────────────────────────────────────
        self.lbl_title = QLabel("שלב 2: שיוך משטח לאיתור יעד")
        self.lbl_title.setObjectName("section_title")
        root.addWidget(self.lbl_title)

        # ── Selector row: pallet + location side-by-side ──────────────────────
        sel_row = QHBoxLayout()
        sel_row.setSpacing(12)

        loc_frame = QFrame()
        loc_frame.setObjectName("card")
        loc_lay = QVBoxLayout(loc_frame)
        loc_lay.setContentsMargins(14, 12, 14, 12)
        loc_lay.setSpacing(8)
        lbl_loc = QLabel("📍  בחר איתור יעד")
        _f = QFont("Segoe UI"); _f.setPixelSize(16); _f.setBold(True); lbl_loc.setFont(_f)
        self.cmb_dest = QComboBox()
        self.cmb_dest.setMinimumHeight(44)
        self.cmb_dest.setEditable(True)
        self.cmb_dest.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        _cd = QCompleter(self.cmb_dest.model(), self.cmb_dest)
        _cd.setFilterMode(Qt.MatchFlag.MatchContains)
        _cd.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        _cd.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.cmb_dest.setCompleter(_cd)
        loc_lay.addWidget(lbl_loc)
        loc_lay.addWidget(self.cmb_dest)

        pal_frame = QFrame()
        pal_frame.setObjectName("card")
        pal_lay = QVBoxLayout(pal_frame)
        pal_lay.setContentsMargins(14, 12, 14, 12)
        pal_lay.setSpacing(8)
        lbl_pal = QLabel("🚚  בחר מס' משטח")
        _f = QFont("Segoe UI"); _f.setPixelSize(16); _f.setBold(True); lbl_pal.setFont(_f)
        self.cmb_pallet = QComboBox()
        self.cmb_pallet.setMinimumHeight(44)
        self.cmb_pallet.setEditable(True)
        self.cmb_pallet.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        _cp = QCompleter(self.cmb_pallet.model(), self.cmb_pallet)
        _cp.setFilterMode(Qt.MatchFlag.MatchContains)
        _cp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        _cp.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.cmb_pallet.setCompleter(_cp)
        self.cmb_pallet.currentIndexChanged.connect(self._on_pallet_changed)
        pal_lay.addWidget(lbl_pal)
        pal_lay.addWidget(self.cmb_pallet)

        sel_row.addWidget(loc_frame)
        sel_row.addWidget(pal_frame)
        root.addLayout(sel_row)

        # ── Detail card ───────────────────────────────────────────────────────
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("card")
        det_lay = QVBoxLayout(self.detail_frame)
        det_lay.setContentsMargins(18, 14, 18, 14)
        det_lay.setSpacing(12)

        self.lbl_pal_title = QLabel("פרטי משטח")
        _f = QFont("Segoe UI"); _f.setPixelSize(19); _f.setBold(True); self.lbl_pal_title.setFont(_f)
        det_lay.addWidget(self.lbl_pal_title)

        status_row = QHBoxLayout()
        lbl_pencil = QLabel("✏")
        _f = QFont("Segoe UI"); _f.setPixelSize(19); lbl_pencil.setFont(_f)
        self.lbl_status_current = QLabel("סטטוס נוכחי: –")
        _f = QFont("Segoe UI"); _f.setPixelSize(19); _f.setBold(True); self.lbl_status_current.setFont(_f)
        status_row.addStretch()
        status_row.addWidget(lbl_pencil)
        status_row.addWidget(self.lbl_status_current)
        det_lay.addLayout(status_row)

        # Status checkboxes (radio-like: only one selected at a time)
        self.chk_placed = QCheckBox("ממוקם (נמצא במחסן היעד)")
        self.chk_setup  = QCheckBox("הוקם")
        self.chk_sent   = QCheckBox("יצא (באמצעות משלוח)")
        for chk in [self.chk_placed, self.chk_setup, self.chk_sent]:
            chk.setMinimumHeight(38)
            det_lay.addWidget(chk)
        self.chk_placed.toggled.connect(lambda v: self._radio_check("ממוקם", v))
        self.chk_setup.toggled.connect(lambda v:  self._radio_check("הוקם",  v))
        self.chk_sent.toggled.connect(lambda v:   self._radio_check("יצא",   v))

        root.addWidget(self.detail_frame)

        # ── Assign button ─────────────────────────────────────────────────────
        self.btn_assign = QPushButton("בצע שיוך ועדכן סטטוס")
        self.btn_assign.setMinimumHeight(54)
        self.btn_assign.clicked.connect(self._do_assign)
        root.addWidget(self.btn_assign)

        # ── Legend ────────────────────────────────────────────────────────────
        leg_frame = QFrame()
        leg_frame.setObjectName("card")
        leg_lay = QVBoxLayout(leg_frame)
        leg_lay.setContentsMargins(16, 12, 16, 12)
        leg_lay.setSpacing(4)

        lbl_leg_hdr = QLabel("** מקרא סטטוסים **")
        _f = QFont("Segoe UI"); _f.setPixelSize(16); _f.setBold(True); lbl_leg_hdr.setFont(_f)
        lbl_leg_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        leg_lay.addWidget(lbl_leg_hdr)
        for txt in [
            "ממוקם = המשטח נמצא במחסן היעד.",
            "הוקם = המשטח הוקם והוא מוכן להעברה.",
            "יצא = המשטח יצא מהמחסן ונמצא באמצע שליחה.",
        ]:
            lbl = QLabel(txt)
            _f = QFont("Segoe UI"); _f.setPixelSize(15); lbl.setFont(_f)
            leg_lay.addWidget(lbl)

        root.addWidget(leg_frame)
        root.addStretch()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _radio_check(self, status: str, checked: bool):
        """Ensure only one status checkbox is active at a time."""
        if self._blocking or not checked:
            return
        self._blocking = True
        self.chk_placed.setChecked(status == "ממוקם")
        self.chk_setup.setChecked(status  == "הוקם")
        self.chk_sent.setChecked(status   == "יצא")
        self.lbl_status_current.setText(f"סטטוס נוכחי: {status}")
        self._blocking = False

    def _selected_status(self) -> str:
        if self.chk_placed.isChecked(): return "ממוקם"
        if self.chk_sent.isChecked():   return "יצא"
        return "הוקם"

    def _reload_pallets(self):
        self.cmb_pallet.blockSignals(True)
        self.cmb_pallet.clear()
        self.cmb_pallet.addItem("-- בחר משטח --", None)
        for p in db.get_pallets():
            icon = {"ממוקם": "✔", "יצא": "→", "הוקם": "●"}.get(p["Status"], "")
            self.cmb_pallet.addItem(f"{icon}  {p['PalletID']}", p["PalletID"])
        self.cmb_pallet.blockSignals(False)

    def _reload_locations(self):
        self.cmb_dest.clear()
        self.cmb_dest.addItem("-- בחר איתור יעד --", None)
        for loc in db.get_all_dest_bins():
            self.cmb_dest.addItem(loc["Dest_BIN"], loc["Dest_BIN"])

    def _on_pallet_changed(self):
        pallet_id = self.cmb_pallet.currentData()
        if not pallet_id:
            self.detail_frame.hide()
            self.btn_assign.setEnabled(False)
            self.lbl_title.setText("שלב 2: שיוך משטח לאיתור יעד")
            return
        pallet = db.get_pallet(pallet_id)
        if not pallet:
            return

        self.detail_frame.show()
        self.btn_assign.setEnabled(True)
        self.lbl_title.setText(f"שלב 2: שיוך משטח לאיתור יעד ({pallet_id})")
        self.lbl_pal_title.setText(f"פרטי משטח {pallet_id}")

        # Pre-select current target bin
        target = pallet["TargetBin"] or ""
        idx = self.cmb_dest.findData(target)
        if idx < 0 and "/" in target:
            idx = self.cmb_dest.findData(target.split("/")[-1])
        if idx >= 0:
            self.cmb_dest.setCurrentIndex(idx)
        else:
            self.cmb_dest.setCurrentIndex(0)

        # Reflect current status in checkboxes
        status = pallet["Status"] or "הוקם"
        self.lbl_status_current.setText(f"סטטוס נוכחי: {status}")
        self._blocking = True
        self.chk_placed.setChecked(status == "ממוקם")
        self.chk_setup.setChecked(status  == "הוקם")
        self.chk_sent.setChecked(status   == "יצא")
        self._blocking = False

    def _do_assign(self):
        pallet_id = self.cmb_pallet.currentData()
        target    = self.cmb_dest.currentData()
        status    = self._selected_status()
        if not pallet_id:
            QMessageBox.warning(self, "שגיאה", "יש לבחור משטח")
            return
        if not target:
            QMessageBox.warning(self, "שגיאה", "יש לבחור איתור יעד")
            return
        try:
            db.assign_pallet_to_bin(pallet_id, target, status, self.username)
            self._on_pallet_changed()
            self._reload_pallets()
            QMessageBox.information(
                self, "הצלחה",
                f"משטח {pallet_id}\nאיתור: {target}\nסטטוס: {status} ✓"
            )
        except ValueError as e:
            QMessageBox.critical(self, "שגיאת שיוך", str(e))

    def refresh(self):
        self._reload_pallets()
        self._reload_locations()
        self._on_pallet_changed()
