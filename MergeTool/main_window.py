import os
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QTabWidget, QGroupBox,
    QLineEdit, QComboBox, QFileDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QTextEdit, QProgressBar, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
import database as db
import excel_handler as xh
import styles


class MainWindow(QMainWindow):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self.setWindowTitle("WMS – כלי איחוד קבצים")
        self.setMinimumSize(1000, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._apply_theme(db.get_setting("theme", "light"))
        self._build_ui()
        self._start_clock()

    def _apply_theme(self, t):
        self.setStyleSheet(styles.get_theme(t))

    def _build_ui(self):
        c = QWidget()
        self.setCentralWidget(c)
        root = QVBoxLayout(c)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        tabs = QTabWidget()
        tabs.addTab(self._merge_tab(),    "🔀 איחוד קבצים")
        tabs.addTab(self._results_tab(),  "📊 תוצאות")
        tabs.addTab(self._settings_tab(), "⚙ הגדרות")
        tabs.addTab(self._log_tab(),      "📋 לוג פעולות")
        root.addWidget(tabs, 1)
        root.addWidget(self._build_status_bar())

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        h = QFrame(); h.setObjectName("header_bar"); h.setFixedHeight(64)
        lay = QHBoxLayout(h); lay.setContentsMargins(20, 0, 20, 0)
        btn_logout = QPushButton("🚪 יציאה")
        btn_logout.setObjectName("btn_menu")
        btn_logout.clicked.connect(self._logout)
        lay.addWidget(btn_logout)
        lay.addStretch()
        t = QLabel("WMS – כלי איחוד קבצי מחסנים")
        t.setObjectName("header_title")
        t.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        lay.addWidget(t)
        return h

    # ── Merge tab ─────────────────────────────────────────────────────────────

    def _merge_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(18)

        title = QLabel("איחוד קבצי יצוא יומי")
        title.setObjectName("title_label")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        # Old warehouse file
        grp_old = QGroupBox("קובץ יצוא – מחסן ישן (InventoryExport)")
        g_old = QVBoxLayout(grp_old); g_old.setSpacing(10)
        row_old = QHBoxLayout()
        self.txt_old_file = QLineEdit(); self.txt_old_file.setPlaceholderText("נתיב קובץ Excel...")
        btn_old = QPushButton("בחר קובץ")
        btn_old.setObjectName("btn_secondary")
        btn_old.clicked.connect(lambda: self._pick_file(self.txt_old_file))
        row_old.addWidget(btn_old); row_old.addWidget(self.txt_old_file)
        g_old.addLayout(row_old)
        self.lbl_old_status = QLabel("לא נטען")
        self.lbl_old_status.setObjectName("status_label")
        g_old.addWidget(self.lbl_old_status)
        lay.addWidget(grp_old)

        # New warehouse file
        grp_new = QGroupBox("קובץ יצוא – מחסן חדש (PalletAssignments)")
        g_new = QVBoxLayout(grp_new); g_new.setSpacing(10)
        row_new = QHBoxLayout()
        self.txt_new_file = QLineEdit(); self.txt_new_file.setPlaceholderText("נתיב קובץ Excel...")
        btn_new = QPushButton("בחר קובץ")
        btn_new.setObjectName("btn_secondary")
        btn_new.clicked.connect(lambda: self._pick_file(self.txt_new_file))
        row_new.addWidget(btn_new); row_new.addWidget(self.txt_new_file)
        g_new.addLayout(row_new)
        self.lbl_new_status = QLabel("לא נטען")
        self.lbl_new_status.setObjectName("status_label")
        g_new.addWidget(self.lbl_new_status)
        lay.addWidget(grp_new)

        # Action
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setRange(0, 0)
        lay.addWidget(self.progress)

        btn_merge = QPushButton("▶ בצע איחוד")
        btn_merge.setMinimumHeight(56)
        btn_merge.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        btn_merge.clicked.connect(self._do_merge)
        lay.addWidget(btn_merge)

        self.lbl_merge_result = QLabel("")
        self.lbl_merge_result.setObjectName("section_title")
        self.lbl_merge_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.lbl_merge_result)

        lay.addStretch()
        return w

    # ── Results tab ───────────────────────────────────────────────────────────

    def _results_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(16, 14, 16, 14); lay.setSpacing(10)

        f_lay = QHBoxLayout()
        self.txt_res_pn     = QLineEdit(); self.txt_res_pn.setPlaceholderText("חיפוש PN")
        self.cmb_res_status = QComboBox()
        self.cmb_res_status.addItems(["הכל", "הוקם", "ממוקם", "יצא", ""])
        self.txt_res_pal    = QLineEdit(); self.txt_res_pal.setPlaceholderText("מס' משטח")
        btn_filter = QPushButton("סנן")
        btn_filter.clicked.connect(self._load_results)
        btn_export = QPushButton("💾 יצוא Excel")
        btn_export.setObjectName("btn_secondary")
        btn_export.clicked.connect(self._export_unified)

        f_lay.addWidget(btn_export)
        f_lay.addWidget(btn_filter)
        f_lay.addWidget(self.txt_res_pal)
        f_lay.addWidget(self.cmb_res_status)
        f_lay.addWidget(self.txt_res_pn)
        lay.addLayout(f_lay)

        cols = ["Cat", "PN", "Batch", "WBS", "Storage", "Area", "Bin",
                "Qty", "PalletID", "IsInStock", "TargetBin", "Status", "MergeDate"]
        self.tbl_results = QTableWidget(0, len(cols))
        self.tbl_results.setHorizontalHeaderLabels(cols)
        hh = self.tbl_results.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_results.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_results.setAlternatingRowColors(True)
        self.tbl_results.verticalHeader().setVisible(False)
        lay.addWidget(self.tbl_results)

        self.lbl_res_count = QLabel("")
        self.lbl_res_count.setStyleSheet("font-size: 12px; color: #757575;")
        lay.addWidget(self.lbl_res_count)
        return w

    # ── Settings tab ─────────────────────────────────────────────────────────

    def _settings_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(16)
        grp = QGroupBox("הגדרות כלי האיחוד")
        g = QVBoxLayout(grp); g.setSpacing(12)

        g.addWidget(QLabel("נתיב יצוא תוצאות:"))
        r1 = QHBoxLayout()
        self.txt_export = QLineEdit(db.get_setting("export_path") or r"C:\Temp\Merge_XLS_WH")
        btn_e = QPushButton("עיון..."); btn_e.setObjectName("btn_secondary")
        btn_e.clicked.connect(lambda: self._browse(self.txt_export))
        r1.addWidget(btn_e); r1.addWidget(self.txt_export)
        g.addLayout(r1)

        g.addWidget(QLabel("נתיב ארכיון:"))
        r2 = QHBoxLayout()
        self.txt_archive = QLineEdit(db.get_setting("archive_path"))
        btn_a = QPushButton("עיון..."); btn_a.setObjectName("btn_secondary")
        btn_a.clicked.connect(lambda: self._browse(self.txt_archive))
        r2.addWidget(btn_a); r2.addWidget(self.txt_archive)
        g.addLayout(r2)

        g.addWidget(QLabel("ערכת עיצוב:"))
        self.cmb_theme = QComboBox()
        self.cmb_theme.addItem("בהיר", "light"); self.cmb_theme.addItem("כהה", "dark")
        idx = 0 if db.get_setting("theme", "light") == "light" else 1
        self.cmb_theme.setCurrentIndex(idx)
        g.addWidget(self.cmb_theme)

        btn_save = QPushButton("שמור הגדרות")
        btn_save.clicked.connect(self._save_settings)
        g.addWidget(btn_save)

        # User management
        grp_u = QGroupBox("משתמשים")
        gu = QVBoxLayout(grp_u); gu.setSpacing(10)
        ar = QHBoxLayout()
        self.txt_new_user = QLineEdit(); self.txt_new_user.setPlaceholderText("שם עובד חדש")
        btn_au = QPushButton("הוסף")
        btn_au.clicked.connect(self._add_user)
        ar.addWidget(btn_au); ar.addWidget(self.txt_new_user)
        gu.addLayout(ar)
        self.tbl_users = QTableWidget(0, 2)
        self.tbl_users.setHorizontalHeaderLabels(["שם", "פעיל"])
        self.tbl_users.setMaximumHeight(160)
        gu.addWidget(self.tbl_users)
        self._reload_users()

        lay.addWidget(grp)
        lay.addWidget(grp_u)
        lay.addStretch()
        return w

    # ── Log tab ───────────────────────────────────────────────────────────────

    def _log_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(16, 14, 16, 14); lay.setSpacing(10)
        f = QHBoxLayout()
        self.txt_log_search = QLineEdit(); self.txt_log_search.setPlaceholderText("חיפוש...")
        self.txt_log_from   = QLineEdit(); self.txt_log_from.setPlaceholderText("מתאריך")
        self.txt_log_to     = QLineEdit(); self.txt_log_to.setPlaceholderText("עד תאריך")
        btn_f = QPushButton("סנן")
        btn_f.clicked.connect(self._filter_logs)
        f.addWidget(btn_f); f.addWidget(self.txt_log_to)
        f.addWidget(self.txt_log_from); f.addWidget(self.txt_log_search)
        lay.addLayout(f)
        self.tbl_log = QTableWidget(0, 5)
        self.tbl_log.setHorizontalHeaderLabels(["זמן", "משתמש", "אפליקציה", "פעולה", "פרטים"])
        self.tbl_log.horizontalHeader().setStretchLastSection(True)
        self.tbl_log.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_log.setAlternatingRowColors(True)
        lay.addWidget(self.tbl_log)
        self._filter_logs()
        return w

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_status_bar(self):
        bar = QFrame(); bar.setObjectName("status_bar"); bar.setFixedHeight(36)
        lay = QHBoxLayout(bar); lay.setContentsMargins(16, 0, 16, 0)
        self.lbl_user  = QLabel(f"משתמש: {self.username}")
        self.lbl_user.setObjectName("status_label")
        self.lbl_clock = QLabel(); self.lbl_clock.setObjectName("status_label")
        self.lbl_last  = QLabel(f"איחוד אחרון: {db.get_setting('last_merge_date') or 'לא בוצע'}")
        self.lbl_last.setObjectName("status_label")
        lay.addWidget(self.lbl_last); lay.addStretch()
        lay.addWidget(self.lbl_clock); lay.addWidget(self.lbl_user)
        return bar

    def _start_clock(self):
        self._tick()
        t = QTimer(self); t.timeout.connect(self._tick); t.start(1000)

    def _tick(self):
        self.lbl_clock.setText(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _pick_file(self, target: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(self, "בחר קובץ Excel", "", "Excel Files (*.xlsx *.xls)")
        if path:
            target.setText(path)

    def _browse(self, target: QLineEdit):
        path = QFileDialog.getExistingDirectory(self, "בחר תיקייה", target.text())
        if path:
            target.setText(path)

    def _do_merge(self):
        old_path = self.txt_old_file.text().strip()
        new_path = self.txt_new_file.text().strip()

        if not old_path:
            QMessageBox.warning(self, "שגיאה", "יש לבחור קובץ יצוא מהמחסן הישן")
            return

        self.progress.setVisible(True)
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            # Load old warehouse
            old_rows = xh.load_old_warehouse_xlsx(old_path)
            self.lbl_old_status.setText(f"✔ נטענו {len(old_rows)} שורות")
            db.log(self.username, "LOAD_OLD_FILE", f"{old_path} → {len(old_rows)} שורות")

            # Load new warehouse (optional)
            new_rows = []
            if new_path:
                new_rows = xh.load_new_warehouse_xlsx(new_path)
                self.lbl_new_status.setText(f"✔ נטענו {len(new_rows)} משטחים ייחודיים")
                db.log(self.username, "LOAD_NEW_FILE", f"{new_path} → {len(new_rows)} משטחים")
            else:
                self.lbl_new_status.setText("(לא נבחר קובץ – ממשיך ללא נתוני מחסן חדש)")

            # Archive prev unified and load staging
            db.archive_unified_to_prev()
            db.clear_staging_old()
            db.bulk_insert_staging_old(old_rows)
            db.clear_staging_new()
            if new_rows:
                db.bulk_insert_staging_new(new_rows)

            # Run merge
            count = db.run_merge(self.username)

            # Auto-export to output path
            archive_dir  = db.get_setting("archive_path")
            export_dir   = db.get_setting("export_path") or r"C:\Temp\Merge_XLS_WH"
            unified_rows = db.get_unified_inventory()
            arc_path     = xh.archive_path(export_dir, "FinalOutput")
            xh.export_unified_xlsx(unified_rows, arc_path)
            db.log(self.username, "EXPORT_UNIFIED", f"{arc_path}")

            # Archive copy under archive_dir/Merge_TIMESTAMP/
            merge_arc = None
            if archive_dir:
                merge_arc = xh.merge_archive_path(archive_dir)
                shutil.copy2(arc_path, merge_arc)
                db.log(self.username, "ARCHIVE_MERGE", f"ארכיון: {merge_arc}")

            self.progress.setVisible(False)
            self.lbl_merge_result.setText(f"✔  האיחוד הושלם! {count} שורות בקובץ המאוחד")
            self.lbl_last.setText(f"איחוד אחרון: {db.get_setting('last_merge_date')}")

            msg = (
                f"האיחוד הושלם בהצלחה!\n\n"
                f"שורות מאוחדות: {count}\n"
                f"קובץ יצוא:\n{arc_path}"
            )
            if merge_arc:
                msg += f"\n\nארכיון:\n{merge_arc}"
            QMessageBox.information(self, "איחוד הושלם", msg)
            self._load_results()

        except Exception as e:
            self.progress.setVisible(False)
            db.log(self.username, "MERGE_ERROR", str(e))
            QMessageBox.critical(self, "שגיאת איחוד", str(e))

    def _load_results(self):
        pn      = self.txt_res_pn.text().strip()
        status  = self.cmb_res_status.currentText()
        pal_id  = self.txt_res_pal.text().strip()
        if status in ("הכל", ""):
            status = ""
        rows = db.get_unified_inventory(pn, status, pal_id)

        db_keys = ["Cat", "Pn", "Batch", "WBS", "Storage", "Area", "Bin",
                   "Qty", "PalletID", "IsInStock", "TargetBin", "Status", "MergeDate"]
        STATUS_COLORS = {"ממוקם": QColor("#C8E6C9"), "יצא": QColor("#BBDEFB"), "הוקם": QColor("#FFF9C4")}

        self.tbl_results.setRowCount(len(rows))
        for r, row in enumerate(rows):
            status_val = row["Status"] or ""
            for c, key in enumerate(db_keys):
                val = row[key] if key in row.keys() else ""
                if key == "IsInStock":
                    val = "כן" if val else "לא"
                item = QTableWidgetItem(str(val or ""))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if status_val in STATUS_COLORS:
                    item.setBackground(STATUS_COLORS[status_val])
                self.tbl_results.setItem(r, c, item)
            self.tbl_results.setRowHeight(r, 44)
        self.lbl_res_count.setText(f"מציג {len(rows)} שורות")

    def _export_unified(self):
        rows = db.get_unified_inventory(
            self.txt_res_pn.text().strip(),
            "" if self.cmb_res_status.currentText() in ("הכל", "") else self.cmb_res_status.currentText(),
            self.txt_res_pal.text().strip(),
        )
        if not rows:
            QMessageBox.warning(self, "אזהרה", "אין נתונים לייצוא")
            return
        export_dir = db.get_setting("export_path") or r"C:\Temp\Merge_XLS_WH"
        arc_path   = xh.archive_path(export_dir, "UnifiedInventory_Export")
        xh.export_unified_xlsx(rows, arc_path)
        db.log(self.username, "EXPORT_UNIFIED", f"{arc_path}")
        QMessageBox.information(self, "הצלחה", f"יוצא:\n{arc_path}")

    def _save_settings(self):
        db.set_setting("export_path",  self.txt_export.text().strip())
        db.set_setting("archive_path", self.txt_archive.text().strip())
        new_theme = self.cmb_theme.currentData()
        db.set_setting("theme", new_theme)
        self._apply_theme(new_theme)
        db.log(self.username, "SAVE_SETTINGS", "הגדרות נשמרו")
        QMessageBox.information(self, "הצלחה", "ההגדרות נשמרו ✓")

    def _add_user(self):
        name = self.txt_new_user.text().strip()
        if name:
            try:
                db.add_user(name)
                self.txt_new_user.clear()
                self._reload_users()
            except Exception as e:
                QMessageBox.warning(self, "שגיאה", str(e))

    def _reload_users(self):
        users = db.get_all_users()
        self.tbl_users.setRowCount(len(users))
        for r, u in enumerate(users):
            self.tbl_users.setItem(r, 0, QTableWidgetItem(u["FullName"]))
            self.tbl_users.setItem(r, 1, QTableWidgetItem("✔" if u["IsActive"] else "✘"))
            self.tbl_users.setRowHeight(r, 44)

    def _filter_logs(self):
        logs = db.get_logs(
            from_date=self.txt_log_from.text().strip(),
            to_date=self.txt_log_to.text().strip(),
            search=self.txt_log_search.text().strip(),
        )
        self.tbl_log.setRowCount(len(logs))
        for r, row in enumerate(logs):
            for c, key in enumerate(["Timestamp", "UserName", "ApplicationName", "ActionType", "Details"]):
                self.tbl_log.setItem(r, c, QTableWidgetItem(str(row[key] or "")))
            self.tbl_log.setRowHeight(r, 44)

    def _logout(self):
        db.log(self.username, "LOGOUT", "יציאה")
        from login_window import LoginWindow
        login = LoginWindow()
        if login.exec():
            self.username = login.selected_user
            self.lbl_user.setText(f"משתמש: {self.username}")
