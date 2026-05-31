"""
提取 Tab
支持提取音频和视频帧截图。
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFileDialog, QLineEdit, QSpinBox,
    QProgressBar, QComboBox, QTabWidget, QFormLayout,
)

from src.core.ffmpeg_manager import extract_audio, extract_frames


class ExtractTab(QWidget):
    """提取音频 / 提取帧"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._input_path = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("🎵 提取")
        title.setObjectName("title")
        layout.addWidget(title)

        desc = QLabel("从视频中提取音频轨道或关键帧截图")
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

        # === 提取方式 Tab ===
        self._extract_tabs = QTabWidget()

        # ---- 音频提取 Tab ----
        audio_tab = QWidget()
        audio_layout = QVBoxLayout(audio_tab)
        audio_layout.setSpacing(12)

        af_group = QGroupBox("音频格式")
        af_layout = QFormLayout(af_group)

        self._audio_format = QComboBox()
        self._audio_format.addItems(["MP3 (推荐)", "WAV (无损)", "AAC", "FLAC", "OGG"])
        af_layout.addRow("输出格式:", self._audio_format)

        audio_layout.addWidget(af_group)

        ao_group = QGroupBox("输出目录")
        ao_layout = QHBoxLayout(ao_group)
        self._audio_output = QLineEdit()
        self._audio_output.setPlaceholderText("默认同源目录")
        ao_browse = QPushButton("📂 选择")
        ao_browse.clicked.connect(lambda: self._browse_dir(self._audio_output))
        ao_layout.addWidget(self._audio_output)
        ao_layout.addWidget(ao_browse)
        audio_layout.addWidget(ao_group)

        self._audio_start_btn = QPushButton("🎵 提取音频")
        self._audio_start_btn.setObjectName("btn_primary")
        self._audio_start_btn.clicked.connect(self._start_extract_audio)
        self._audio_start_btn.setEnabled(False)
        audio_layout.addWidget(self._audio_start_btn)
        audio_layout.addStretch()

        self._extract_tabs.addTab(audio_tab, "🎵 提取音频")

        # ---- 帧提取 Tab ----
        frame_tab = QWidget()
        frame_layout = QVBoxLayout(frame_tab)
        frame_layout.setSpacing(12)

        ff_group = QGroupBox("帧提取设置")
        ff_layout = QFormLayout(ff_group)

        self._fps_spin = QSpinBox()
        self._fps_spin.setRange(1, 30)
        self._fps_spin.setValue(1)
        self._fps_spin.setSuffix(" fps")
        ff_layout.addRow("提取频率:", self._fps_spin)

        self._quality_spin = QSpinBox()
        self._quality_spin.setRange(1, 10)
        self._quality_spin.setValue(3)
        self._quality_spin.setSuffix(" (1-10, 1=最高)")
        ff_layout.addRow("图片质量:", self._quality_spin)

        frame_layout.addWidget(ff_group)

        fo_group = QGroupBox("输出目录")
        fo_layout = QHBoxLayout(fo_group)
        self._frame_output = QLineEdit()
        self._frame_output.setPlaceholderText("默认同源目录/frames")
        fo_browse = QPushButton("📂 选择")
        fo_browse.clicked.connect(lambda: self._browse_dir(self._frame_output))
        fo_layout.addWidget(self._frame_output)
        fo_layout.addWidget(fo_browse)
        frame_layout.addWidget(fo_group)

        self._frame_start_btn = QPushButton("🖼️ 提取帧")
        self._frame_start_btn.setObjectName("btn_primary")
        self._frame_start_btn.clicked.connect(self._start_extract_frames)
        self._frame_start_btn.setEnabled(False)
        frame_layout.addWidget(self._frame_start_btn)
        frame_layout.addStretch()

        self._extract_tabs.addTab(frame_tab, "🖼️ 提取帧")

        layout.addWidget(self._extract_tabs)

        # === 进度 ===
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        layout.addStretch()

        self.setAcceptDrops(True)

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv);;所有文件 (*.*)"
        )
        if path:
            self._input_path = path
            self._input_edit.setText(path)
            self._audio_start_btn.setEnabled(True)
            self._frame_start_btn.setEnabled(True)

    def _browse_dir(self, edit_widget):
        path = QFileDialog.getExistingDirectory(self, "选择目录")
        if path:
            edit_widget.setText(path)

    def _start_extract_audio(self):
        if not self._input_path:
            return

        self._audio_start_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)

        stem = Path(self._input_path).stem
        output_dir = self._audio_output.text().strip() or str(Path(self._input_path).parent)

        fmt_map = {
            "MP3 (推荐)": ".mp3",
            "WAV (无损)": ".wav",
            "AAC": ".aac",
            "FLAC": ".flac",
            "OGG": ".ogg",
        }
        ext = fmt_map.get(self._audio_format.currentText(), ".mp3")
        output_path = str(Path(output_dir) / f"{stem}_audio{ext}")

        def progress_cb(pct):
            self._progress.setValue(int(pct))

        try:
            extract_audio(self._input_path, output_path, progress_callback=progress_cb)
            self._progress.setValue(100)
            self._update_status(f"✅ 音频已提取: {Path(output_path).name}")
        except Exception as e:
            self._progress.setValue(0)
            self._update_status(f"❌ 提取失败: {e}")
        finally:
            self._audio_start_btn.setEnabled(True)

    def _start_extract_frames(self):
        if not self._input_path:
            return

        self._frame_start_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)

        stem = Path(self._input_path).stem
        output_dir = self._frame_output.text().strip() or str(Path(self._input_path).parent / f"{stem}_frames")

        fps = self._fps_spin.value()
        quality = self._quality_spin.value()

        def progress_cb(pct):
            self._progress.setValue(int(pct))

        try:
            extract_frames(
                self._input_path, output_dir,
                fps=fps, quality=quality,
                progress_callback=progress_cb,
            )
            self._progress.setValue(100)
            self._update_status(f"✅ 帧已提取到: {output_dir}")
        except Exception as e:
            self._progress.setValue(0)
            self._update_status(f"❌ 提取帧失败: {e}")
        finally:
            self._frame_start_btn.setEnabled(True)

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
                self._input_path = path
                self._input_edit.setText(path)
                self._audio_start_btn.setEnabled(True)
                self._frame_start_btn.setEnabled(True)
                break
