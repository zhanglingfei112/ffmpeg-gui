"""
FFmpeg 管理器测试
"""

import os
import sys
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.ffmpeg_manager import (
    MediaInfo, get_media_info, check_ffmpeg_installed, check_ffprobe_installed,
    _parse_time_str, convert_file, extract_audio, FFMPEG_PATH, FFPROBE_PATH,
)


def _generate_test_media(duration_sec: float = 1) -> str:
    """
    生成一个测试用音频文件（不依赖系统文件）。
    返回文件路径，调用方负责删除。
    """
    if not check_ffmpeg_installed()[0]:
        raise RuntimeError("ffmpeg not available")

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    subprocess.run(
        [FFMPEG_PATH, "-y", "-f", "lavfi", "-i",
         f"sine=frequency=440:duration={duration_sec}",
         "-ar", "44100", path],
        capture_output=True, timeout=30, check=True,
    )
    return path


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
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(msg, str)

    def test_check_ffprobe(self):
        ok, msg = check_ffprobe_installed()
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(msg, str)


class TestFFprobeIntegration(unittest.TestCase):
    """FFprobe 集成测试（动态生成测试文件）"""

    @classmethod
    def setUpClass(cls):
        cls.ffprobe_ok, _ = check_ffprobe_installed()
        cls.ffmpeg_ok, _ = check_ffmpeg_installed()

    def test_get_media_info_nonexistent(self):
        if not self.ffprobe_ok:
            self.skipTest("ffprobe not available")
        with self.assertRaises(Exception):
            get_media_info("/nonexistent/file.mp4")

    def test_get_media_info_small_file(self):
        """测试 ffprobe 能解析生成的音频文件"""
        if not self.ffprobe_ok or not self.ffmpeg_ok:
            self.skipTest("ffmpeg/ffprobe not available")

        test_file = None
        try:
            test_file = _generate_test_media(0.5)
            info = get_media_info(test_file)
            self.assertIsInstance(info, MediaInfo)
            self.assertEqual(info.file_path, test_file)
            self.assertGreater(info.file_size, 0)
            self.assertIn(info.format_name, ["wav", "pcm_s16le"])
        finally:
            if test_file and os.path.isfile(test_file):
                os.unlink(test_file)


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

    def test_extract_audio_from_generated(self):
        """从生成的音频文件提取/转码为 MP3，验证输出文件存在且有内容"""
        if not self.ffmpeg_ok or not self.ffprobe_ok:
            self.skipTest("ffmpeg/ffprobe not available")

        src = None
        out_fd, out_path = tempfile.mkstemp(suffix=".mp3")
        os.close(out_fd)
        try:
            src = _generate_test_media(0.5)
            result = extract_audio(src, out_path)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
            self.assertTrue(os.path.isfile(out_path))
            self.assertGreater(os.path.getsize(out_path), 100,
                               "Output MP3 should have content")
        finally:
            if src and os.path.isfile(src):
                os.unlink(src)
            if os.path.isfile(out_path):
                os.unlink(out_path)


if __name__ == "__main__":
    unittest.main()
