"""
FFmpeg 安装检测对话框
启动时检测 FFmpeg，未安装时弹出安装引导对话框。
"""

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QMessageBox,
)

from src.core import language
from src.core.ffmpeg_downloader import auto_install_ffmpeg, get_install_instructions
from src.core.ffmpeg_manager import check_ffmpeg_installed
from src.core.language import _ as _tr


class InstallWorker(QThread):
    """后台安装线程"""
    progress = Signal(int)
    log = Signal(str)
    finished_signal = Signal(bool, str, str)  # success, ffmpeg_path, ffprobe_path

    def run(self):
        success, ff_path, fp_path = auto_install_ffmpeg(
            progress_callback=self.progress.emit,
            log_callback=self.log.emit,
        )
        self.finished_signal.emit(success, ff_path, fp_path)


class FfmpegInstallDialog(QDialog):
    """FFmpeg 安装对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result_paths = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(_tr("install_title"))
        self.setMinimumWidth(480)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        # 标题
        title = QLabel(f"⚠️ {_tr('install_title')}")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #da4a4a;")
        layout.addWidget(title)

        # 提示文字
        self._msg = QLabel(_tr("install_msg"))
        self._msg.setWordWrap(True)
        self._msg.setStyleSheet("color: #c0c0d0; font-size: 13px; line-height: 1.6;")
        layout.addWidget(self._msg)

        # 日志区域（隐藏）
        self._log_area = QTextEdit()
        self._log_area.setReadOnly(True)
        self._log_area.setMaximumHeight(100)
        self._log_area.setVisible(False)
        self._log_area.setStyleSheet("""
            QTextEdit {
                background-color: #14152a;
                color: #88cc88;
                font-family: monospace;
                font-size: 11px;
                border: 1px solid #2a2b4a;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self._log_area)

        # 进度条（隐藏）
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._auto_btn = QPushButton(f"⬇️ {_tr('install_btn_auto')}")
        self._auto_btn.setObjectName("btn_primary")
        self._auto_btn.clicked.connect(self._start_install)
        self._auto_btn.setCursor(Qt.PointingHandCursor)

        self._cancel_btn = QPushButton(_tr("install_btn_cancel"))
        self._cancel_btn.clicked.connect(self._show_manual_guide)
        self._cancel_btn.setCursor(Qt.PointingHandCursor)

        btn_layout.addWidget(self._auto_btn)
        btn_layout.addWidget(self._cancel_btn)
        layout.addLayout(btn_layout)

        self._worker = None

    def _start_install(self):
        from src.core.ffmpeg_downloader import IS_WINDOWS

        if not IS_WINDOWS:
            self._show_linux_hint()
            return

        self._auto_btn.setEnabled(False)
        self._cancel_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._log_area.setVisible(True)
        self._msg.setText(_tr("install_downloading"))

        self._worker = InstallWorker()
        self._worker.progress.connect(self._progress.setValue)
        self._worker.log.connect(self._log_area.append)
        self._worker.finished_signal.connect(self._on_install_finished)
        self._worker.start()

    def _on_install_finished(self, success, ff_path, fp_path):
        if success:
            self._msg.setText(f"✅ {_tr('install_done')}")
            self._progress.setValue(100)
            self._result_paths = (ff_path, fp_path)
            # 关闭对话框
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1500, self.accept)
        else:
            self._msg.setText(f"❌ {_tr('install_fail')}")
            self._auto_btn.setEnabled(True)
            self._cancel_btn.setEnabled(True)
            self._cancel_btn.setText(_tr("common_close"))
            # 添加手动安装提示
            self._log_area.append(f"\n---\n{_tr('install_manual_hint')}")

    def _show_manual_guide(self):
        """显示手动安装指引"""
        from src.core.ffmpeg_downloader import IS_WINDOWS, IS_LINUX, IS_MACOS

        if IS_WINDOWS:
            guide = _tr("install_manual_hint")
        elif IS_LINUX:
            guide = _tr("install_linux_hint")
        elif IS_MACOS:
            guide = _tr("install_os_not_supported")
        else:
            guide = _tr("install_os_not_supported")

        QMessageBox.information(self, _tr("install_title"), guide)
        self.reject()

    def _show_linux_hint(self):
        """Linux 提示"""
        guide = _tr("install_linux_hint")
        QMessageBox.information(self, _tr("install_title"), guide)
        self.reject()

    def get_result(self) -> tuple:
        """获取安装结果 (ffmpeg_path, ffprobe_path) 或 None"""
        return self._result_paths


def check_and_install_ffmpeg(parent=None) -> bool:
    """
    检测 FFmpeg 是否可用。不可用时弹出安装对话框。
    返回 True 表示 FFmpeg 可用（已安装或用户取消后自备）。
    """
    ok, ver = check_ffmpeg_installed()
    if ok:
        return True

    dialog = FfmpegInstallDialog(parent)
    result = dialog.exec()

    if result == QDialog.Accepted and dialog.get_result():
        # 安装成功，更新全局路径
        ff_path, fp_path = dialog.get_result()
        from src.core.ffmpeg_manager import FFMPEG_PATH, FFPROBE_PATH
        # 设置模块级变量
        import src.core.ffmpeg_manager as fm
        fm.FFMPEG_PATH = ff_path
        fm.FFPROBE_PATH = fp_path
        return True

    # 用户取消，仍然返回 True（让用户手动安装）
    return True
