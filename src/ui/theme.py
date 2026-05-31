"""
深色主题模块
提供统一的暗色主题 QSS 样式表。
"""

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication


# 深色主题 QSS
DARK_STYLE = """
/* === 全局 === */
QWidget {
    background-color: #1a1b2e;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Noto Sans CJK SC", "WenQuanYi Micro Hei",
                 "PingFang SC", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* === 主窗口 === */
QMainWindow {
    background-color: #1a1b2e;
}

/* === 侧边导航栏 === */
QFrame#sidebar {
    background-color: #14152a;
    border-right: 1px solid #2a2b4a;
    min-width: 180px;
    max-width: 180px;
}

QPushButton#nav_btn {
    background-color: transparent;
    color: #8888aa;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#nav_btn:hover {
    background-color: #1f2140;
    color: #c0c0e0;
}

QPushButton#nav_btn:checked {
    background-color: #2a3a6a;
    color: #6aa0ff;
    border-left: 3px solid #6aa0ff;
}

/* === 内容区 === */
QFrame#content_area {
    background-color: #1a1b2e;
}

/* === 标签页组件 === */
QTabWidget::pane {
    background-color: #1a1b2e;
    border: none;
}

QTabBar::tab {
    background-color: #14152a;
    color: #8888aa;
    padding: 8px 20px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: #6aa0ff;
    border-bottom: 2px solid #6aa0ff;
}

QTabBar::tab:hover {
    color: #c0c0e0;
}

/* === 分组框 === */
QGroupBox {
    background-color: #1e2040;
    border: 1px solid #2a2b4a;
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px 12px 12px 12px;
    font-weight: 500;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #6aa0ff;
}

/* === 按钮 === */
QPushButton {
    background-color: #2a3a6a;
    color: #e0e0e0;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3a4a8a;
}

QPushButton:pressed {
    background-color: #1a2a5a;
}

QPushButton:disabled {
    background-color: #2a2a3a;
    color: #666688;
}

QPushButton#btn_primary {
    background-color: #3a6ad0;
    color: white;
    font-size: 14px;
    font-weight: 600;
    padding: 10px 28px;
}

QPushButton#btn_primary:hover {
    background-color: #4a7ae0;
}

QPushButton#btn_danger {
    background-color: #8a2a3a;
    color: white;
}

QPushButton#btn_danger:hover {
    background-color: #aa3a4a;
}

/* === 下拉框 === */
QComboBox {
    background-color: #1e2040;
    color: #e0e0e0;
    border: 1px solid #2a2b4a;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #3a5a9a;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1e2040;
    color: #e0e0e0;
    border: 1px solid #2a2b4a;
    selection-background-color: #2a3a6a;
}

/* === 输入框 === */
QLineEdit, QSpinBox, QDoubleSpinBox, QTimeEdit {
    background-color: #1e2040;
    color: #e0e0e0;
    border: 1px solid #2a2b4a;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 20px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {
    border-color: #3a5a9a;
}

/* === 标签 === */
QLabel {
    color: #c0c0d0;
    background-color: transparent;
}

QLabel#title {
    font-size: 18px;
    font-weight: 600;
    color: #e0e0f0;
}

QLabel#section_title {
    font-size: 14px;
    font-weight: 600;
    color: #6aa0ff;
    padding: 4px 0;
}

QLabel#info_value {
    color: #e0e0e0;
    font-weight: 500;
}

QLabel#info_label {
    color: #8888aa;
}

QLabel#drop_hint {
    color: #55557a;
    font-size: 16px;
    border: 2px dashed #2a2b4a;
    border-radius: 12px;
    padding: 40px;
}

/* === 进度条 === */
QProgressBar {
    background-color: #1e2040;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #e0e0e0;
    font-size: 11px;
    min-height: 16px;
}

QProgressBar::chunk {
    background-color: #3a6ad0;
    border-radius: 4px;
}

/* === 表格 === */
QTableWidget {
    background-color: #1e2040;
    border: 1px solid #2a2b4a;
    border-radius: 6px;
    gridline-color: #2a2b4a;
}

QTableWidget::item {
    padding: 6px 10px;
    color: #c0c0d0;
}

QTableWidget::item:selected {
    background-color: #2a3a6a;
    color: #e0e0ff;
}

QHeaderView::section {
    background-color: #14152a;
    color: #8888aa;
    border: none;
    border-bottom: 1px solid #2a2b4a;
    padding: 8px 10px;
    font-weight: 500;
}

/* === 列表 === */
QListWidget {
    background-color: #1e2040;
    border: 1px solid #2a2b4a;
    border-radius: 6px;
}

QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #25254a;
}

QListWidget::item:selected {
    background-color: #2a3a6a;
}

/* === 滚动条 === */
QScrollBar:vertical {
    background-color: #1a1b2e;
    width: 8px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #3a3a5a;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4a4a6a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #1a1b2e;
    height: 8px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #3a3a5a;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* === 文件拖放区域 === */
QFrame#drop_zone {
    background-color: #1e2040;
    border: 2px dashed #2a2b4a;
    border-radius: 12px;
}

QFrame#drop_zone:hover {
    border-color: #3a5a9a;
    background-color: #222552;
}

/* === 任务状态标签 === */
QLabel#status_waiting { color: #8888aa; }
QLabel#status_running { color: #6aa0ff; }
QLabel#status_completed { color: #4aca6a; }
QLabel#status_failed { color: #da4a4a; }
QLabel#status_cancelled { color: #aa8a3a; }

/* === 滚动区域 === */
QScrollArea {
    border: none;
    background-color: transparent;
}

/* === 复选框 / 单选框 === */
QCheckBox {
    spacing: 8px;
    color: #c0c0d0;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #2a2b4a;
    border-radius: 3px;
    background-color: #1e2040;
}

QCheckBox::indicator:checked {
    background-color: #3a6ad0;
    border-color: #3a6ad0;
}

QRadioButton {
    spacing: 8px;
    color: #c0c0d0;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #2a2b4a;
    border-radius: 8px;
    background-color: #1e2040;
}

QRadioButton::indicator:checked {
    background-color: #3a6ad0;
    border-color: #3a6ad0;
}
"""


def apply_dark_theme(app: QApplication):
    """应用深色主题到应用"""
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLE)

    # 设置调色板
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(26, 27, 46))
    palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
    palette.setColor(QPalette.Base, QColor(30, 32, 64))
    palette.setColor(QPalette.AlternateBase, QColor(26, 27, 46))
    palette.setColor(QPalette.ToolTipBase, QColor(30, 32, 64))
    palette.setColor(QPalette.ToolTipText, QColor(224, 224, 224))
    palette.setColor(QPalette.Text, QColor(224, 224, 224))
    palette.setColor(QPalette.Button, QColor(42, 58, 106))
    palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
    palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.Link, QColor(106, 160, 255))
    palette.setColor(QPalette.Highlight, QColor(42, 58, 106))
    palette.setColor(QPalette.HighlightedText, QColor(224, 224, 255))
    app.setPalette(palette)
