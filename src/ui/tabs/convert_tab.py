"""
格式转换 & 压缩 Tab
支持格式转换、质量/压缩预设、分辨率调整。
"""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QFileDialog, QLineEdit, QCheckBox,
    QProgressBar, QFormLayout, QFrame, QScrollArea,
)

from src.core.ffmpeg_manager import convert_file, change_resolution, compress_video, get_media_info
from src.core.presets import FORMAT_PRESETS, QUALITY_PRESETS, DEVICE_PRESETS


class ConvertTab(QWidget):
    """格式转换、压缩、分辨率调整"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._input_path = ""
        self._current_task_id = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel("🔄 格式转换 & 压缩")
        title.setObjectName("title")
        layout.addWidget(title)

        desc = QLabel("将视频转换为其他格式、调整画质或分辨率")
        desc.setStyleSheet("color: #8888aa; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(desc)

        # === 输入文件 ===
        input_group = QGroupBox("输入文件")
        input_layout = QHBoxLayout(input_group)

        self._input_path_edit = QLineEdit()
        self._input_path_edit.setPlaceholderText("选择或拖拽视频文件到此处...")
        self._input_path_edit.setReadOnly(True)

        browse_btn = QPushButton("📂 浏览")
        browse_btn.clicked.connect(self._browse_input)

        input_layout.addWidget(self._input_path_edit)
        input_layout.addWidget(browse_btn)
        layout.addWidget(input_group)

        # === 输出格式 ===
        format_group = QGroupBox("输出格式 & 质量")
        format_layout = QFormLayout(format_group)
        format_layout.setSpacing(10)

        # 格式选择
        self._format_combo = QComboBox()
        for p in FORMAT_PRESETS:
            self._format_combo.addItem(f"{p.name} — {p.description}", p.name)
        format_layout.addRow("输出格式:", self._format_combo)

        # 质量预设
        self._quality_combo = QComboBox()
        for p in QUALITY_PRESETS:
            self._quality_combo.addItem(f"{p.name} — {p.description}", p.name)
        self._quality_combo.setCurrentIndex(2)  # 默认"平衡"
        format_layout.addRow("压缩质量:", self._quality_combo)

        # CRF 微调
        crf_row = QHBoxLayout()
        self._crf_label = QLabel("CRF 值 (17-40):")
        self._crf_label.setObjectName("info_label")
        self._crf_spin = type("Spin", (), {"value": lambda self, v=None: 28})()
        # 后门: 用 QSpinBox, 但这里简化处理
        from PySide6.QtWidgets import QSpinBox
        self._crf_spin = QSpinBox()
        self._crf_spin.setRange(17, 40)
        self._crf_spin.setValue(28)
        crf_row.addWidget(self._crf_label)
        crf_row.addWidget(self._crf_spin)
        crf_row.addStretch()
        format_layout.addRow("", crf_row)

        layout.addWidget(format_group)

        # === 分辨率 ===
        reso_group = QGroupBox("分辨率调整（可选）")
        reso_layout = QHBoxLayout(reso_group)

        self._resize_check = QCheckBox("调整分辨率")
        self._resize_check.toggled.connect(self._on_resize_toggle)

        self._device_combo = QComboBox()
        for d in DEVICE_PRESETS:
            label = d.name
            if d.description:
                label += f" ({d.description})"
            self._device_combo.addItem(label, (d.width, d.height))
        self._device_combo.setEnabled(False)

        reso_layout.addWidget(self._resize_check)
        reso_layout.addWidget(self._device_combo)
        reso_layout.addStretch()
        layout.addWidget(reso_group)

        # === 输出目录 ===
        output_group = QGroupBox("输出")
        output_layout = QHBoxLayout(output_group)

        self._output_path_edit = QLineEdit()
        self._output_path_edit.setPlaceholderText("输出目录（默认同源目录）")

        output_browse = QPushButton("📂 选择")
        output_browse.clicked.connect(self._browse_output)

        output_layout.addWidget(self._output_path_edit)
        output_layout.addWidget(output_browse)
        layout.addWidget(output_group)

        # === 进度 ===
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        # === 操作按钮 ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._start_btn = QPushButton("🚀 开始转换")
        self._start_btn.setObjectName("btn_primary")
        self._start_btn.clicked.connect(self._start_convert)
        self._start_btn.setEnabled(False)

        btn_layout.addWidget(self._start_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

        # === 拖拽支持 ===
        self.setAcceptDrops(True)

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv *.m4v *.ts);;所有文件 (*.*)"
        )
        if path:
            self._set_input(path)

    def _set_input(self, path):
        self._input_path = path
        self._input_path_edit.setText(path)
        self._start_btn.setEnabled(True)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self._output_path_edit.setText(path)

    def _on_resize_toggle(self, checked):
        self._device_combo.setEnabled(checked)

    def _start_convert(self):
        if not self._input_path:
            return

        self._start_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)

        # 获取设置
        output_dir = self._output_path_edit.text().strip()
        if not output_dir:
            output_dir = str(Path(self._input_path).parent)

        format_name = self._format_combo.currentData()
        quality_name = self._quality_combo.currentData()
        crf = self._crf_spin.value()
        do_resize = self._resize_check.isChecked()
        device = self._device_combo.currentData() if do_resize else (0, 0)

        # 构建输出路径
        stem = Path(self._input_path).stem
        ext = ".mp4"
        for p in FORMAT_PRESETS:
            if p.name == format_name:
                ext = p.extension
                break

        output_path = str(Path(output_dir) / f"{stem}_converted{ext}")

        # 获取预设
        from src.core.presets import get_format_preset, get_quality_preset
        fmt = get_format_preset(format_name)
        qlt = get_quality_preset(quality_name)

        # 确定参数
        if fmt and qlt:
            # 在 CRF 模式下的视频选项
            video_opts = fmt.video_opts
            if qlt.crf > 0:
                if "libx264" in video_opts:
                    video_opts = f"-c:v libx264 -preset medium -crf {crf}"
                elif "libx265" in video_opts:
                    video_opts = f"-c:v libx265 -preset medium -crf {crf}"
                elif "libvpx-vp9" in video_opts:
                    video_opts = f"-c:v libvpx-vp9 -b:v 0 -crf {min(crf + 2, 50)}"
            preset = {
                "video_opts": video_opts,
                "audio_opts": fmt.audio_opts,
                "extra_opts": fmt.extra_opts,
            }
        else:
            preset = None

        # 执行
        def progress_cb(pct):
            self._progress_bar.setValue(int(pct))

        try:
            if do_resize and device and device[0] > 0:
                result = change_resolution(
                    self._input_path, output_path,
                    device[0], device[1],
                    progress_callback=progress_cb,
                )
            else:
                result = convert_file(
                    self._input_path, output_path,
                    preset=preset,
                    progress_callback=progress_cb,
                )
            self._progress_bar.setValue(100)
            # 找到父窗口的 MainWindow 更新状态
            self._update_status(f"✅ 转换完成: {Path(output_path).name}")
        except Exception as e:
            self._progress_bar.setValue(0)
            self._update_status(f"❌ 转换失败: {e}")
        finally:
            self._start_btn.setEnabled(True)

    def _update_status(self, text):
        """更新底部状态栏"""
        w = self.window()
        if hasattr(w, "update_status"):
            w.update_status(text)

    # === 拖拽支持 ===
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith((".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv", ".wmv")):
                self._set_input(path)
                break
