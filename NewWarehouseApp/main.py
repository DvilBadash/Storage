import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import database as db
import styles
from login_window import LoginWindow
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setFont(QFont("Segoe UI", 12))

    db.init_db()

    if not db.get_active_users():
        db.add_user("מנהל מחסן")

    theme = db.get_setting("theme", "light")
    app.setStyleSheet(styles.get_theme(theme))

    wh_name = db.get_setting("warehouse_name", "YYY")
    login = LoginWindow(wh_name)
    if login.exec() != login.DialogCode.Accepted:
        sys.exit(0)

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
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
