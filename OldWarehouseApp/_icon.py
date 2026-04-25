from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QPainterPath, QBrush, QPolygonF
from PyQt6.QtCore import Qt, QRectF, QPointF


def app_icon() -> QIcon:
    S = 256
    px = QPixmap(S, S)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    bg = QPainterPath()
    bg.addRoundedRect(QRectF(0, 0, S, S), 52, 52)
    p.fillPath(bg, QColor("#1565C0"))
    p.setPen(Qt.PenStyle.NoPen)

    # White warehouse: roof triangle + body rectangle + door cutout
    p.setBrush(QBrush(Qt.GlobalColor.white))
    p.drawPolygon(QPolygonF([
        QPointF(128, 54),
        QPointF(20, 144),
        QPointF(236, 144),
    ]))
    p.drawRect(QRectF(42, 144, 172, 78))

    # Door – same colour as background makes a clean hole
    p.setBrush(QBrush(QColor("#1565C0")))
    p.drawRoundedRect(QRectF(98, 163, 60, 59), 7, 7)

    p.end()
    icon = QIcon()
    icon.addPixmap(px)
    return icon
