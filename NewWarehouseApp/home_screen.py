from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
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

        text_lay = QVBoxLayout()
        text_lay.setSpacing(4)
        t_lbl = QLabel(title)
        t_lbl.setObjectName("card_title")
        s_lbl = QLabel(subtitle)
        s_lbl.setObjectName("card_sub")
        text_lay.addWidget(t_lbl)
        text_lay.addWidget(s_lbl)

        if icon:
            icon_lbl = QLabel(icon)
            _f = QFont("Segoe UI Emoji"); _f.setPixelSize(37); icon_lbl.setFont(_f)
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
    go_assign  = pyqtSignal()
    go_manage  = pyqtSignal()

    def __init__(self, warehouse_name: str, username: str):
        super().__init__()
        self._build_ui(warehouse_name)

    def _build_ui(self, warehouse_name: str):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.setSpacing(20)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("תפריט ראשי: ביצוע העברה")
        title.setObjectName("title_label")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        sep = QFrame(); sep.setObjectName("separator"); sep.setFixedHeight(1)
        lay.addWidget(sep)
        lay.addSpacing(10)

        card1 = StepCard("1", "שיוך משטח לאיתור יעד",
                         "שייך את המשטחים לאיתור היעד הנבחר", "📦")
        card1.clicked.connect(self.go_assign.emit)
        lay.addWidget(card1)

        card2 = StepCard("2", "ניהול משטחים",
                         "צפה ועדכן סטטוס של כל המשטחים במחסן", "📋")
        card2.clicked.connect(self.go_manage.emit)
        lay.addWidget(card2)

        lay.addStretch()
