from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import database as db
import styles
from home_screen import HomeScreen
from pallet_screen import PalletAssignmentScreen
from pallet_mgmt_screen import PalletManagementScreen
from settings_screen import SettingsScreen


class MainWindow(QMainWindow):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self.setWindowTitle("WMS – מחסן חדש")
        self.setMinimumSize(960, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._apply_theme(db.get_setting("theme", "light"))
        self._build_ui()
        self._start_clock()

    def _apply_theme(self, theme: str):
        self.setStyleSheet(styles.get_theme(theme))

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        self.stack = QStackedWidget()
        wh = db.get_setting("warehouse_name", "YYY")

        self.home_screen    = HomeScreen(wh, self.username)
        self.assign_screen  = PalletAssignmentScreen(self.username)
        self.mgmt_screen    = PalletManagementScreen(self.username)
        self.settings_screen = SettingsScreen(self.username)

        self.home_screen.go_assign.connect(self._show_assign)
        self.home_screen.go_manage.connect(self._show_manage)
        self.settings_screen.theme_changed.connect(self._apply_theme)

        self.stack.addWidget(self.home_screen)     # 0
        self.stack.addWidget(self.assign_screen)   # 1
        self.stack.addWidget(self.mgmt_screen)     # 2
        self.stack.addWidget(self.settings_screen) # 3

        root.addWidget(self.stack, 1)
        root.addWidget(self._build_status_bar())

    def _build_header(self):
        header = QFrame()
        header.setObjectName("header_bar")
        header.setFixedHeight(64)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(10)

        for text, slot in [("🏠 ראשי", self._show_home),
                            ("⚙ הגדרות", self._show_settings),
                            ("🚪 יציאה", self._logout)]:
            btn = QPushButton(text)
            btn.setObjectName("btn_menu")
            btn.clicked.connect(slot)
            lay.addWidget(btn)

        lay.addStretch()
        wh = db.get_setting("warehouse_name", "YYY")
        self.header_title = QLabel(f"WMS – ניהול העברת מלאי  |  מחסן: {wh}")
        self.header_title.setObjectName("header_title")
        self.header_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        lay.addWidget(self.header_title)
        return header

    def _build_status_bar(self):
        bar = QFrame()
        bar.setObjectName("status_bar")
        bar.setFixedHeight(36)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(20)
        self.lbl_user  = QLabel(f"משתמש: {self.username}")
        self.lbl_user.setObjectName("status_label")
        self.lbl_clock = QLabel()
        self.lbl_clock.setObjectName("status_label")
        self.lbl_last  = QLabel()
        self.lbl_last.setObjectName("status_label")
        self.update_status()
        lay.addWidget(self.lbl_last)
        lay.addStretch()
        lay.addWidget(self.lbl_clock)
        lay.addWidget(self.lbl_user)
        return bar

    def _start_clock(self):
        self._tick()
        t = QTimer(self); t.timeout.connect(self._tick); t.start(1000)

    def _tick(self):
        self.lbl_clock.setText(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

    def update_status(self):
        last = db.get_setting("last_pallet_import", "")
        self.lbl_last.setText(f"ייבוא אחרון: {last or 'לא בוצע'}")

    def _show_home(self):     self.stack.setCurrentIndex(0)
    def _show_assign(self):   self.assign_screen.refresh(); self.stack.setCurrentIndex(1)
    def _show_manage(self):   self.mgmt_screen.refresh();   self.stack.setCurrentIndex(2)
    def _show_settings(self): self.stack.setCurrentIndex(3)

    def _logout(self):
        db.log(self.username, "LOGOUT", "יציאה")
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
