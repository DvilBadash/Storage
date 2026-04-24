from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import database as db


class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("כלי איחוד – כניסה")
        self.setMinimumSize(420, 300)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.selected_user = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        header = QFrame(); header.setObjectName("header_bar"); header.setFixedHeight(65)
        h_lay = QHBoxLayout(header); h_lay.setContentsMargins(20, 0, 20, 0)
        t = QLabel("WMS – כלי איחוד"); t.setObjectName("header_title")
        h_lay.addStretch(); h_lay.addWidget(t)
        root.addWidget(header)

        body = QVBoxLayout(); body.setContentsMargins(36, 26, 36, 26); body.setSpacing(16)
        lbl = QLabel("כלי איחוד קבצי מחסנים")
        lbl.setObjectName("title_label"); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(lbl)
        body.addWidget(QLabel("שם עובד:"))
        self.combo = QComboBox(); self.combo.setMinimumHeight(46)
        self._reload()
        body.addWidget(self.combo)
        btn = QPushButton("כניסה")
        btn.setMinimumHeight(50); btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        btn.clicked.connect(self._on_login)
        body.addWidget(btn)
        root.addLayout(body)

    def _reload(self):
        self.combo.clear()
        self.combo.addItem("-- בחר עובד --", None)
        for u in db.get_active_users():
            self.combo.addItem(u["FullName"], u["UserID"])

    def _on_login(self):
        if self.combo.currentData() is None:
            QMessageBox.warning(self, "שגיאה", "יש לבחור עובד")
            return
        self.selected_user = self.combo.currentText()
        db.log(self.selected_user, "LOGIN", "כניסה")
        self.accept()
