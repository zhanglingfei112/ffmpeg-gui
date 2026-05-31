"""
主窗口模块
左侧导航栏 + 右侧 StackedWidget 内容区 + 底部状态栏
支持语言切换。
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QWidget, QFrame, QPushButton,
    QStackedWidget, QLabel, QApplication, QMainWindow, QSizePolicy,
)

from src.ui.tabs.convert_tab import ConvertTab
from src.ui.tabs.trim_tab import TrimTab
from src.ui.tabs.merge_tab import MergeTab
from src.ui.tabs.extract_tab import ExtractTab
from src.ui.tabs.info_tab import InfoTab
from src.ui.tabs.batch_tab import BatchTab
from src.ui.tabs.settings_tab import SettingsTab
from src.core.language import LanguageManager, _


NAV_KEYS = [
    "nav_convert", "nav_trim", "nav_merge", "nav_extract",
    "nav_info", "nav_batch", "nav_settings",
]

NAV_ICONS = ["🔄", "✂️", "📎", "🎵", "ℹ️", "📋", "⚙️"]

TAB_CLASSES = [
    ConvertTab, TrimTab, MergeTab, ExtractTab,
    InfoTab, BatchTab, SettingsTab,
]


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self, ffmpeg_available=True, ffmpeg_version="", parent=None):
        super().__init__(parent)
        self._tabs = []
        self._nav_buttons = []
        self._ffmpeg_available = ffmpeg_available
        self._ffmpeg_version = ffmpeg_version
        self._ffmpeg_status_label = None

        self.setMinimumSize(960, 640)
        self.resize(1100, 720)

        self._setup_ui(ffmpeg_available, ffmpeg_version)
        self._update_window_title()

        # 监听语言切换（不重建 UI，只更新文本）
        LanguageManager.instance().add_listener(self._on_language_changed)

    def _update_window_title(self):
        self.setWindowTitle(f"🎬 {_('app_name')} — {_('app_desc')}")

    def _on_language_changed(self, lang):
        """语言切换时更新导航和状态（不重建UI）"""
        self._update_window_title()
        self._update_nav_buttons()
        self._update_status_label()
        # 通知各 tab 更新文本
        for tab in self._tabs:
            if hasattr(tab, "on_language_changed"):
                tab.on_language_changed()
            elif hasattr(tab, "retranslate_ui"):
                tab.retranslate_ui()

    def _update_nav_buttons(self):
        for i, btn in enumerate(self._nav_buttons):
            if i < len(NAV_KEYS):
                icon = NAV_ICONS[i]
                text = _(NAV_KEYS[i])
                btn.setText(f"  {icon}  {text}")

    def _update_status_label(self):
        if self._ffmpeg_available:
            self._ffmpeg_status_label.setText(f"✅ {_('status_ffmpeg_ok')}")
        else:
            self._ffmpeg_status_label.setText(f"❌ {_('status_no_ffmpeg')}")

    def _setup_ui(self, ffmpeg_available, ffmpeg_version):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 左侧导航栏 ===
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(180)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 16, 8, 16)
        sidebar_layout.setSpacing(4)

        # Logo / 标题
        logo = QLabel("🎬 FFmpeg GUI")
        logo.setObjectName("title")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("padding: 8px 0 16px 0;")
        sidebar_layout.addWidget(logo)

        # 导航按钮组
        for i, key in enumerate(NAV_KEYS):
            icon = NAV_ICONS[i]
            btn = QPushButton(f"  {icon}  {_(key)}")
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # FFmpeg 状态
        self._ffmpeg_status_label = QLabel()
        if ffmpeg_available:
            self._ffmpeg_status_label.setText(f"✅ {_('status_ffmpeg_ok')}")
            self._ffmpeg_status_label.setStyleSheet("color: #4aca6a; font-size: 11px; padding: 4px;")
        else:
            self._ffmpeg_status_label.setText(f"❌ {_('status_no_ffmpeg')}")
            self._ffmpeg_status_label.setStyleSheet("color: #da4a4a; font-size: 11px; padding: 4px;")
        self._ffmpeg_status_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self._ffmpeg_status_label)

        if ffmpeg_version:
            ver_label = QLabel(ffmpeg_version[:40])
            ver_label.setStyleSheet("color: #55557a; font-size: 10px; padding: 2px 4px;")
            ver_label.setAlignment(Qt.AlignCenter)
            sidebar_layout.addWidget(ver_label)

        main_layout.addWidget(sidebar)

        # === 右侧内容区 ===
        content_frame = QFrame()
        content_frame.setObjectName("content_area")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._stack = QStackedWidget()
        for TabClass in TAB_CLASSES:
            tab = TabClass()
            self._tabs.append(tab)
            self._stack.addWidget(tab)

        content_layout.addWidget(self._stack)

        # === 底部全局状态栏 ===
        self._status_bar = QFrame()
        self._status_bar.setObjectName("status_bar")
        self._status_bar.setFixedHeight(28)
        self._status_bar.setStyleSheet("""
            QFrame#status_bar {
                background-color: #14152a;
                border-top: 1px solid #2a2b4a;
            }
            QLabel {
                color: #666688;
                font-size: 11px;
                padding: 0 12px;
            }
        """)
        bar_layout = QHBoxLayout(self._status_bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        self._status_label = QLabel(f"  {_('status_ready')}")
        bar_layout.addWidget(self._status_label)
        bar_layout.addStretch()

        content_layout.addWidget(self._status_bar)

        main_layout.addWidget(content_frame)

        # 默认选中第一个 tab
        self._nav_buttons[0].setChecked(True)
        self._stack.setCurrentIndex(0)

    def _switch_tab(self, idx: int):
        """切换标签页"""
        if 0 <= idx < len(self._nav_buttons):
            for i, btn in enumerate(self._nav_buttons):
                btn.setChecked(i == idx)
            if 0 <= idx < self._stack.count():
                self._stack.setCurrentIndex(idx)

    def update_status(self, text: str):
        """更新底部状态栏"""
        self._status_label.setText(f" {text}")
