from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import database as db
import styles
from home_screen import HomeScreen
from inventory_screen import InventoryScreen
from settings_screen import SettingsScreen


class MainWindow(QMainWindow):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self.setWindowTitle("WMS – ניהול העברת מלאי מלאי מחסנים")
        self.setMinimumSize(900, 680)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._apply_theme(db.get_setting("theme", "light"))
        self._build_ui()
        self._start_clock()

    # ── Theme ──────────────────────────────────────────────────────────────────

    def _apply_theme(self, theme: str):
        self.setStyleSheet(styles.get_theme(theme))

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        self.stack = QStackedWidget()
        wh_name = db.get_setting("warehouse_name", "XXX")

        self.home_screen     = HomeScreen(wh_name, self.username)
        self.inventory_screen = InventoryScreen(self.username)
        self.settings_screen  = SettingsScreen(self.username)

        self.home_screen.go_inventory.connect(self._show_inventory)
        self.settings_screen.theme_changed.connect(self._apply_theme)

        self.stack.addWidget(self.home_screen)      # 0
        self.stack.addWidget(self.inventory_screen) # 1
        self.stack.addWidget(self.settings_screen)  # 2

        root.addWidget(self.stack, 1)
        root.addWidget(self._build_status_bar())

    def _build_header(self):
        header = QFrame()
        header.setObjectName("header_bar")
        header.setFixedHeight(64)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(10)

        # Left side: nav buttons
        btn_home = QPushButton("🏠 ראשי")
        btn_home.setObjectName("btn_menu")
        btn_home.clicked.connect(self._show_home)

        btn_settings = QPushButton("⚙ הגדרות")
        btn_settings.setObjectName("btn_menu")
        btn_settings.clicked.connect(self._show_settings)

        btn_logout = QPushButton("🚪 יציאה")
        btn_logout.setObjectName("btn_menu")
        btn_logout.clicked.connect(self._logout)

        lay.addWidget(btn_logout)
        lay.addWidget(btn_settings)
        lay.addWidget(btn_home)
        lay.addStretch()

        # Center: title
        wh_name = db.get_setting("warehouse_name", "XXX")
        self.header_title = QLabel(f"WMS – ניהול העברת מלאי מחסנים  |  מחסן: {wh_name}")
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

        self.lbl_user = QLabel(f"משתמש: {self.username}")
        self.lbl_user.setObjectName("status_label")

        self.lbl_clock = QLabel()
        self.lbl_clock.setObjectName("status_label")

        self.lbl_last_load = QLabel()
        self.lbl_last_load.setObjectName("status_label")
        self.update_status()

        lay.addWidget(self.lbl_last_load)
        lay.addStretch()
        lay.addWidget(self.lbl_clock)
        lay.addWidget(self.lbl_user)
        return bar

    def _start_clock(self):
        self._tick()
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)

    def _tick(self):
        now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        self.lbl_clock.setText(now)

    def update_status(self):
        last = db.get_setting("last_load_date", "")
        self.lbl_last_load.setText(f"טעינה אחרונה: {last or 'לא בוצעה'}")

    # ── Navigation ─────────────────────────────────────────────────────────────

    def _show_home(self):
        self.stack.setCurrentIndex(0)

    def _show_inventory(self):
        self.inventory_screen.refresh()
        self.stack.setCurrentIndex(1)

    def _show_settings(self):
        self.stack.setCurrentIndex(2)

    def _logout(self):
        db.log(self.username, "LOGOUT", "יציאה מהמערכת")
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
