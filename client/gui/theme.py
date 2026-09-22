"""
Aurora Dark Theme - QSS (Qt Style Sheet)
Mengadopsi estetika dari repo duhemen/gambut.
"""
from __future__ import annotations

# Palet warna
COLORS = {
    "bg_deep":     "#0A0E17",
    "bg_panel":    "#0F1523",
    "bg_card":     "#141B2D",
    "border":      "#1E2A44",
    "text":        "#E0E0E0",
    "text_muted":  "#8A94A6",
    "cyan":        "#00E5FF",
    "violet":      "#B388FF",
    "orange":      "#FF6E40",
    "green":       "#4ADE80",
    "yellow":      "#FACC15",
    "red":         "#EF4444",
}

# Warna per kategori UERI
CATEGORY_COLORS = {
    "AMAN":    COLORS["green"],
    "WASPADA": COLORS["yellow"],
    "SIAGA":   COLORS["orange"],
    "BAHAYA":  COLORS["red"],
}


def get_stylesheet() -> str:
    c = COLORS
    return f"""
    QWidget {{
        background-color: {c['bg_deep']};
        color: {c['text']};
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 13px;
    }}
    QMainWindow, QDialog {{
        background-color: {c['bg_deep']};
    }}
    QLabel#Title {{
        font-size: 22px;
        font-weight: 700;
        color: {c['cyan']};
        margin-bottom: 8px;
    }}
    QLabel#Subtitle {{
        font-size: 12px;
        color: {c['text_muted']};
        margin-bottom: 12px;
    }}

    /* ==================== BUTTONS ==================== */
    QPushButton {{
        background-color: {c['bg_card']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: 600;
        min-height: 32px;
        min-width: 90px;
        margin: 2px;
    }}
    QPushButton:hover {{
        background-color: {c['bg_panel']};
        border: 1px solid {c['cyan']};
        color: {c['cyan']};
    }}
    QPushButton:pressed {{
        background-color: {c['border']};
    }}
    QPushButton#Primary {{
        background-color: {c['cyan']};
        color: {c['bg_deep']};
        border: none;
        min-height: 34px;
        padding: 8px 22px;
    }}
    QPushButton#Primary:hover {{
        background-color: #33EBFF;
    }}

    /* ==================== INPUTS ==================== */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {c['bg_panel']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 10px;
        color: {c['text']};
        min-height: 28px;
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {c['cyan']};
    }}
    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {c['cyan']};
        margin-right: 6px;
    }}
    QTextEdit {{
        background-color: {c['bg_panel']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 8px;
        color: {c['text']};
    }}
    QTextEdit:focus {{
        border: 1px solid {c['cyan']};
    }}

    /* ==================== GROUPBOX ==================== */
    QGroupBox {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        margin-top: 16px;
        padding: 18px 14px 14px 14px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 14px;
        padding: 0 8px;
        color: {c['cyan']};
        background-color: {c['bg_card']};
    }}

    /* ==================== TABS ==================== */
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        border-radius: 8px;
        background-color: {c['bg_panel']};
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: {c['bg_deep']};
        color: {c['text_muted']};
        padding: 10px 22px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        margin-right: 3px;
        min-width: 80px;
    }}
    QTabBar::tab:hover {{
        color: {c['cyan']};
    }}
    QTabBar::tab:selected {{
        background-color: {c['bg_panel']};
        color: {c['cyan']};
        border-bottom: 2px solid {c['cyan']};
    }}

    /* ==================== LISTS ==================== */
    QListWidget {{
        padding: 6px;
        background-color: {c['bg_panel']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 8px 12px;
        margin: 3px 0;
        border-radius: 5px;
        border: 1px solid transparent;
    }}
    QListWidget::item:hover {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border']};
    }}
    QListWidget::item:selected {{
        background-color: {c['bg_card']};
        color: {c['cyan']};
        border: 1px solid {c['cyan']};
    }}

    /* ==================== SCROLLBAR ==================== */
    QScrollBar:vertical {{
        background: {c['bg_deep']};
        width: 10px;
        border-radius: 5px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c['border']};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c['cyan']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* ==================== STATUS BAR ==================== */
    QStatusBar {{
        background-color: {c['bg_panel']};
        color: {c['text_muted']};
        border-top: 1px solid {c['border']};
        padding: 4px 12px;
    }}

    /* ==================== TABLE ==================== */
    QTableWidget {{
        background-color: {c['bg_panel']};
        gridline-color: {c['border']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 4px;
    }}
    QTableWidget::item {{
        padding: 6px 10px;
    }}
    QTableWidget::item:selected {{
        background-color: {c['bg_card']};
        color: {c['cyan']};
    }}
    QHeaderView::section {{
        background-color: {c['bg_card']};
        color: {c['cyan']};
        padding: 8px 10px;
        border: none;
        border-bottom: 1px solid {c['border']};
        font-weight: 600;
    }}

    /* ==================== FORM LAYOUT ==================== */
    QFormLayout {{
        spacing: 10px;
    }}
    QFormLayout QLabel {{
        color: {c['text_muted']};
        min-width: 90px;
    }}
    """