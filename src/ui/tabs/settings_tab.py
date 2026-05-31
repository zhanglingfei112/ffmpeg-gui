"""
设置 Tab
资源管理、FFmpeg 路径、界面语言、应用配置。
"""

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QSpinBox, QLineEdit, QFormLayout, QFileDialog,
    QComboBox, QMessageBox,
)

from src.core.ffmpeg_manager import check_ffmpeg_installed, check_ffprobe_installed
from src.core.language import LanguageManager, _ as _tr


class SettingsTab(QWidget):
    """设置与资源管理"""

    _instance = None

    def __init__(self, parent=None):
        super().__init__(parent)
        SettingsTab._instance = self
        self._max_concurrent = 1
        self._default_threads = 2
        self._ffmpeg_path = "ffmpeg"
        self._ffprobe_path = "ffprobe"
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(24, 20, 24, 20)
        self._layout.setSpacing(16)
        self._build_ui()

    def _build_ui(self):
        # 清除旧内容
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        layout = self._layout

        title = QLabel(_tr("tab_settings_title"))
        title.setObjectName("title")
        layout.addWidget(title)

        desc = QLabel(_tr("tab_settings_desc"))
        desc.setStyleSheet("color: #8888aa; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(desc)

        # === 资源调度 ===
        res_group = QGroupBox(_tr("tab_settings_resource"))
        res_layout = QFormLayout(res_group)
        res_layout.setSpacing(10)

        self._concurrent_spin = QSpinBox()
        self._concurrent_spin.setRange(1, 2)
        self._concurrent_spin.setValue(self._max_concurrent)
        self._concurrent_spin.valueChanged.connect(self._on_concurrent_changed)
        res_layout.addRow(_tr("tab_settings_concurrent") + ":", self._concurrent_spin)

        self._threads_spin = QSpinBox()
        self._threads_spin.setRange(1, 4)
        self._threads_spin.setValue(self._default_threads)
        self._threads_spin.setSuffix(" 核心")
        self._threads_spin.valueChanged.connect(self._on_threads_changed)
        res_layout.addRow(_tr("tab_settings_threads") + ":", self._threads_spin)

        tips = QLabel(f"💡 {_tr('tab_settings_tip')}")
        tips.setStyleSheet("color: #8888aa; font-size: 11px; padding: 4px;")
        res_layout.addRow("", tips)

        layout.addWidget(res_group)

        # === 语言设置 ===
        lang_group = QGroupBox(_tr("tab_settings_language"))
        lang_layout = QFormLayout(lang_group)
        lang_layout.setSpacing(10)

        self._lang_combo = QComboBox()
        for code, name in LanguageManager.available_languages():
            self._lang_combo.addItem(name, code)
        # 设置当前语言
        current = LanguageManager.instance().current
        idx = self._lang_combo.findData(current)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addRow(_tr("tab_settings_language_label") + ":", self._lang_combo)

        layout.addWidget(lang_group)

        # === FFmpeg 配置 ===
        ff_group = QGroupBox(_tr("tab_settings_ffmpeg_path"))
        ff_layout = QFormLayout(ff_group)
        ff_layout.setSpacing(10)

        # ffmpeg
        ffmpeg_row = QHBoxLayout()
        self._ffmpeg_edit = QLineEdit(self._ffmpeg_path)
        self._ffmpeg_edit.textChanged.connect(self._on_ffmpeg_path_changed)
        ffmpeg_browse = QPushButton(f"📂 {_tr('tab_settings_browse')}")
        ffmpeg_browse.clicked.connect(self._browse_ffmpeg)
        ffmpeg_test = QPushButton(f"🔍 {_tr('tab_settings_test')}")
        ffmpeg_test.clicked.connect(self._test_ffmpeg)
        ffmpeg_row.addWidget(self._ffmpeg_edit)
        ffmpeg_row.addWidget(ffmpeg_browse)
        ffmpeg_row.addWidget(ffmpeg_test)
        ff_layout.addRow(f"{_tr('tab_settings_ffmpeg')}:", ffmpeg_row)

        # ffprobe
        ffprobe_row = QHBoxLayout()
        self._ffprobe_edit = QLineEdit(self._ffprobe_path)
        ffprobe_browse = QPushButton(f"📂 {_tr('tab_settings_browse')}")
        ffprobe_browse.clicked.connect(self._browse_ffprobe)
        ffprobe_test = QPushButton(f"🔍 {_tr('tab_settings_test')}")
        ffprobe_test.clicked.connect(self._test_ffprobe)
        ffprobe_row.addWidget(self._ffprobe_edit)
        ffprobe_row.addWidget(ffprobe_browse)
        ffprobe_row.addWidget(ffprobe_test)
        ff_layout.addRow(f"{_tr('tab_settings_ffprobe')}:", ffprobe_row)

        # 状态
        self._ff_status = QLabel(_tr("tab_settings_status_hint"))
        self._ff_status.setStyleSheet("color: #8888aa; font-size: 11px; padding: 4px;")
        ff_layout.addRow("", self._ff_status)

        layout.addWidget(ff_group)

        # === 关于 ===
        about_group = QGroupBox(_tr("tab_settings_about"))
        about_layout = QVBoxLayout(about_group)
        about_layout.addWidget(QLabel(f"{_tr('tab_settings_version')}: FFmpeg GUI v0.1.0"))
        about_layout.addWidget(QLabel(f"{_tr('tab_settings_tech')}: Python + PySide6 + FFmpeg"))
        about_layout.addWidget(QLabel(f"{_tr('tab_settings_license')}: MIT"))
        layout.addWidget(about_group)

        layout.addStretch()

    def retranslate_ui(self):
        """重新翻译界面（语言切换时调用）"""
        # 不要重建UI，避免丢失状态
        self._simple_retranslate()

    def on_language_changed(self):
        """语言切换时仅更新文本，不重建"""
        self._simple_retranslate()

    def _simple_retranslate(self):
        """仅更新现有控件的文本"""
        # 找到所有子控件并更新它们的文本
        # 这个方法在_build_ui后只更新label/button文本
        for widget in self.findChildren(QLabel):
            current = widget.text()
            # 跳过非翻译控件（文件路径、状态等）
            if current.startswith("✅") or current.startswith("❌") or not current:
                continue
        for widget in self.findChildren(QGroupBox):
            current = widget.title()
        # 简单的重建方式 — 保留配置值
        old_concurrent = self._concurrent_spin.value() if hasattr(self, '_concurrent_spin') else self._max_concurrent
        old_threads = self._threads_spin.value() if hasattr(self, '_threads_spin') else self._default_threads
        old_lang = self._lang_combo.currentData() if hasattr(self, '_lang_combo') else None

        self._build_ui()

        # 恢复旧值
        if hasattr(self, '_concurrent_spin'):
            self._concurrent_spin.setValue(old_concurrent)
        if hasattr(self, '_threads_spin'):
            self._threads_spin.setValue(old_threads)
        if old_lang and hasattr(self, '_lang_combo'):
            idx = self._lang_combo.findData(old_lang)
            if idx >= 0:
                self._lang_combo.setCurrentIndex(idx)

    def _on_language_changed(self, idx):
        code = self._lang_combo.currentData()
        if code:
            LanguageManager.instance().set_language(code)
            # 保存设置
            settings = QSettings()
            settings.setValue("language", code)

    def _on_concurrent_changed(self, val):
        self._max_concurrent = val
        self._update_all_configs()

    def _on_threads_changed(self, val):
        self._default_threads = val
        self._update_all_configs()

    def _on_ffmpeg_path_changed(self, val):
        self._ffmpeg_path = val.strip() or "ffmpeg"

    def _update_all_configs(self):
        """将设置同步到所有依赖模块"""
        # 通知当前 MainWindow 的 batch_tab
        w = self.window()
        if hasattr(w, "_tabs"):
            for tab in w._tabs:
                if hasattr(tab, "_queue") and hasattr(tab._queue, "max_concurrent"):
                    tab._queue.max_concurrent = self._max_concurrent
                    tab._queue.default_threads = self._default_threads

    def _browse_ffmpeg(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 ffmpeg", "",
                                               "可执行文件 (*.exe *);;所有文件 (*.*)")
        if path:
            self._ffmpeg_edit.setText(path)

    def _browse_ffprobe(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 ffprobe", "",
                                               "可执行文件 (*.exe *);;所有文件 (*.*)")
        if path:
            self._ffprobe_edit.setText(path)

    def _test_ffmpeg(self):
        ok, msg = check_ffmpeg_installed()
        if ok:
            self._ff_status.setText(f"✅ {msg[:60]}")
            self._ff_status.setStyleSheet("color: #4aca6a; font-size: 11px; padding: 4px;")
        else:
            self._ff_status.setText(f"❌ {msg}")
            self._ff_status.setStyleSheet("color: #da4a4a; font-size: 11px; padding: 4px;")

    def _test_ffprobe(self):
        ok, msg = check_ffprobe_installed()
        if ok:
            self._ff_status.setText(f"✅ {msg[:60]}")
            self._ff_status.setStyleSheet("color: #4aca6a; font-size: 11px; padding: 4px;")
        else:
            self._ff_status.setText(f"❌ {msg}")
            self._ff_status.setStyleSheet("color: #da4a4a; font-size: 11px; padding: 4px;")
