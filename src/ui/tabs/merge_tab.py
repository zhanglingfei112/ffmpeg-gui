"""
视频合并 Tab
将多个视频文件合并为一个。
"""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFileDialog, QListWidget, QListWidgetItem,
    QProgressBar, QLineEdit, QMessageBox,
)

from src.core.ffmpeg_manager import merge_videos


class MergeTab(QWidget):
    """视频合并"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_paths = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("📎 视频合并")
        title.setObjectName("title")
        layout.addWidget(title)

        desc = QLabel("将多个视频片段合并成一个文件（需相同编码格式）")
        desc.setStyleSheet("color: #8888aa; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(desc)

        # === 文件列表 ===
        list_group = QGroupBox("视频列表（拖拽排序）")
        list_layout = QVBoxLayout(list_group)

        self._file_list = QListWidget()
        self._file_list.setAlternatingRowColors(True)
        self._file_list.setDragDropMode(QListWidget.InternalMove)
        self._file_list.setDefaultDropAction(Qt.MoveAction)
        # 拖拽排序后同步数据列表
        self._file_list.model().layoutChanged.connect(self._sync_file_paths)
        list_layout.addWidget(self._file_list)

        # 操作按钮
        list_btn_layout = QHBoxLayout()

        add_btn = QPushButton("➕ 添加文件")
        add_btn.clicked.connect(self._add_files)

        remove_btn = QPushButton("🗑 移除选中")
        remove_btn.clicked.connect(self._remove_selected)

        clear_btn = QPushButton("清空列表")
        clear_btn.clicked.connect(self._clear_list)

        list_btn_layout.addWidget(add_btn)
        list_btn_layout.addWidget(remove_btn)
        list_btn_layout.addWidget(clear_btn)
        list_btn_layout.addStretch()
        list_layout.addLayout(list_btn_layout)

        layout.addWidget(list_group)

        # === 输出 ===
        output_group = QGroupBox("输出文件")
        output_layout = QHBoxLayout(output_group)

        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("合并后的文件路径...")
        output_browse = QPushButton("📂 保存到...")
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
        self._start_btn = QPushButton("📎 开始合并")
        self._start_btn.setObjectName("btn_primary")
        self._start_btn.clicked.connect(self._start_merge)
        self._start_btn.setEnabled(False)
        btn_layout.addWidget(self._start_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv);;所有文件 (*.*)"
        )
        for path in paths:
            if path not in self._file_paths:
                self._file_paths.append(path)
                self._file_list.addItem(Path(path).name)
                self._file_list.item(self._file_list.count() - 1).setToolTip(path)
        self._update_start_btn()

    def _remove_selected(self):
        for item in self._file_list.selectedItems():
            idx = self._file_list.row(item)
            self._file_list.takeItem(idx)
            if idx < len(self._file_paths):
                self._file_paths.pop(idx)
        self._update_start_btn()

    def _sync_file_paths(self):
        """拖拽排序后同步 _file_paths 数据列表"""
        new_paths = []
        for i in range(self._file_list.count()):
            item = self._file_list.item(i)
            tooltip = item.toolTip()
            # tooltip 里存的是完整路径
            if tooltip and tooltip in self._file_paths:
                new_paths.append(tooltip)
            elif tooltip:
                new_paths.append(tooltip)
        if new_paths:
            self._file_paths[:] = new_paths

    def _clear_list(self):
        self._file_list.clear()
        self._file_paths.clear()
        self._update_start_btn()

    def _update_start_btn(self):
        self._start_btn.setEnabled(len(self._file_paths) >= 2)

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存合并文件", "",
            "MP4 文件 (*.mp4);;MKV 文件 (*.mkv);;所有文件 (*.*)"
        )
        if path:
            self._output_edit.setText(path)

    def _start_merge(self):
        if len(self._file_paths) < 2:
            return

        output = self._output_edit.text().strip()
        if not output:
            QMessageBox.warning(self, "提示", "请选择输出文件路径")
            return

        self._start_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)

        def progress_cb(pct):
            self._progress.setValue(int(pct))

        try:
            merge_videos(self._file_paths, output, progress_callback=progress_cb)
            self._progress.setValue(100)
            self._update_status(f"✅ 合并完成: {Path(output).name}")
        except Exception as e:
            self._progress.setValue(0)
            self._update_status(f"❌ 合并失败: {e}")
        finally:
            self._start_btn.setEnabled(True)

    def _update_status(self, text):
        w = self.window()
        if hasattr(w, "update_status"):
            w.update_status(text)
