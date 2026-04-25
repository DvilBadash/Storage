import sys
import os
import traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

import database as db
import styles
import _icon
from login_window import LoginWindow
from main_window import MainWindow


def _show_crash(msg: str):
    """Show a dialog with the full traceback so users without a console can report it."""
    dlg = QMessageBox()
    dlg.setIcon(QMessageBox.Icon.Critical)
    dlg.setWindowTitle("שגיאת הפעלה")
    dlg.setText("אירעה שגיאה בהפעלת האפליקציה:")
    dlg.setDetailedText(msg)
    dlg.exec()


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    try:
        db.init_db()
    except Exception:
        _show_crash(traceback.format_exc())
        sys.exit(1)

    if not db.get_active_users():
        db.add_user("מנהל מחסן")

    app.setQuitOnLastWindowClosed(False)

    theme = db.get_setting("theme", "light")
    app.setStyleSheet(styles.get_theme(theme))
    app.setWindowIcon(_icon.app_icon())

    wh_name = db.get_setting("warehouse_name", "YYY")
    login = LoginWindow(wh_name)
    if login.exec() != login.DialogCode.Accepted:
        sys.exit(0)

    try:
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
    except Exception:
        _show_crash(traceback.format_exc())
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
