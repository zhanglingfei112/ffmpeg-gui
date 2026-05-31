"""
批量任务 Tab
管理批量任务队列，支持添加、取消、查看进度。
"""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QMessageBox,
)

from src.core.task_queue import TaskQueue, TaskStatus
from src.core.ffmpeg_manager import convert_file, compress_video, change_resolution


class BatchTab(QWidget):
    """批量任务处理"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue = TaskQueue(max_concurrent=1, default_threads=2)
        self._setup_ui()

        # 定时刷新 UI
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_table)
        self._timer.start(500)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("📋 批量任务")
        title.setObjectName("title")
        layout.addWidget(title)

        desc = QLabel("批量处理视频文件，支持队列管理和并发控制")
        desc.setStyleSheet("color: #8888aa; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(desc)

        # === 添加文件区域 ===
        add_group = QGroupBox("添加任务")
        add_layout = QHBoxLayout(add_group)

        add_files_btn = QPushButton("📂 选择文件")
        add_files_btn.clicked.connect(self._add_files)

        add_folder_btn = QPushButton("📁 选择文件夹")
        add_folder_btn.clicked.connect(self._add_folder)

        clear_btn = QPushButton("🗑 清空已完成")
        clear_btn.clicked.connect(self._clear_completed)

        add_layout.addWidget(add_files_btn)
        add_layout.addWidget(add_folder_btn)
        add_layout.addStretch()
        add_layout.addWidget(clear_btn)
        layout.addWidget(add_group)

        # === 任务列表 ===
        table_group = QGroupBox("任务列表")
        table_layout = QVBoxLayout(table_group)

        self._task_table = QTableWidget()
        self._task_table.setColumnCount(5)
        self._task_table.setHorizontalHeaderLabels(["任务名", "状态", "进度", "耗时", "操作"])
        self._task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._task_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._task_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._task_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._task_table.verticalHeader().setVisible(False)
        self._task_table.setSelectionBehavior(QTableWidget.SelectRows)

        table_layout.addWidget(self._task_table)

        # 队列控制按钮
        ctrl_layout = QHBoxLayout()

        self._cancel_all_btn = QPushButton("⏹ 取消全部排队")
        self._cancel_all_btn.clicked.connect(self._cancel_all)
        self._cancel_all_btn.setEnabled(False)

        ctrl_layout.addWidget(self._cancel_all_btn)
        ctrl_layout.addStretch()

        # 并发数显示
        self._queue_status = QLabel("队列: 0 | 运行中: 0 | 已完成: 0")
        self._queue_status.setStyleSheet("color: #8888aa; font-size: 12px;")
        ctrl_layout.addWidget(self._queue_status)

        table_layout.addLayout(ctrl_layout)
        layout.addWidget(table_group)

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv);;所有文件 (*.*)"
        )
        self._add_tasks(paths)

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            paths = []
            for ext in (".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv", ".wmv", ".m4v"):
                paths.extend(str(p) for p in Path(folder).rglob(f"*{ext}"))
            if paths:
                self._add_tasks(paths)
            else:
                QMessageBox.information(self, "提示", "文件夹中未找到视频文件")

    def _add_tasks(self, paths):
        if not paths:
            return

        # 默认输出目录 = 源目录 + "_converted"
        for path in paths[:20]:  # 限制最多 20 个
            stem = Path(path).stem
            out_dir = Path(path).parent / f"{stem}_converted"
            out_dir.mkdir(exist_ok=True)
            output_path = str(out_dir / f"{stem}_compressed.mp4")

            task_id = self._queue.add_task(
                stem, compress_video,
                path, output_path,
                crf=28,
            )

        self._queue_status.setText(
            f"队列: {self._queue.waiting_count} | "
            f"运行中: {self._queue.running_count} | "
            f"已完成: {self._queue.completed_count}"
        )
        self._cancel_all_btn.setEnabled(self._queue.waiting_count > 0)
        self._refresh_table()

    def _cancel_all(self):
        cancelled = self._queue.cancel_all()
        if cancelled:
            self._update_status(f"已取消 {len(cancelled)} 个任务")

    def _clear_completed(self):
        self._queue.clear_completed()
        self._refresh_table()

    def _refresh_table(self):
        tasks = self._queue.get_all_tasks()
        self._task_table.setRowCount(len(tasks))

        for i, task in enumerate(tasks):
            # 任务名
            name_item = QTableWidgetItem(task.name)
            name_item.setToolTip(task.error or "")
            self._task_table.setItem(i, 0, name_item)

            # 状态
            status_text = task.status.value
            status_item = QTableWidgetItem(status_text)
            if task.status == TaskStatus.RUNNING:
                status_item.setForeground(Qt.blue)
            elif task.status == TaskStatus.COMPLETED:
                status_item.setForeground(Qt.darkGreen)
            elif task.status == TaskStatus.FAILED:
                status_item.setForeground(Qt.red)
            elif task.status == TaskStatus.CANCELLED:
                status_item.setForeground(Qt.gray)
            self._task_table.setItem(i, 1, status_item)

            # 进度
            progress_item = QTableWidgetItem(f"{int(task.progress)}%")
            self._task_table.setItem(i, 2, progress_item)

            # 耗时
            dur_item = QTableWidgetItem(task.duration_str)
            self._task_table.setItem(i, 3, dur_item)

            # 操作按钮
            op_widget = QWidget()
            op_layout = QHBoxLayout(op_widget)
            op_layout.setContentsMargins(4, 2, 4, 2)

            if task.status == TaskStatus.WAITING:
                cancel_btn = QPushButton("取消")
                cancel_btn.setFixedWidth(50)
                cancel_btn.clicked.connect(lambda checked, tid=task.id: self._queue.cancel_task(tid))
                op_layout.addWidget(cancel_btn)

            self._task_table.setCellWidget(i, 4, op_widget)
            self._task_table.setRowHeight(i, 40)

        # 更新队列状态
        self._queue_status.setText(
            f"队列: {self._queue.waiting_count} | "
            f"运行中: {self._queue.running_count} | "
            f"已完成: {self._queue.completed_count}"
        )
        self._cancel_all_btn.setEnabled(self._queue.waiting_count > 0)

    def _update_status(self, text):
        w = self.window()
        if hasattr(w, "update_status"):
            w.update_status(text)
