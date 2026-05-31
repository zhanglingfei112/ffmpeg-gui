"""
FFmpeg 管理器测试
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.ffmpeg_manager import (
    MediaInfo, get_media_info, check_ffmpeg_installed, check_ffprobe_installed,
    _parse_time_str, convert_file, FFMPEG_PATH, FFPROBE_PATH,
)


class TestMediaInfo(unittest.TestCase):
    """MediaInfo 类测试"""

    def test_duration_str(self):
        info = MediaInfo({"duration": 3661.5})
        self.assertEqual(info.duration_str, "01:01:01.500")

    def test_duration_str_zero(self):
        info = MediaInfo({"duration": 0})
        self.assertEqual(info.duration_str, "00:00:00.000")

    def test_file_size_str_bytes(self):
        info = MediaInfo({"file_size": 500})
        self.assertEqual(info.file_size_str, "500.0 B")

    def test_file_size_str_kb(self):
        info = MediaInfo({"file_size": 2048})
        self.assertEqual(info.file_size_str, "2.0 KB")

    def test_file_size_str_mb(self):
        info = MediaInfo({"file_size": 1048576 * 5})
        self.assertEqual(info.file_size_str, "5.0 MB")

    def test_file_size_str_gb(self):
        info = MediaInfo({"file_size": 1073741824 * 2})
        self.assertEqual(info.file_size_str, "2.0 GB")

    def test_bitrate_str(self):
        info = MediaInfo({
            "video": {"bitrate": 5000000},
            "audio": {"bitrate": 128000},
        })
        self.assertEqual(info.bitrate_str, "5 Mbps")

    def test_bitrate_str_unknown(self):
        info = MediaInfo({"video": {}, "audio": {}})
        self.assertEqual(info.bitrate_str, "未知")


class TestParseTimeStr(unittest.TestCase):
    """时间字符串解析测试"""

    def test_hms(self):
        self.assertAlmostEqual(_parse_time_str("01:30:45.500"), 5445.5)

    def test_ms(self):
        self.assertAlmostEqual(_parse_time_str("05:30.0"), 330.0)

    def test_seconds(self):
        self.assertAlmostEqual(_parse_time_str("120.5"), 120.5)


class TestCheckFFmpeg(unittest.TestCase):
    """FFmpeg 可用性检查测试"""

    def test_check_installed(self):
        """测试 FFmpeg 检查可以运行"""
        ok, msg = check_ffmpeg_installed()
        # 在 VPS 上可能安装也可能没安装，不做断言
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(msg, str)

    def test_check_ffprobe(self):
        ok, msg = check_ffprobe_installed()
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(msg, str)


class TestFFprobeIntegration(unittest.TestCase):
    """FFprobe 集成测试（仅在 ffprobe 可用时运行）"""

    @classmethod
    def setUpClass(cls):
        cls.ffprobe_ok, _ = check_ffprobe_installed()

    def test_get_media_info_nonexistent(self):
        if not self.ffprobe_ok:
            self.skipTest("ffprobe not available")
        with self.assertRaises(Exception):
            get_media_info("/nonexistent/file.mp4")

    def test_get_media_info_small_video(self):
        """测试 ffprobe 能解析视频文件"""
        if not self.ffprobe_ok:
            self.skipTest("ffprobe not available")

        # 查找系统上的测试音频文件
        test_videos = [
            "/usr/share/sounds/alsa/Front_Center.wav",
        ]
        test_file = None
        for p in test_videos:
            if os.path.isfile(p):
                test_file = p
                break

        if not test_file:
            self.skipTest("no test media file found on this system")

        info = get_media_info(test_file)
        self.assertIsInstance(info, MediaInfo)
        self.assertEqual(info.file_path, test_file)
        self.assertGreater(info.file_size, 0)


class TestConvertFile(unittest.TestCase):
    """转换功能测试（仅 ffmpeg 可用时运行）"""

    @classmethod
    def setUpClass(cls):
        cls.ffmpeg_ok, _ = check_ffmpeg_installed()
        cls.ffprobe_ok, _ = check_ffprobe_installed()

    def test_convert_nonexistent_input(self):
        if not self.ffmpeg_ok:
            self.skipTest("ffmpeg not available")
        with self.assertRaises(Exception):
            convert_file("/nonexistent/file.mp4", "/tmp/out.mp4")


if __name__ == "__main__":
    unittest.main()
