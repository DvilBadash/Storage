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
    p.fillPath(bg, QColor("#1B5E20"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(Qt.GlobalColor.white))

    # Upward arrow: triangle head + rectangular shaft
    p.drawPolygon(QPolygonF([
        QPointF(128, 42),
        QPointF(70, 132),
        QPointF(186, 132),
    ]))
    p.drawRect(QRectF(107, 132, 42, 62))

    # Pallet: flat board + two legs
    p.drawRoundedRect(QRectF(34, 194, 188, 20), 5, 5)
    p.drawRect(QRectF(54, 214, 40, 16))
    p.drawRect(QRectF(162, 214, 40, 16))

    p.end()
    icon = QIcon()
    icon.addPixmap(px)
    return icon
