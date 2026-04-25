from PyQt6.QtGui import (
    QIcon, QPixmap, QColor, QPainter, QPainterPath, QBrush, QPolygonF, QPen,
)
from PyQt6.QtCore import Qt, QRectF, QPointF


def app_icon() -> QIcon:
    S = 256
    px = QPixmap(S, S)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    bg = QPainterPath()
    bg.addRoundedRect(QRectF(0, 0, S, S), 52, 52)
    p.fillPath(bg, QColor("#E65100"))

    # Y-shape merge: two thick branches from top-left and bottom-left converging
    # into a single shaft that ends in an arrowhead pointing right
    pen = QPen(
        Qt.GlobalColor.white, 22,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
        Qt.PenJoinStyle.RoundJoin,
    )
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    p.drawLine(QPointF(34, 70),  QPointF(122, 128))   # upper branch
    p.drawLine(QPointF(34, 186), QPointF(122, 128))   # lower branch
    p.drawLine(QPointF(122, 128), QPointF(196, 128))  # right shaft

    # Arrowhead
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(Qt.GlobalColor.white))
    p.drawPolygon(QPolygonF([
        QPointF(190, 103),
        QPointF(238, 128),
        QPointF(190, 153),
    ]))

    p.end()
    icon = QIcon()
    icon.addPixmap(px)
    return icon
