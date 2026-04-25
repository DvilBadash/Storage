import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QGroupBox, QFileDialog, QMessageBox,
    QHeaderView, QAbstractItemView, QFrame,
    QScrollArea, QGridLayout, QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
import database as db
import excel_handler as xh


class SettingsScreen(QWidget):
    theme_changed = pyqtSignal(str)

    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        title = QLabel("הגדרות מערכת")
        title.setObjectName("section_title")
        root.addWidget(title)
        tabs = QTabWidget()
        tabs.addTab(self._general_tab(),  "כללי")
        tabs.addTab(self._data_tab(),     "נתונים")
        tabs.addTab(self._users_tab(),    "משתמשים")
        tabs.addTab(self._log_tab(),      "לוג פעולות")
        root.addWidget(tabs)

    def _general_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(20,20,20,20); lay.setSpacing(14)
        grp = QGroupBox("הגדרות בסיסיות")
        g = QVBoxLayout(grp); g.setSpacing(12)
        g.addWidget(QLabel("שם המחסן (YYY):"))
        self.txt_wh_name = QLineEdit()
        g.addWidget(self.txt_wh_name)
        g.addWidget(QLabel("נתיב יצוא:"))
        row = QHBoxLayout()
        self.txt_export = QLineEdit()
        btn = QPushButton("עיון...")
        btn.setObjectName("btn_secondary")
        btn.clicked.connect(lambda: self._browse(self.txt_export))
        row.addWidget(btn); row.addWidget(self.txt_export)
        g.addLayout(row)
        g.addWidget(QLabel("נתיב ארכיון:"))
        row2 = QHBoxLayout()
        self.txt_archive = QLineEdit()
        btn2 = QPushButton("עיון...")
        btn2.setObjectName("btn_secondary")
        btn2.clicked.connect(lambda: self._browse(self.txt_archive))
        row2.addWidget(btn2); row2.addWidget(self.txt_archive)
        g.addLayout(row2)
        g.addWidget(QLabel("ערכת עיצוב:"))
        self.cmb_theme = QComboBox()
        self.cmb_theme.addItem("בהיר", "light")
        self.cmb_theme.addItem("כהה",  "dark")
        g.addWidget(self.cmb_theme)
        btn_save = QPushButton("שמור הגדרות")
        btn_save.clicked.connect(self._save_general)
        g.addWidget(btn_save)
        lay.addWidget(grp); lay.addStretch()
        return w

    def _data_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(24, 24, 24, 24); lay.setSpacing(16)

        btn_inv = QPushButton("📂  טעינת קובץ מלאי")
        btn_inv.setMinimumHeight(52)
        btn_inv.clicked.connect(self._import_pallets)
        lay.addWidget(btn_inv)
        self.lbl_last_import = QLabel(f"ייבוא אחרון: {db.get_setting('last_pallet_import') or 'לא בוצע'}")
        self.lbl_last_import.setObjectName("status_label")
        lay.addWidget(self.lbl_last_import)

        btn_pal = QPushButton("📋  קליטת רשימת משטחים")
        btn_pal.setMinimumHeight(52)
        btn_pal.clicked.connect(self._load_pallet_codes)
        lay.addWidget(btn_pal)
        self.lbl_pallet_codes = QLabel(f"ייבוא אחרון: {db.get_setting('last_pallet_import') or 'לא בוצע'}")
        self.lbl_pallet_codes.setObjectName("status_label")
        lay.addWidget(self.lbl_pallet_codes)

        btn_exp = QPushButton("💾  יצוא שיוכים")
        btn_exp.setMinimumHeight(52)
        btn_exp.clicked.connect(self._export_assignments)
        lay.addWidget(btn_exp)

        lay.addStretch()
        return w

    def _columns_tab(self):
        """Rename column headers and toggle visibility for item and pallet tables."""
        w = QWidget()
        outer = QVBoxLayout(w); outer.setContentsMargins(20, 16, 20, 16); outer.setSpacing(14)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        grid = QGridLayout(container); grid.setSpacing(8); grid.setContentsMargins(0,0,12,0)

        from database import DEFAULT_ITEM_HEADERS, DEFAULT_PAL_HEADERS
        all_defaults = {**DEFAULT_ITEM_HEADERS, **DEFAULT_PAL_HEADERS}
        fields: dict[str, QLineEdit] = {}
        checks: dict[str, QCheckBox] = {}

        row_pos = 0
        for section, keys in [
            ("טבלת פריטי משטח:", [f"item_col_{i}" for i in range(11)]),
            ("טבלת ניהול משטחים:", [f"pal_col_{i}"  for i in range(6)]),
        ]:
            sec_lbl = QLabel(section)
            sec_lbl.setStyleSheet("font-weight:bold; color:#1565C0;")
            grid.addWidget(sec_lbl, row_pos, 0, 1, 3)
            row_pos += 1

            # Sub-header
            for col_idx, text in enumerate(["כותרת עמודה", "הצג", "ברירת מחדל"]):
                h = QLabel(text)
                h.setStyleSheet("font-weight:bold; color:#757575; font-size:11px;")
                grid.addWidget(h, row_pos, col_idx)
            row_pos += 1

            for key in keys:
                default = all_defaults.get(key, "")
                le = QLineEdit(db.get_setting(key, default))
                le.setMinimumHeight(40)
                cb = QCheckBox()
                cb.setChecked(not db.get_col_hidden(key))
                cb.setToolTip("מסומן = עמודה מוצגת")
                lbl = QLabel(f'"{default}"')
                lbl.setStyleSheet("color:#757575; font-size:12px;")
                grid.addWidget(le,  row_pos, 0)
                grid.addWidget(cb,  row_pos, 1)
                grid.addWidget(lbl, row_pos, 2)
                fields[key] = le
                checks[key] = cb
                row_pos += 1
            row_pos += 1  # gap between sections

        grid.setColumnStretch(0, 1)
        scroll.setWidget(container)
        outer.addWidget(scroll, 1)

        btn_row = QHBoxLayout()
        btn_reset = QPushButton("אפס לברירות מחדל"); btn_reset.setObjectName("btn_secondary")
        btn_save  = QPushButton("שמור כותרות")

        def _save():
            for key, le in fields.items():
                db.set_col_header(key, le.text().strip())
            for key, cb in checks.items():
                db.set_col_hidden(key, not cb.isChecked())
            db.log(self.username, "SAVE_COLUMN_HEADERS", "כותרות עמודות עודכנו")
            QMessageBox.information(w, "הצלחה",
                "הכותרות נשמרו ✓\nהשינויים יופיעו בפעם הבאה שהטבלה תיטען.")

        def _reset():
            for key, le in fields.items():
                default = all_defaults.get(key, "")
                le.setText(default)
                db.set_col_header(key, default)
            for key, cb in checks.items():
                cb.setChecked(True)
                db.set_col_hidden(key, False)
            QMessageBox.information(w, "אופס", "ברירות המחדל שוחזרו ✓")

        btn_reset.clicked.connect(_reset)
        btn_save.clicked.connect(_save)
        btn_row.addWidget(btn_reset); btn_row.addWidget(btn_save)
        outer.addLayout(btn_row)
        return w

    def _users_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)
        add_lay = QHBoxLayout()
        self.txt_new_user = QLineEdit()
        self.txt_new_user.setPlaceholderText("שם עובד חדש")
        btn_add = QPushButton("הוסף")
        btn_add.clicked.connect(self._add_user)
        add_lay.addWidget(btn_add); add_lay.addWidget(self.txt_new_user)
        lay.addLayout(add_lay)
        self.tbl_users = QTableWidget(0, 3)
        self.tbl_users.setHorizontalHeaderLabels(["שם עובד", "פעיל", "פעולה"])
        self.tbl_users.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl_users.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        lay.addWidget(self.tbl_users)
        self._reload_users_table()
        return w

    def _log_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)
        f_lay = QHBoxLayout()
        self.txt_log_search = QLineEdit(); self.txt_log_search.setPlaceholderText("חיפוש טקסט...")
        self.txt_log_from   = QLineEdit(); self.txt_log_from.setPlaceholderText("מתאריך YYYY-MM-DD")
        self.txt_log_to     = QLineEdit(); self.txt_log_to.setPlaceholderText("עד תאריך")
        self.cmb_log_action = QComboBox()
        self.cmb_log_action.addItems(["-- סוג פעולה --", "LOGIN", "IMPORT_PALLETS",
                                      "LOAD_LOCATIONS", "ASSIGN_PALLET_BIN",
                                      "UPDATE_PALLET_STATUS", "EXPORT_ASSIGNMENTS"])
        btn_f = QPushButton("סנן")
        btn_f.clicked.connect(self._filter_logs)
        f_lay.addWidget(btn_f)
        f_lay.addWidget(self.cmb_log_action)
        f_lay.addWidget(self.txt_log_to)
        f_lay.addWidget(self.txt_log_from)
        f_lay.addWidget(self.txt_log_search)
        lay.addLayout(f_lay)
        self.tbl_log = QTableWidget(0, 5)
        self.tbl_log.setHorizontalHeaderLabels(["זמן", "משתמש", "אפליקציה", "פעולה", "פרטים"])
        self.tbl_log.horizontalHeader().setStretchLastSection(True)
        self.tbl_log.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_log.setAlternatingRowColors(True)
        lay.addWidget(self.tbl_log)
        self._filter_logs()
        return w

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_settings(self):
        self.txt_wh_name.setText(db.get_setting("warehouse_name", "YYY"))
        self.txt_export.setText(db.get_setting("export_path"))
        self.txt_archive.setText(db.get_setting("archive_path"))
        theme = db.get_setting("theme", "light")
        self.cmb_theme.setCurrentIndex(0 if theme == "light" else 1)

    def _save_general(self):
        db.set_setting("warehouse_name", self.txt_wh_name.text().strip() or "YYY")
        db.set_setting("export_path",    self.txt_export.text().strip())
        db.set_setting("archive_path",   self.txt_archive.text().strip())
        new_theme = self.cmb_theme.currentData()
        db.set_setting("theme", new_theme)
        self.theme_changed.emit(new_theme)
        db.log(self.username, "SAVE_SETTINGS", "הגדרות נשמרו")
        QMessageBox.information(self, "הצלחה", "ההגדרות נשמרו ✓")

    def _browse(self, target: QLineEdit):
        path = QFileDialog.getExistingDirectory(self, "בחר תיקייה", target.text())
        if path:
            target.setText(path)

    def _load_locations(self):
        path, _ = QFileDialog.getOpenFileName(self, "בחר קובץ איתורים Excel", "", "Excel Files (*.xlsx *.xls)")
        if not path:
            return
        archive_dir = db.get_setting("archive_path")
        existing = db.get_dest_areas()
        if existing:
            pass  # minimal export for locations not needed (small data)
        try:
            rows = xh.load_locations_xlsx(path)
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", str(e))
            return
        db.clear_locations()
        db.bulk_insert_locations(rows)
        db.set_setting("last_load_date", __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        db.log(self.username, "LOAD_LOCATIONS", f"נטענו {len(rows)} איתורים מ: {path}")
        QMessageBox.information(self, "הצלחה", f"נטענו {len(rows)} איתורים ✓")

    # ── Archive helper ────────────────────────────────────────────────────────

    def _do_archive(self, prefix: str) -> str | None:
        rows = db.get_all_pallets_export()
        if not rows:
            return None
        arc_dir = db.get_setting(
            "archive_path",
            os.path.join(os.path.dirname(db.DB_PATH), "archive"),
        )
        path = xh.archive_path(arc_dir, prefix)
        xh.export_pallets_xlsx(rows, path)
        return path

    def _import_pallets(self):
        path, _ = QFileDialog.getOpenFileName(self, "בחר קובץ משטחים Excel", "", "Excel Files (*.xlsx *.xls)")
        if not path:
            return
        try:
            rows = xh.load_pallet_xlsx(path)
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", str(e))
            return
        db.import_pallets_from_rows(rows, self.username)
        self.lbl_last_import.setText(f"ייבוא אחרון: {db.get_setting('last_pallet_import')}")
        arc = self._do_archive("Import_FinalOutput")
        msg = f"יובאו {len(rows)} שורות משטחים ✓"
        if arc:
            msg += f"\nגיבוי ארכיון:\n{arc}"
        QMessageBox.information(self, "הצלחה", msg)

    def _load_pallet_codes(self):
        path, _ = QFileDialog.getOpenFileName(self, "בחר קובץ קודי משטחים Excel", "", "Excel Files (*.xlsx *.xls)")
        if not path:
            return
        try:
            codes = xh.load_pallet_codes_xlsx(path)
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", str(e))
            return
        if not codes:
            QMessageBox.warning(self, "אזהרה", "לא נמצאו קודי משטחים בקובץ")
            return
        db.bulk_insert_pallet_codes(codes, self.username)
        self.lbl_pallet_codes.setText(f"ייבוא אחרון: {db.get_setting('last_pallet_import')}")
        arc = self._do_archive("Import_PalletCodes")
        msg = f"נטענו {len(codes)} קודי משטחים ✓"
        if arc:
            msg += f"\nגיבוי ארכיון:\n{arc}"
        QMessageBox.information(self, "הצלחה", msg)

    def _create_pallet_codes_sample(self):
        export_dir = db.get_setting("export_path", os.path.expanduser("~/Desktop"))
        path = xh.archive_path(export_dir, "Pallets_Sample")
        xh.create_pallet_codes_sample(path)
        QMessageBox.information(self, "הצלחה", f"קובץ דוגמא נוצר:\n{path}")

    def _export_assignments(self):
        export_dir = db.get_setting("export_path", os.path.expanduser("~/Desktop"))
        rows = db.get_all_pallets_export()
        if not rows:
            QMessageBox.warning(self, "אזהרה", "אין נתונים לייצוא")
            return
        out_path = xh.archive_path(export_dir, "NewWarehouse_PalletAssignments")
        xh.export_pallets_xlsx(rows, out_path)
        arc = self._do_archive("Export_PalletAssignments")
        db.log(self.username, "EXPORT_ASSIGNMENTS", f"יוצא ל: {out_path}")
        msg = f"קובץ יוצא:\n{out_path}"
        if arc:
            msg += f"\n\nגיבוי ארכיון:\n{arc}"
        QMessageBox.information(self, "הצלחה", msg)

    def _reload_users_table(self):
        users = db.get_all_users()
        self.tbl_users.setRowCount(len(users))
        for r, u in enumerate(users):
            self.tbl_users.setItem(r, 0, QTableWidgetItem(u["FullName"]))
            active = QTableWidgetItem("✔ פעיל" if u["IsActive"] else "✘ מושהה")
            active.setForeground(Qt.GlobalColor.darkGreen if u["IsActive"] else Qt.GlobalColor.red)
            self.tbl_users.setItem(r, 1, active)
            btn = QPushButton("השהה" if u["IsActive"] else "הפעל")
            uid = u["UserID"]; ia = u["IsActive"]
            btn.clicked.connect(lambda _, uid=uid, ia=ia: self._toggle_user(uid, ia))
            self.tbl_users.setCellWidget(r, 2, btn)
            self.tbl_users.setRowHeight(r, 48)

    def _add_user(self):
        name = self.txt_new_user.text().strip()
        if not name:
            return
        try:
            db.add_user(name)
            self.txt_new_user.clear()
            self._reload_users_table()
            db.log(self.username, "ADD_USER", f"נוסף: {name}")
        except Exception as e:
            QMessageBox.warning(self, "שגיאה", str(e))

    def _toggle_user(self, uid, currently_active):
        db.set_user_active(uid, not currently_active)
        self._reload_users_table()

    def _filter_logs(self):
        action = self.cmb_log_action.currentText()
        if action.startswith("--"):
            action = ""
        logs = db.get_logs(
            from_date=self.txt_log_from.text().strip(),
            to_date=self.txt_log_to.text().strip(),
            action=action,
            search=self.txt_log_search.text().strip(),
        )
        self.tbl_log.setRowCount(len(logs))
        for r, row in enumerate(logs):
            for c, key in enumerate(["Timestamp", "UserName", "ApplicationName", "ActionType", "Details"]):
                self.tbl_log.setItem(r, c, QTableWidgetItem(str(row[key] or "")))
            self.tbl_log.setRowHeight(r, 44)
