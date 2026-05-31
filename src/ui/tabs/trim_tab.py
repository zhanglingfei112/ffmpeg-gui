"""
视频裁剪 Tab
支持按开始时间/结束时间/时长裁剪视频。
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFileDialog, QLineEdit, QTimeEdit, QProgressBar,
    QFormLayout, QRadioButton,
)
from PySide6.QtCore import QTime

from src.core.ffmpeg_manager import trim_video, get_media_info


class TrimTab(QWidget):
    """视频裁剪"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._input_path = ""
        self._duration = 0.0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("✂️ 视频裁剪")
        title.setObjectName("title")
        layout.addWidget(title)

        desc = QLabel("截取视频片段，支持按开始/结束时间或时长裁剪")
        desc.setStyleSheet("color: #8888aa; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(desc)

        # === 输入文件 ===
        input_group = QGroupBox("输入文件")
        input_layout = QHBoxLayout(input_group)

        self._input_edit = QLineEdit()
        self._input_edit.setPlaceholderText("选择视频文件...")
        self._input_edit.setReadOnly(True)

        browse_btn = QPushButton("📂 浏览")
        browse_btn.clicked.connect(self._browse_input)

        input_layout.addWidget(self._input_edit)
        input_layout.addWidget(browse_btn)
        layout.addWidget(input_group)

        # === 裁剪设置 ===
        trim_group = QGroupBox("裁剪设置")
        trim_layout = QFormLayout(trim_group)
        trim_layout.setSpacing(10)

        # 显示总时长
        self._duration_label = QLabel("未选择文件")
        self._duration_label.setObjectName("info_value")
        trim_layout.addRow("视频时长:", self._duration_label)

        # 开始时间
        self._start_time = QTimeEdit()
        self._start_time.setDisplayFormat("HH:mm:ss.zzz")
        self._start_time.setTime(QTime(0, 0, 0))
        trim_layout.addRow("开始时间:", self._start_time)

        # 结束模式
        mode_group = QGroupBox()
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setContentsMargins(0, 0, 0, 0)

        self._end_time_radio = QRadioButton("指定结束时间")
        self._end_time_radio.setChecked(True)
        self._duration_radio = QRadioButton("指定时长")

        mode_layout.addWidget(self._end_time_radio)
        mode_layout.addWidget(self._duration_radio)

        trim_layout.addRow("裁剪方式:", mode_group)

        # 结束时间
        self._end_time = QTimeEdit()
        self._end_time.setDisplayFormat("HH:mm:ss.zzz")
        self._end_time.setTime(QTime(0, 1, 0))  # 默认1分钟
        trim_layout.addRow("结束时间:", self._end_time)

        # 时长
        self._duration_input = QTimeEdit()
        self._duration_input.setDisplayFormat("HH:mm:ss.zzz")
        self._duration_input.setTime(QTime(0, 0, 30))  # 默认30秒
        trim_layout.addRow("时长:", self._duration_input)

        layout.addWidget(trim_group)

        # === 输出 ===
        output_group = QGroupBox("输出")
        output_layout = QHBoxLayout(output_group)

        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("输出目录（默认同源目录）")
        output_browse = QPushButton("📂 选择")
        output_browse.clicked.connect(self._browse_output)
        output_layout.addWidget(self._output_edit)
        output_layout.addWidget(output_browse)
        layout.addWidget(output_group)

        # === 进度 ===
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # === 按钮 ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._start_btn = QPushButton("✂️ 开始裁剪")
        self._start_btn.setObjectName("btn_primary")
        self._start_btn.clicked.connect(self._start_trim)
        self._start_btn.setEnabled(False)
        btn_layout.addWidget(self._start_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

        self.setAcceptDrops(True)

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv);;所有文件 (*.*)"
        )
        if path:
            self._set_input(path)

    def _set_input(self, path):
        self._input_path = path
        self._input_edit.setText(path)
        try:
            info = get_media_info(path)
            self._duration = info.duration
            self._duration_label.setText(
                f"{info.duration_str}  ({info.file_size_str})"
            )
            # 默认结束时间为文件结束
            et = QTime(0, 0, 0)
            et = et.addSecs(int(info.duration))
            self._end_time.setTime(et)
            self._start_btn.setEnabled(True)
        except Exception as e:
            self._duration_label.setText(f"读取失败: {e}")
            self._start_btn.setEnabled(False)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self._output_edit.setText(path)

    def _start_trim(self):
        if not self._input_path:
            return

        self._start_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)

        # 构建路径
        stem = Path(self._input_path).stem
        output_dir = self._output_edit.text().strip() or str(Path(self._input_path).parent)
        output_path = str(Path(output_dir) / f"{stem}_trimmed.mp4")

        # 时间参数
        start = self._start_time.time().toString("HH:mm:ss.zzz")

        if self._end_time_radio.isChecked():
            end = self._end_time.time().toString("HH:mm:ss.zzz")
            duration = None
        else:
            duration = self._duration_input.time().toString("HH:mm:ss.zzz")
            end = None

        def progress_cb(pct):
            self._progress.setValue(int(pct))

        try:
            trim_video(
                self._input_path, output_path,
                start_time=start,
                end_time=end,
                duration=duration,
                progress_callback=progress_cb,
            )
            self._progress.setValue(100)
            self._update_status(f"✅ 裁剪完成: {Path(output_path).name}")
        except Exception as e:
            self._progress.setValue(0)
            self._update_status(f"❌ 裁剪失败: {e}")
        finally:
            self._start_btn.setEnabled(True)

    def _update_status(self, text):
        w = self.window()
        if hasattr(w, "update_status"):
            w.update_status(text)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith((".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv", ".wmv")):
                self._set_input(path)
                break
