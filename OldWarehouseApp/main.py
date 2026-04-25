import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont

import database as db
import styles
from login_window import LoginWindow
from main_window import MainWindow


def _make_splash(wh_name: str) -> QSplashScreen:
    px = QPixmap(500, 200)
    px.fill(QColor("#1565C0"))
    p = QPainter(px)
    p.setPen(QColor("white"))

    f_title = QFont("Segoe UI", 22)
    f_title.setBold(True)
    p.setFont(f_title)
    p.drawText(QRect(0, 35, 500, 70), Qt.AlignmentFlag.AlignCenter, f"WMS – {wh_name}")

    f_sub = QFont("Segoe UI", 13)
    p.setFont(f_sub)
    p.drawText(QRect(0, 120, 500, 45), Qt.AlignmentFlag.AlignCenter, "טוען את המערכת, אנא המתן...")

    p.end()
    return QSplashScreen(px, Qt.WindowType.WindowStaysOnTopHint)


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    db.init_db()

    if not db.get_active_users():
        db.add_user("מנהל מחסן")

    theme = db.get_setting("theme", "light")
    app.setStyleSheet(styles.get_theme(theme))

    wh_name = db.get_setting("warehouse_name", "XXX")
    login = LoginWindow(wh_name)
    if login.exec() != login.DialogCode.Accepted:
        sys.exit(0)

    splash = _make_splash(wh_name)
    splash.show()
    app.processEvents()          # paint splash before blocking on MainWindow init

    window = MainWindow(login.selected_user)
    screen = QApplication.primaryScreen().availableGeometry()
    w = min(1280, screen.width())
    h = min(800, screen.height())
    window.resize(w, h)
    window.move(
        screen.x() + (screen.width()  - w) // 2,
        screen.y() + (screen.height() - h) // 2,
    )
    window.show()
    splash.finish(window)        # close splash once main window is painted

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
