from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QMessageBox,
)
from PyQt6.QtCore import Qt
import database as db


class LoginWindow(QDialog):
    def __init__(self, warehouse_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("כניסה למערכת")
        self.setMinimumSize(460, 340)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setModal(True)
        self.selected_user = None
        self._build_ui(warehouse_name)

    def _build_ui(self, wh):
        from PyQt6.QtWidgets import QFrame
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setObjectName("header_bar")
        header.setFixedHeight(70)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(24, 0, 24, 0)
        title = QLabel(f"WMS – {wh}")
        title.setObjectName("header_title")
        h_lay.addStretch()
        h_lay.addWidget(title)
        root.addWidget(header)

        body = QVBoxLayout()
        body.setContentsMargins(40, 30, 40, 30)
        body.setSpacing(18)

        lbl = QLabel("מערכת ניהול העברת מלאי")
        lbl.setObjectName("title_label")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(lbl)

        self.combo_user = QComboBox()
        self.combo_user.setMinimumHeight(48)
        self._reload_users()
        body.addWidget(QLabel("שם עובד:"))
        body.addWidget(self.combo_user)

        btn = QPushButton("כניסה")
        btn.setMinimumHeight(52)
        btn.clicked.connect(self._on_login)
        body.addWidget(btn)
        root.addLayout(body)

    def _reload_users(self):
        self.combo_user.clear()
        self.combo_user.addItem("-- בחר עובד --", None)
        for u in db.get_active_users():
            self.combo_user.addItem(u["FullName"], u["UserID"])

    def _on_login(self):
        if self.combo_user.currentData() is None:
            QMessageBox.warning(self, "שגיאה", "יש לבחור עובד")
            return
        self.selected_user = self.combo_user.currentText()
        db.log(self.selected_user, "LOGIN", "כניסה למערכת")
        self.accept()
