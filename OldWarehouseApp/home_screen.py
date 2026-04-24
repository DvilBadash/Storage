from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class StepCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, number: str, title: str, subtitle: str, icon: str = ""):
        super().__init__()
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(110)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(18)

        num_lbl = QLabel(number)
        num_lbl.setObjectName("step_num")
        num_lbl.setFixedSize(40, 40)
        num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))

        text_lay = QVBoxLayout()
        text_lay.setSpacing(4)
        t_lbl = QLabel(title)
        t_lbl.setObjectName("card_title")
        t_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        s_lbl = QLabel(subtitle)
        s_lbl.setObjectName("card_sub")
        text_lay.addWidget(t_lbl)
        text_lay.addWidget(s_lbl)

        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont("Segoe UI Emoji", 28))
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setFixedWidth(50)
            lay.addWidget(icon_lbl)

        lay.addLayout(text_lay)
        lay.addStretch()
        lay.addWidget(num_lbl)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class HomeScreen(QWidget):
    go_inventory = pyqtSignal()

    def __init__(self, warehouse_name: str, username: str):
        super().__init__()
        self.warehouse_name = warehouse_name
        self.username = username
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.setSpacing(20)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("תפריט ראשי: ביצוע העברה")
        title.setObjectName("title_label")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        lay.addWidget(title)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFixedHeight(1)
        lay.addWidget(sep)
        lay.addSpacing(10)

        card1 = StepCard("1", "בחירת איתור ושיוך מלאי למשטח",
                         "חפש פריטים, בחר איתור וצור שיוך למשטח", "🏭")
        card1.clicked.connect(self.go_inventory.emit)
        lay.addWidget(card1)

        lay.addStretch()

        info = QLabel("מספר העברה: INT-00001")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #9E9E9E; font-size: 12px;")
        lay.addWidget(info)
