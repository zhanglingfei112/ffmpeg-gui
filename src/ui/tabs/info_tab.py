"""
媒体信息 Tab
显示视频文件的完整元数据。
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFileDialog, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame,
)

from src.core.ffmpeg_manager import get_media_info, check_ffmpeg_installed


class InfoTab(QWidget):
    """媒体信息查看"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("ℹ️ 媒体信息")
        title.setObjectName("title")
        layout.addWidget(title)

        desc = QLabel("查看视频/音频文件的详细编码信息")
        desc.setStyleSheet("color: #8888aa; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(desc)

        # === 输入 ===
        input_group = QGroupBox("选择文件")
        input_layout = QHBoxLayout(input_group)

        self._input_edit = QLineEdit()
        self._input_edit.setPlaceholderText("拖拽或选择视频/音频文件...")
        self._input_edit.setReadOnly(True)

        browse_btn = QPushButton("📂 浏览")
        browse_btn.clicked.connect(self._browse_file)

        input_layout.addWidget(self._input_edit)
        input_layout.addWidget(browse_btn)
        layout.addWidget(input_group)

        # === 信息展示 ===
        self._info_group = QGroupBox("文件信息")
        info_layout = QVBoxLayout(self._info_group)

        # 概要信息卡
        self._summary_frame = QFrame()
        self._summary_frame.setObjectName("drop_zone")
        summary_layout = QVBoxLayout(self._summary_frame)
        self._summary_label = QLabel("请选择或拖拽一个视频/音频文件查看信息")
        self._summary_label.setAlignment(Qt.AlignCenter)
        self._summary_label.setWordWrap(True)
        self._summary_label.setStyleSheet("color: #55557a; font-size: 14px; padding: 30px;")
        summary_layout.addWidget(self._summary_label)
        info_layout.addWidget(self._summary_frame)

        # 详细信息表格
        self._info_table = QTableWidget()
        self._info_table.setColumnCount(2)
        self._info_table.setHorizontalHeaderLabels(["属性", "值"])
        self._info_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._info_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._info_table.verticalHeader().setVisible(False)
        self._info_table.setVisible(False)
        info_layout.addWidget(self._info_table)

        layout.addWidget(self._info_group)
        layout.addStretch()

        self.setAcceptDrops(True)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择媒体文件", "",
            "媒体文件 (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv *.mp3 *.wav *.aac *.flac *.ogg);;所有文件 (*.*)"
        )
        if path:
            self._load_info(path)

    def _load_info(self, path):
        self._input_edit.setText(path)
        try:
            info = get_media_info(path)

            # 摘要信息
            summary = f"""📁 {info.file_name}
📏 大小: {info.file_size_str}
⏱ 时长: {info.duration_str}
🎬 视频: {info.video.get('codec', 'N/A')} · {info.video.get('width', '?')}x{info.video.get('height', '?')} · {info.video.get('fps', '?')} fps
🔊 音频: {info.audio.get('codec', 'N/A')} · {info.audio.get('sample_rate', '?')} Hz · {info.audio.get('channels', '?')} ch"""
            self._summary_label.setText(summary)
            self._summary_label.setAlignment(Qt.AlignLeft)
            self._summary_label.setStyleSheet("color: #c0c0d0; font-size: 13px; padding: 20px; line-height: 1.8;")

            # 详细信息表
            rows = [
                ("文件路径", info.file_path),
                ("文件名", info.file_name),
                ("文件大小", info.file_size_str),
                ("格式", info.format_name),
                ("时长", info.duration_str),
                ("总比特率", info.bitrate_str),
                ("", ""),
                ("— 视频流 —", ""),
                ("编码", info.video.get("codec", "无")),
                ("分辨率", f"{info.video.get('width', 0)} × {info.video.get('height', 0)}"),
                ("帧率", f"{info.video.get('fps', 0)} fps"),
                ("像素格式", info.video.get("pixel_format", "N/A")),
                ("视频比特率", f"{info.video.get('bitrate', 0) // 1000} kbps" if info.video.get("bitrate") else "N/A"),
                ("", ""),
                ("— 音频流 —", ""),
                ("编码", info.audio.get("codec", "无")),
                ("采样率", f"{info.audio.get('sample_rate', 0)} Hz"),
                ("声道数", str(info.audio.get("channels", 0))),
                ("音频比特率", f"{info.audio.get('bitrate', 0) // 1000} kbps" if info.audio.get("bitrate") else "N/A"),
            ]

            self._info_table.setRowCount(len(rows))
            for i, (key, val) in enumerate(rows):
                key_item = QTableWidgetItem(key)
                key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
                if key in ("— 视频流 —", "— 音频流 —") or (key == "" and val == ""):
                    key_item.setForeground(Qt.gray)
                self._info_table.setItem(i, 0, key_item)

                val_item = QTableWidgetItem(str(val))
                val_item.setFlags(val_item.flags() & ~Qt.ItemIsEditable)
                self._info_table.setItem(i, 1, val_item)

            self._info_table.setVisible(True)

        except Exception as e:
            self._summary_label.setText(f"❌ 读取失败: {e}")
            self._summary_label.setAlignment(Qt.AlignCenter)
            self._summary_label.setStyleSheet("color: #da4a4a; font-size: 14px; padding: 30px;")
            self._info_table.setVisible(False)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith((".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv", ".wmv",
                                       ".mp3", ".wav", ".aac", ".flac", ".ogg")):
                self._load_info(path)
                break
