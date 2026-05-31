"""
应用配置和启动模块
"""

import sys
import os

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QApplication

from src.ui.theme import apply_dark_theme
from src.ui.main_window import MainWindow
from src.core.ffmpeg_manager import check_ffmpeg_installed
from src.core.language import LanguageManager
from src.ui.install_dialog import check_and_install_ffmpeg


_APP_NAME = "FFmpeg GUI"
_ORG_NAME = "LFZ"
_APP_VERSION = "0.2.0"


class App(QApplication):
    """应用程序"""

    def __init__(self, argv=None):
        if argv is None:
            argv = sys.argv
        super().__init__(argv)

        self.setApplicationName(_APP_NAME)
        self.setOrganizationName(_ORG_NAME)
        self.setApplicationVersion(_APP_VERSION)

        # 应用深色主题
        apply_dark_theme(self)

        # 初始化语言（从设置读取）
        settings = QSettings()
        lang = settings.value("language", "zh_cn")
        LanguageManager.instance().set_language(lang)

        # 检查 FFmpeg — 如果未安装弹出安装对话框
        ffmpeg_ok, ffmpeg_ver = check_ffmpeg_installed()
        if not ffmpeg_ok:
            # 先创建窗口（用于作为父窗口），但隐藏
            from PySide6.QtWidgets import QWidget
            temp_parent = QWidget()
            ffmpeg_ok = check_and_install_ffmpeg(temp_parent)
            temp_parent.deleteLater()
            # 重新检查
            if ffmpeg_ok:
                ffmpeg_ok, ffmpeg_ver = check_ffmpeg_installed()

        # 创建主窗口
        self._window = MainWindow(
            ffmpeg_available=ffmpeg_ok,
            ffmpeg_version=ffmpeg_ver if ffmpeg_ok else "",
        )
        self._window.show()

    def window(self):
        return self._window


def run():
    """启动应用"""
    # 高 DPI 支持
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = App(sys.argv)
    sys.exit(app.exec())
