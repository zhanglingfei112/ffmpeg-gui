"""
语言管理模块
支持简体中文和英文的界面字符串管理。
"""

import json
import os
from typing import Optional


_STRINGS = {
    "zh_cn": {
        # 应用
        "app_name": "FFmpeg GUI",
        "app_desc": "基于 FFmpeg 的本地视频处理桌面工具",
        "status_ready": "就绪",
        "status_no_ffmpeg": "FFmpeg 未安装",
        "status_ffmpeg_ok": "FFmpeg 就绪",

        # 侧边导航
        "nav_convert": "转换",
        "nav_trim": "裁剪",
        "nav_merge": "合并",
        "nav_extract": "提取",
        "nav_info": "信息",
        "nav_batch": "批量",
        "nav_settings": "设置",

        # 转换 Tab
        "tab_convert_title": "🔄 格式转换 & 压缩",
        "tab_convert_desc": "将视频转换为其他格式、调整画质或分辨率",
        "tab_convert_input": "输入文件",
        "tab_convert_browse": "浏览",
        "tab_convert_format": "输出格式 & 质量",
        "tab_convert_output_fmt": "输出格式",
        "tab_convert_quality": "压缩质量",
        "tab_convert_crf": "CRF 值 (17-40)",
        "tab_convert_resize": "分辨率调整（可选）",
        "tab_convert_resize_check": "调整分辨率",
        "tab_convert_device": "目标设备",
        "tab_convert_output_path": "输出",
        "tab_convert_select_output": "选择",
        "tab_convert_start": "开始转换",
        "tab_convert_started": "转换进行中...",
        "tab_convert_done": "转换完成",
        "tab_convert_fail": "转换失败",
        "tab_convert_placeholder": "选择或拖拽视频文件到此处...",
        "tab_convert_output_dir_placeholder": "输出目录（默认同源目录）",

        # 裁剪 Tab
        "tab_trim_title": "✂️ 视频裁剪",
        "tab_trim_desc": "截取视频片段，支持按开始/结束时间或时长裁剪",
        "tab_trim_input": "输入文件",
        "tab_trim_browse": "浏览",
        "tab_trim_duration": "视频时长",
        "tab_trim_start": "开始时间",
        "tab_trim_end": "结束时间",
        "tab_trim_end_mode": "裁剪方式",
        "tab_trim_end_specify": "指定结束时间",
        "tab_trim_duration_specify": "指定时长",
        "tab_trim_output": "输出",
        "tab_trim_start_btn": "开始裁剪",
        "tab_trim_done": "裁剪完成",
        "tab_trim_fail": "裁剪失败",
        "tab_trim_placeholder": "选择视频文件...",

        # 合并 Tab
        "tab_merge_title": "📎 视频合并",
        "tab_merge_desc": "将多个视频片段合并成一个文件（需相同编码格式）",
        "tab_merge_video_list": "视频列表（拖拽排序）",
        "tab_merge_add": "添加文件",
        "tab_merge_remove": "移除选中",
        "tab_merge_clear": "清空列表",
        "tab_merge_output": "输出文件",
        "tab_merge_save_as": "保存到...",
        "tab_merge_start": "开始合并",
        "tab_merge_done": "合并完成",
        "tab_merge_fail": "合并失败",
        "tab_merge_warn": "提示",
        "tab_merge_warn_output": "请选择输出文件路径",

        # 提取 Tab
        "tab_extract_title": "🎵 提取",
        "tab_extract_desc": "从视频中提取音频轨道或关键帧截图",
        "tab_extract_input": "输入文件",
        "tab_extract_browse": "浏览",
        "tab_extract_audio_format": "音频格式",
        "tab_extract_audio_output": "输出目录",
        "tab_extract_frame_settings": "帧提取设置",
        "tab_extract_frame_fps": "提取频率",
        "tab_extract_frame_quality": "图片质量",
        "tab_extract_frame_output": "输出目录",
        "tab_extract_audio_btn": "提取音频",
        "tab_extract_frame_btn": "提取帧",
        "tab_extract_audio_done": "音频已提取",
        "tab_extract_frame_done": "帧已提取到",
        "tab_extract_fail": "提取失败",
        "tab_extract_audio_tab": "提取音频",
        "tab_extract_frame_tab": "提取帧",

        # 信息 Tab
        "tab_info_title": "ℹ️ 媒体信息",
        "tab_info_desc": "查看视频/音频文件的详细编码信息",
        "tab_info_select": "选择文件",
        "tab_info_browse": "浏览",
        "tab_info_group": "文件信息",
        "tab_info_placeholder": "请选择或拖拽一个视频/音频文件查看信息",
        "tab_info_fail": "读取失败",

        # 批量 Tab
        "tab_batch_title": "📋 批量任务",
        "tab_batch_desc": "批量处理视频文件，支持队列管理和并发控制",
        "tab_batch_add": "添加任务",
        "tab_batch_add_files": "选择文件",
        "tab_batch_add_folder": "选择文件夹",
        "tab_batch_clear_done": "清空已完成",
        "tab_batch_task_list": "任务列表",
        "tab_batch_cancel_all": "取消全部排队",
        "tab_batch_queue_status": "队列",
        "tab_batch_running": "运行中",
        "tab_batch_completed": "已完成",
        "tab_batch_no_video": "文件夹中未找到视频文件",

        # 设置 Tab
        "tab_settings_title": "⚙️ 设置",
        "tab_settings_desc": "配置 FFmpeg 路径、资源调度参数、界面语言",
        "tab_settings_resource": "资源调度",
        "tab_settings_concurrent": "最大并发任务数",
        "tab_settings_threads": "CPU 核心数上限",
        "tab_settings_tip": "数值越高处理越快，但系统会变卡。\n保守设置：1 核心、1 并发 → 系统全程流畅\n平衡设置：2 核心、1 并发 → 推荐\n高性能：4 核心、2 并发 → 适合专门处理机",
        "tab_settings_ffmpeg_path": "FFmpeg 路径",
        "tab_settings_ffmpeg": "FFmpeg",
        "tab_settings_ffprobe": "FFprobe",
        "tab_settings_test": "测试",
        "tab_settings_browse": "浏览",
        "tab_settings_status_hint": "点击「测试」检查 FFmpeg 状态",
        "tab_settings_language": "界面语言",
        "tab_settings_language_label": "语言",
        "tab_settings_about": "关于",
        "tab_settings_version": "版本",
        "tab_settings_tech": "技术栈",
        "tab_settings_license": "开源协议",

        # 安装检测
        "install_title": "FFmpeg 未安装",
        "install_msg": "未检测到 FFmpeg，视频处理功能无法使用。\n是否自动下载并安装 FFmpeg？",
        "install_btn_auto": "自动安装",
        "install_btn_cancel": "取消",
        "install_downloading": "正在下载 FFmpeg...",
        "install_extracting": "正在解压...",
        "install_done": "FFmpeg 安装完成！",
        "install_fail": "自动安装失败",
        "install_manual_hint": "请手动下载安装 FFmpeg：\nhttps://ffmpeg.org/download.html\n\n安装后重启应用即可。",
        "install_os_not_supported": "当前操作系统不支持自动安装。\n请访问 https://ffmpeg.org/download.html 手动下载。",
        "install_linux_hint": "Linux 用户请使用包管理器安装：\napt install ffmpeg   (Debian/Ubuntu)\nyum install ffmpeg   (RHEL/CentOS)\npacman -S ffmpeg     (Arch Linux)",

        # 通用
        "common_confirm": "确认",
        "common_cancel": "取消",
        "common_ok": "确定",
        "common_close": "关闭",
        "common_retry": "重试",
        "common_loading": "加载中...",
        "common_error": "错误",
        "common_success": "成功",
        "common_warning": "警告",
        "common_info": "信息",

        # 任务状态
        "status_waiting": "等待中",
        "status_running": "进行中",
        "status_completed": "已完成",
        "status_failed": "失败",
        "status_cancelled": "已取消",

        # 文件对话框
        "video_files": "视频文件",
        "media_files": "媒体文件",
        "all_files": "所有文件",
        "save_as_mp4": "MP4 文件",
        "save_as_mkv": "MKV 文件",
        "select_video": "选择视频文件",
        "select_media": "选择媒体文件",
        "select_folder": "选择文件夹",
        "save_merged": "保存合并文件",
        "select_output_dir": "选择输出目录",
        "select_ffmpeg": "选择 ffmpeg",
        "select_ffprobe": "选择 ffprobe",
    },

    "en_us": {
        # Application
        "app_name": "FFmpeg GUI",
        "app_desc": "Local video processing tool powered by FFmpeg",
        "status_ready": "Ready",
        "status_no_ffmpeg": "FFmpeg not found",
        "status_ffmpeg_ok": "FFmpeg ready",

        # Sidebar nav
        "nav_convert": "Convert",
        "nav_trim": "Trim",
        "nav_merge": "Merge",
        "nav_extract": "Extract",
        "nav_info": "Info",
        "nav_batch": "Batch",
        "nav_settings": "Settings",

        # Convert tab
        "tab_convert_title": "🔄 Convert & Compress",
        "tab_convert_desc": "Convert video format, adjust quality or resolution",
        "tab_convert_input": "Input File",
        "tab_convert_browse": "Browse",
        "tab_convert_format": "Output Format & Quality",
        "tab_convert_output_fmt": "Output Format",
        "tab_convert_quality": "Compression Quality",
        "tab_convert_crf": "CRF Value (17-40)",
        "tab_convert_resize": "Resolution (Optional)",
        "tab_convert_resize_check": "Adjust Resolution",
        "tab_convert_device": "Target Device",
        "tab_convert_output_path": "Output",
        "tab_convert_select_output": "Select",
        "tab_convert_start": "Start Convert",
        "tab_convert_started": "Converting...",
        "tab_convert_done": "Convert completed",
        "tab_convert_fail": "Convert failed",
        "tab_convert_placeholder": "Drop or select a video file...",
        "tab_convert_output_dir_placeholder": "Output directory (same as source by default)",

        # Trim tab
        "tab_trim_title": "✂️ Video Trim",
        "tab_trim_desc": "Cut video clips by start/end time or duration",
        "tab_trim_input": "Input File",
        "tab_trim_browse": "Browse",
        "tab_trim_duration": "Duration",
        "tab_trim_start": "Start Time",
        "tab_trim_end": "End Time",
        "tab_trim_end_mode": "Trim Mode",
        "tab_trim_end_specify": "Specify End Time",
        "tab_trim_duration_specify": "Specify Duration",
        "tab_trim_output": "Output",
        "tab_trim_start_btn": "Start Trim",
        "tab_trim_done": "Trim completed",
        "tab_trim_fail": "Trim failed",
        "tab_trim_placeholder": "Select a video file...",

        # Merge tab
        "tab_merge_title": "📎 Merge Videos",
        "tab_merge_desc": "Merge multiple video files into one (same codec required)",
        "tab_merge_video_list": "Video List (drag to reorder)",
        "tab_merge_add": "Add Files",
        "tab_merge_remove": "Remove Selected",
        "tab_merge_clear": "Clear List",
        "tab_merge_output": "Output File",
        "tab_merge_save_as": "Save As...",
        "tab_merge_start": "Start Merge",
        "tab_merge_done": "Merge completed",
        "tab_merge_fail": "Merge failed",
        "tab_merge_warn": "Notice",
        "tab_merge_warn_output": "Please select an output file path",

        # Extract tab
        "tab_extract_title": "🎵 Extract",
        "tab_extract_desc": "Extract audio tracks or video frames",
        "tab_extract_input": "Input File",
        "tab_extract_browse": "Browse",
        "tab_extract_audio_format": "Audio Format",
        "tab_extract_audio_output": "Output Directory",
        "tab_extract_frame_settings": "Frame Extraction Settings",
        "tab_extract_frame_fps": "Extraction Rate",
        "tab_extract_frame_quality": "Image Quality",
        "tab_extract_frame_output": "Output Directory",
        "tab_extract_audio_btn": "Extract Audio",
        "tab_extract_frame_btn": "Extract Frames",
        "tab_extract_audio_done": "Audio extracted",
        "tab_extract_frame_done": "Frames extracted to",
        "tab_extract_fail": "Extraction failed",
        "tab_extract_audio_tab": "Extract Audio",
        "tab_extract_frame_tab": "Extract Frames",

        # Info tab
        "tab_info_title": "ℹ️ Media Info",
        "tab_info_desc": "View detailed media file information",
        "tab_info_select": "Select File",
        "tab_info_browse": "Browse",
        "tab_info_group": "File Info",
        "tab_info_placeholder": "Select or drop a media file to view info",
        "tab_info_fail": "Failed to read",

        # Batch tab
        "tab_batch_title": "📋 Batch Tasks",
        "tab_batch_desc": "Process multiple video files with queue management",
        "tab_batch_add": "Add Tasks",
        "tab_batch_add_files": "Select Files",
        "tab_batch_add_folder": "Select Folder",
        "tab_batch_clear_done": "Clear Completed",
        "tab_batch_task_list": "Task List",
        "tab_batch_cancel_all": "Cancel All Queued",
        "tab_batch_queue_status": "Queue",
        "tab_batch_running": "Running",
        "tab_batch_completed": "Completed",
        "tab_batch_no_video": "No video files found in folder",

        # Settings tab
        "tab_settings_title": "⚙️ Settings",
        "tab_settings_desc": "Configure FFmpeg path, resource limits, language",
        "tab_settings_resource": "Resource Management",
        "tab_settings_concurrent": "Max Concurrent Tasks",
        "tab_settings_threads": "CPU Core Limit",
        "tab_settings_tip": "Higher = faster but system may lag.\nConservative: 1 core, 1 task → smooth multitasking\nBalanced: 2 cores, 1 task → recommended\nHigh perf: 4 cores, 2 tasks → dedicated machine",
        "tab_settings_ffmpeg_path": "FFmpeg Path",
        "tab_settings_ffmpeg": "FFmpeg",
        "tab_settings_ffprobe": "FFprobe",
        "tab_settings_test": "Test",
        "tab_settings_browse": "Browse",
        "tab_settings_status_hint": "Click 'Test' to check FFmpeg status",
        "tab_settings_language": "Interface Language",
        "tab_settings_language_label": "Language",
        "tab_settings_about": "About",
        "tab_settings_version": "Version",
        "tab_settings_tech": "Tech Stack",
        "tab_settings_license": "License",

        # Install dialog
        "install_title": "FFmpeg Not Found",
        "install_msg": "FFmpeg was not detected. Video processing requires FFmpeg.\nDownload and install FFmpeg now?",
        "install_btn_auto": "Auto Install",
        "install_btn_cancel": "Cancel",
        "install_downloading": "Downloading FFmpeg...",
        "install_extracting": "Extracting...",
        "install_done": "FFmpeg installed successfully!",
        "install_fail": "Auto install failed",
        "install_manual_hint": "Please manually download FFmpeg:\nhttps://ffmpeg.org/download.html\n\nRestart the app after installation.",
        "install_os_not_supported": "Auto install is not supported on this OS.\nPlease visit https://ffmpeg.org/download.html",
        "install_linux_hint": "Linux users: install via package manager:\napt install ffmpeg   (Debian/Ubuntu)\nyum install ffmpeg   (RHEL/CentOS)\npacman -S ffmpeg     (Arch Linux)",

        # Common
        "common_confirm": "Confirm",
        "common_cancel": "Cancel",
        "common_ok": "OK",
        "common_close": "Close",
        "common_retry": "Retry",
        "common_loading": "Loading...",
        "common_error": "Error",
        "common_success": "Success",
        "common_warning": "Warning",
        "common_info": "Info",

        # Task status
        "status_waiting": "Waiting",
        "status_running": "Running",
        "status_completed": "Completed",
        "status_failed": "Failed",
        "status_cancelled": "Cancelled",

        # File dialogs
        "video_files": "Video Files",
        "media_files": "Media Files",
        "all_files": "All Files",
        "save_as_mp4": "MP4 File",
        "save_as_mkv": "MKV File",
        "select_video": "Select Video File",
        "select_media": "Select Media File",
        "select_folder": "Select Folder",
        "save_merged": "Save Merged File",
        "select_output_dir": "Select Output Directory",
        "select_ffmpeg": "Select ffmpeg",
        "select_ffprobe": "Select ffprobe",
    },
}


class LanguageManager:
    """语言管理器单例"""

    _instance = None

    def __init__(self):
        self._current = "zh_cn"
        self._listeners = []

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def current(self) -> str:
        return self._current

    def set_language(self, lang: str):
        if lang in _STRINGS and lang != self._current:
            self._current = lang
            for callback in self._listeners:
                try:
                    callback(lang)
                except Exception:
                    pass

    def add_listener(self, callback):
        """添加语言变更监听器"""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def tr(self, key: str) -> str:
        """获取当前语言的字符串"""
        return _STRINGS.get(self._current, {}).get(key, _STRINGS.get("zh_cn", {}).get(key, key))

    def is_chinese(self) -> bool:
        return self._current == "zh_cn"

    @staticmethod
    def available_languages() -> list[tuple[str, str]]:
        return [("zh_cn", "中文"), ("en_us", "English")]


# 快捷函数
_lang = LanguageManager.instance


def _(key: str) -> str:
    """快捷翻译函数"""
    return _lang().tr(key)
