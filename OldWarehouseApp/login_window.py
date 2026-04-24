from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
import database as db


class LoginWindow(QDialog):
    def __init__(self, warehouse_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("כניסה למערכת")
        self.setMinimumSize(460, 380)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setModal(True)
        self.selected_user = None
        self._build_ui(warehouse_name)

    def _build_ui(self, warehouse_name: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("header_bar")
        header.setFixedHeight(80)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(24, 0, 24, 0)
        title = QLabel(f"WMS – {warehouse_name}")
        title.setObjectName("header_title")
        h_lay.addStretch()
        h_lay.addWidget(title)
        root.addWidget(header)

        # Body
        body = QVBoxLayout()
        body.setContentsMargins(40, 36, 40, 36)
        body.setSpacing(20)

        lbl_sys = QLabel("מערכת ניהול העברת מלאי")
        lbl_sys.setObjectName("title_label")
        lbl_sys.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(lbl_sys)

        lbl_sub = QLabel("בחר את שמך להמשך")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet("font-size: 14px; color: #616161;")
        body.addWidget(lbl_sub)

        body.addSpacing(8)

        lbl_user = QLabel("שם עובד:")
        lbl_user.setStyleSheet("font-size: 14px; font-weight: bold;")
        body.addWidget(lbl_user)

        self.combo_user = QComboBox()
        self.combo_user.setMinimumHeight(48)
        self.combo_user.setFont(QFont("Segoe UI", 13))
        self._reload_users()
        body.addWidget(self.combo_user)

        body.addSpacing(8)

        btn_login = QPushButton("כניסה")
        btn_login.setMinimumHeight(52)
        btn_login.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        btn_login.clicked.connect(self._on_login)
        body.addWidget(btn_login)

        root.addLayout(body)

    def _reload_users(self):
        self.combo_user.clear()
        self.combo_user.addItem("-- בחר עובד --", None)
        for u in db.get_active_users():
            self.combo_user.addItem(u["FullName"], u["UserID"])

    def _on_login(self):
        user = self.combo_user.currentData()
        if user is None:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "שגיאה", "יש לבחור עובד לפני הכניסה")
            return
        self.selected_user = self.combo_user.currentText()
        db.log(self.selected_user, "LOGIN", "כניסה למערכת")
        self.accept()
