
LIGHT = """
QMainWindow, QDialog, QWidget {
    background-color: #F0F2F5;
    font-family: 'Segoe UI', Arial;
    font-size: 13px;
    color: #212121;
}
QLabel { color: #212121; background-color: transparent; }
QLabel#title_label {
    font-size: 20px; font-weight: bold; color: #1565C0;
}
QLabel#step_num {
    font-size: 22px; font-weight: bold; color: white;
    background-color: #1976D2; border-radius: 20px;
    min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px;
    qproperty-alignment: AlignCenter;
}
QLabel#card_title { font-size: 17px; font-weight: bold; color: #1565C0; }
QLabel#card_sub   { font-size: 13px; color: #616161; }
QLabel#header_title { font-size: 17px; font-weight: bold; color: white; }
QLabel#status_label { font-size: 11px; color: #616161; background-color: transparent; }
QLabel#section_title { font-size: 15px; font-weight: bold; color: #1565C0; }
QLabel#warn_label { color: #C62828; font-weight: bold; background-color: transparent; }

QFrame#header_bar {
    background-color: #1976D2;
    border-bottom: 2px solid #1565C0;
}
QFrame#card {
    background-color: white;
    border-radius: 12px;
    border: 1px solid #E0E0E0;
}
QFrame#card:hover { border: 1.5px solid #1976D2; }
QFrame#status_bar {
    background-color: #EEEEEE;
    border-top: 1px solid #BDBDBD;
}
QFrame#separator { background-color: #E0E0E0; max-height: 1px; }

QPushButton {
    background-color: #1976D2; color: white;
    border: none; border-radius: 8px;
    padding: 11px 22px; font-size: 14px; font-weight: bold;
    min-height: 44px;
}
QPushButton:hover   { background-color: #1565C0; }
QPushButton:pressed { background-color: #0D47A1; }
QPushButton:disabled { background-color: #BDBDBD; color: #757575; }
QPushButton#btn_secondary {
    background-color: white; color: #1976D2;
    border: 2px solid #1976D2;
}
QPushButton#btn_secondary:hover { background-color: #E3F2FD; }
QPushButton#btn_danger {
    background-color: #D32F2F;
}
QPushButton#btn_danger:hover { background-color: #B71C1C; }
QPushButton#btn_icon {
    background-color: transparent; color: #1976D2;
    border: none; padding: 6px; min-height: 32px; min-width: 32px;
    font-size: 18px;
}
QPushButton#btn_menu {
    background-color: transparent; color: white;
    border: 1px solid rgba(255,255,255,0.4); border-radius: 6px;
    padding: 8px 14px; font-size: 13px; min-height: 36px;
}
QPushButton#btn_menu:hover { background-color: rgba(255,255,255,0.15); }

QLineEdit {
    border: 2px solid #BDBDBD; border-radius: 8px;
    padding: 10px 14px; font-size: 13px;
    background-color: white; min-height: 44px;
}
QLineEdit:focus { border-color: #1976D2; }

QComboBox {
    border: 2px solid #BDBDBD; border-radius: 8px;
    padding: 10px 14px; font-size: 13px;
    background-color: white; min-height: 44px;
}
QComboBox:focus { border-color: #1976D2; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow { image: none; border-left: 5px solid transparent;
    border-right: 5px solid transparent; border-top: 6px solid #757575;
    margin-right: 8px; }
QComboBox QAbstractItemView {
    background: white; border: 1px solid #E0E0E0;
    selection-background-color: #BBDEFB; color: #212121;
    font-size: 13px;
}

QTableWidget {
    border: 1px solid #E0E0E0; border-radius: 8px;
    background-color: white; gridline-color: #F0F0F0;
    font-size: 12px; alternate-background-color: #FAFAFA;
}
QTableWidget::item { padding: 6px 8px; min-height: 44px; color: #212121; }
QTableWidget::item:selected { background-color: #BBDEFB; color: #1565C0; }
QHeaderView::section {
    background-color: #1976D2; color: white;
    padding: 10px 8px; font-weight: bold; font-size: 12px;
    border: none; border-right: 1px solid #1565C0;
}
QHeaderView::section:last { border-right: none; }

QScrollBar:vertical { width: 14px; background: #F5F5F5; border-radius: 7px; }
QScrollBar::handle:vertical { background: #BDBDBD; border-radius: 7px; min-height: 36px; }
QScrollBar::handle:vertical:hover { background: #9E9E9E; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { height: 14px; background: #F5F5F5; }
QScrollBar::handle:horizontal { background: #BDBDBD; border-radius: 7px; min-width: 36px; }

QTabWidget::pane { border: 1px solid #E0E0E0; background: white; border-radius: 8px; }
QTabBar::tab {
    background: #F5F5F5; color: #616161; border: 1px solid #E0E0E0;
    padding: 10px 20px; font-size: 13px; min-width: 100px;
    border-top-left-radius: 6px; border-top-right-radius: 6px;
}
QTabBar::tab:selected { background: white; color: #1565C0; font-weight: bold; border-bottom: none; }
QTabBar::tab:hover { background: #E3F2FD; }

QCheckBox { spacing: 10px; font-size: 13px; }
QCheckBox::indicator { width: 22px; height: 22px; border: 2px solid #BDBDBD; border-radius: 4px; background: white; }
QCheckBox::indicator:checked { background-color: #1976D2; border-color: #1976D2; }


QMessageBox { background-color: white; }
QMessageBox QLabel { color: #212121; font-size: 14px; }

QGroupBox {
    border: 1px solid #E0E0E0; border-radius: 8px;
    margin-top: 16px; font-weight: bold; color: #1565C0; font-size: 13px;
    background-color: white;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }

QTextEdit {
    border: 1px solid #E0E0E0; border-radius: 8px;
    background: white; font-size: 12px; color: #212121;
}

QSpinBox {
    border: 2px solid #BDBDBD; border-radius: 8px;
    padding: 8px 12px; font-size: 13px; background: white; min-height: 44px;
}
QSpinBox:focus { border-color: #1976D2; }
"""

DARK = """
QMainWindow, QDialog, QWidget {
    background-color: #1A1A2E;
    font-family: 'Segoe UI', Arial;
    font-size: 13px;
    color: #E0E0E0;
}
QLabel { color: #E0E0E0; background-color: transparent; }
QLabel#title_label { font-size: 20px; font-weight: bold; color: #90CAF9; }
QLabel#step_num {
    font-size: 22px; font-weight: bold; color: white;
    background-color: #1565C0; border-radius: 20px;
    min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px;
    qproperty-alignment: AlignCenter;
}
QLabel#card_title { font-size: 17px; font-weight: bold; color: #90CAF9; }
QLabel#card_sub   { font-size: 13px; color: #9E9E9E; }
QLabel#header_title { font-size: 17px; font-weight: bold; color: white; }
QLabel#status_label { font-size: 11px; color: #9E9E9E; background-color: transparent; }
QLabel#section_title { font-size: 15px; font-weight: bold; color: #90CAF9; }
QLabel#warn_label { color: #EF9A9A; font-weight: bold; background-color: transparent; }

QFrame#header_bar { background-color: #0D47A1; border-bottom: 2px solid #1565C0; }
QFrame#card { background-color: #16213E; border-radius: 12px; border: 1px solid #2D3748; }
QFrame#card:hover { border: 1.5px solid #1976D2; }
QFrame#status_bar { background-color: #12172B; border-top: 1px solid #2D3748; }
QFrame#separator { background-color: #2D3748; max-height: 1px; }

QPushButton {
    background-color: #1565C0; color: white;
    border: none; border-radius: 8px;
    padding: 11px 22px; font-size: 14px; font-weight: bold; min-height: 44px;
}
QPushButton:hover   { background-color: #1976D2; }
QPushButton:pressed { background-color: #0D47A1; }
QPushButton:disabled { background-color: #37474F; color: #78909C; }
QPushButton#btn_secondary {
    background-color: #16213E; color: #90CAF9; border: 2px solid #1565C0;
}
QPushButton#btn_secondary:hover { background-color: #1A2744; }
QPushButton#btn_danger { background-color: #C62828; }
QPushButton#btn_danger:hover { background-color: #B71C1C; }
QPushButton#btn_icon {
    background-color: transparent; color: #90CAF9;
    border: none; padding: 6px; min-height: 32px; min-width: 32px; font-size: 18px;
}
QPushButton#btn_menu {
    background-color: transparent; color: white;
    border: 1px solid rgba(255,255,255,0.3); border-radius: 6px;
    padding: 8px 14px; font-size: 13px; min-height: 36px;
}
QPushButton#btn_menu:hover { background-color: rgba(255,255,255,0.1); }

QLineEdit {
    border: 2px solid #2D3748; border-radius: 8px;
    padding: 10px 14px; font-size: 13px;
    background-color: #16213E; color: #E0E0E0; min-height: 44px;
}
QLineEdit:focus { border-color: #1976D2; }

QComboBox {
    border: 2px solid #2D3748; border-radius: 8px;
    padding: 10px 14px; font-size: 13px;
    background-color: #16213E; color: #E0E0E0; min-height: 44px;
}
QComboBox:focus { border-color: #1976D2; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow { border-left: 5px solid transparent;
    border-right: 5px solid transparent; border-top: 6px solid #90CAF9; margin-right: 8px; }
QComboBox QAbstractItemView {
    background: #16213E; border: 1px solid #2D3748;
    selection-background-color: #1565C0; color: #E0E0E0; font-size: 13px;
}

QTableWidget {
    border: 1px solid #2D3748; border-radius: 8px;
    background-color: #16213E; gridline-color: #2D3748;
    color: #E0E0E0; font-size: 12px; alternate-background-color: #1A2744;
}
QTableWidget::item { padding: 6px 8px; min-height: 44px; color: #E0E0E0; }
QTableWidget::item:selected { background-color: #1565C0; color: white; }
QHeaderView::section {
    background-color: #0D47A1; color: white;
    padding: 10px 8px; font-weight: bold; font-size: 12px;
    border: none; border-right: 1px solid #1565C0;
}

QScrollBar:vertical { width: 14px; background: #12172B; border-radius: 7px; }
QScrollBar::handle:vertical { background: #37474F; border-radius: 7px; min-height: 36px; }
QScrollBar::handle:vertical:hover { background: #546E7A; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { height: 14px; background: #12172B; }
QScrollBar::handle:horizontal { background: #37474F; border-radius: 7px; min-width: 36px; }

QTabWidget::pane { border: 1px solid #2D3748; background: #16213E; border-radius: 8px; }
QTabBar::tab {
    background: #12172B; color: #9E9E9E; border: 1px solid #2D3748;
    padding: 10px 20px; font-size: 13px; min-width: 100px;
    border-top-left-radius: 6px; border-top-right-radius: 6px;
}
QTabBar::tab:selected { background: #16213E; color: #90CAF9; font-weight: bold; border-bottom: none; }
QTabBar::tab:hover { background: #1A2744; }

QCheckBox { spacing: 10px; font-size: 13px; color: #E0E0E0; }
QCheckBox::indicator { width: 22px; height: 22px; border: 2px solid #37474F; border-radius: 4px; background: #16213E; }
QCheckBox::indicator:checked { background-color: #1565C0; border-color: #1976D2; }

QMessageBox { background-color: #16213E; }
QMessageBox QLabel { color: #E0E0E0; font-size: 14px; }

QGroupBox {
    border: 1px solid #2D3748; border-radius: 8px;
    margin-top: 16px; font-weight: bold; color: #90CAF9; font-size: 13px;
    background-color: #16213E;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }

QTextEdit {
    border: 1px solid #2D3748; border-radius: 8px;
    background: #16213E; font-size: 12px; color: #E0E0E0;
}

QSpinBox {
    border: 2px solid #2D3748; border-radius: 8px;
    padding: 8px 12px; font-size: 13px; background: #16213E; color: #E0E0E0; min-height: 44px;
}
QSpinBox:focus { border-color: #1976D2; }
"""


def get_theme(name: str) -> str:
    return DARK if name == "dark" else LIGHT
