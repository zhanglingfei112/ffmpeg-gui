"""
FFmpeg 核心管理模块
负责 FFmpeg/FFprobe 子进程调用、进度解析、终止控制。
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


class FFprobeError(Exception):
    """FFprobe 调用失败"""
    pass


class FFmpegError(Exception):
    """FFmpeg 调用失败"""
    pass


class MediaInfo:
    """媒体文件元数据"""

    def __init__(self, data: dict):
        self.file_path = data.get("file_path", "")
        self.file_name = data.get("file_name", "")
        self.file_size = data.get("file_size", 0)
        self.duration = data.get("duration", 0.0)  # 秒
        self.video = data.get("video", {})
        self.audio = data.get("audio", {})
        self.format_name = data.get("format_name", "")

    @property
    def duration_str(self) -> str:
        """格式化为 HH:MM:SS.mmm"""
        if not self.duration:
            return "00:00:00.000"
        h, r = divmod(int(self.duration * 1000), 3600000)
        m, r = divmod(r, 60000)
        s, ms = divmod(r, 1000)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

    @property
    def file_size_str(self) -> str:
        """格式化为可读文件大小"""
        s = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if s < 1024:
                return f"{s:.1f} {unit}"
            s /= 1024
        return f"{s:.2f} TB"

    @property
    def bitrate_str(self) -> str:
        """格式化为可读比特率"""
        total = 0
        if self.video and self.video.get("bitrate"):
            total += self.video["bitrate"]
        if self.audio and self.audio.get("bitrate"):
            total += self.audio["bitrate"]
        if total > 0:
            if total >= 1000000:
                return f"{total / 1000000:.0f} Mbps"
            return f"{total // 1000} kbps"
        return "未知"

    def __str__(self) -> str:
        lines = [
            f"📁 {self.file_name}",
            f"📏 大小: {self.file_size_str}",
            f"⏱ 时长: {self.duration_str}",
            f"🎬 视频: {self.video.get('codec', 'N/A')} "
            f"{self.video.get('width', '?')}x{self.video.get('height', '?')} "
            f"{self.video.get('fps', '?')}fps",
            f"🔊 音频: {self.audio.get('codec', 'N/A')} "
            f"{self.audio.get('sample_rate', '?')}Hz "
            f"{self.audio.get('channels', '?')}ch",
        ]
        return "\n".join(lines)


def _find_ffmpeg() -> str:
    """查找系统 FFmpeg 路径"""
    for name in ["ffmpeg", "ffmpeg.exe"]:
        try:
            r = subprocess.run([name, "-version"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return name
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    # 常见安装路径
    common_paths = [
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "C:\\ffmpeg\\bin\\ffmpeg.exe",
        "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p
    return "ffmpeg"  # 默认，让系统找


def _find_ffprobe() -> str:
    """查找系统 FFprobe 路径"""
    for name in ["ffprobe", "ffprobe.exe"]:
        try:
            r = subprocess.run([name, "-version"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return name
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    common_paths = [
        "/usr/bin/ffprobe",
        "/usr/local/bin/ffprobe",
        "C:\\ffmpeg\\bin\\ffprobe.exe",
        "C:\\Program Files\\ffmpeg\\bin\\ffprobe.exe",
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p
    return "ffprobe"


FFMPEG_PATH = _find_ffmpeg()
FFPROBE_PATH = _find_ffprobe()


# ---------- FFprobe ----------

def get_media_info(file_path: str) -> MediaInfo:
    """用 FFprobe 提取媒体文件元数据"""
    if not os.path.isfile(file_path):
        raise FFprobeError(f"文件不存在: {file_path}")

    cmd = [
        FFPROBE_PATH,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise FFprobeError(f"ffprobe 返回错误: {r.stderr[:200]}")
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise FFprobeError(f"ffprobe 输出解析失败: {e}")
    except subprocess.TimeoutExpired:
        raise FFprobeError("ffprobe 超时")
    except FileNotFoundError:
        raise FFprobeError(f"找不到 ffprobe，请确认 FFmpeg 已安装")

    fmt = data.get("format", {})
    video_info = {}
    audio_info = {}

    for stream in data.get("streams", []):
        codec_type = stream.get("codec_type")
        if codec_type == "video" and not video_info:
            video_info = {
                "codec": stream.get("codec_name", ""),
                "width": stream.get("width", 0),
                "height": stream.get("height", 0),
                "fps": _parse_fps(stream),
                "bitrate": int(stream.get("bit_rate", 0) or 0),
                "pixel_format": stream.get("pix_fmt", ""),
            }
        elif codec_type == "audio" and not audio_info:
            audio_info = {
                "codec": stream.get("codec_name", ""),
                "sample_rate": int(stream.get("sample_rate", 0) or 0),
                "channels": stream.get("channels", 0),
                "bitrate": int(stream.get("bit_rate", 0) or 0),
            }

    duration = float(fmt.get("duration", 0) or 0)
    return MediaInfo({
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "file_size": os.path.getsize(file_path),
        "duration": duration,
        "video": video_info,
        "audio": audio_info,
        "format_name": fmt.get("format_name", ""),
    })


def _parse_fps(stream: dict) -> float:
    """解析帧率，优先 avg_frame_rate"""
    for key in ["avg_frame_rate", "r_frame_rate"]:
        val = stream.get(key, "0/0")
        if "/" in val:
            try:
                num, den = val.split("/")
                if int(den) > 0:
                    return round(int(num) / int(den), 2)
            except (ValueError, ZeroDivisionError):
                continue
        elif val:
            try:
                return float(val)
            except ValueError:
                continue
    return 0.0


# ---------- FFmpeg ----------

_FFMPEG_COMMON_OPTIONS = [
    "-y",  # 覆盖输出文件
    "-hide_banner",
]


def _run_ffmpeg(args: list[str], duration: float = 0.0,
                progress_callback=None, log_callback=None,
                thread_count: int = 0) -> str:
    """
    运行 FFmpeg 命令并返回 stderr 输出。
    - args: ffmpeg 参数字符串列表（不含程序名）
    - duration: 视频总时长（秒），用于进度计算
    - progress_callback(percent): 进度回调
    - log_callback(line): 实时日志回调
    - thread_count: 限制线程数（0=不限制）
    """
    cmd = [FFMPEG_PATH] + _FFMPEG_COMMON_OPTIONS
    if thread_count > 0:
        cmd += ["-threads", str(thread_count)]
    cmd += args

    try:
        # 设置进程优先级：低优先级运行，不抢占系统资源
        prio_kwargs = {}
        if sys.platform == "win32":
            # Windows: BELOW_NORMAL_PRIORITY_CLASS (0x4000)
            prio_kwargs["creationflags"] = 0x4000
        else:
            # Linux/macOS: 增加 nice 值（更低优先级）
            def lower_prio():
                os.nice(10)
            prio_kwargs["preexec_fn"] = lower_prio

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            **prio_kwargs,
        )
    except FileNotFoundError:
        raise FFmpegError(f"找不到 ffmpeg，请确认 FFmpeg 已安装")
    except Exception as e:
        raise FFmpegError(f"启动 ffmpeg 失败: {e}")

    stderr_output = []
    time_pattern = re.compile(r"time=(\d+):(\d+):(\d+)\.(\d+)")
    time_pattern2 = re.compile(r"time=(\d+\.\d+)")

    # 逐行实时读取 stderr
    # 使用 stderr 的流式读取
    if proc.stderr:
        for line in iter(proc.stderr.readline, ""):
            stderr_output.append(line)
            if log_callback:
                log_callback(line.rstrip("\n"))

            if progress_callback and duration > 0:
                m = time_pattern.search(line)
                if m:
                    h, m_, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
                    current = h * 3600 + m_ * 60 + s + ms / 100
                    pct = min(current / duration * 100, 99.9)
                    progress_callback(round(pct, 1))
                else:
                    m2 = time_pattern2.search(line)
                    if m2:
                        current = float(m2.group(1))
                        pct = min(current / duration * 100, 99.9)
                        progress_callback(round(pct, 1))
            elif progress_callback:
                # 无法计算进度时，发送模糊进度
                progress_callback(50.0)

    proc.wait()

    if proc.returncode != 0:
        # 在某些情况下 ffmpeg 虽然完成了但仍有非零返回
        stderr_text = "".join(stderr_output[-50:])
        # 检查是否是 "already exists" 等非致命错误
        if "already exists" in stderr_text:
            raise FFmpegError(f"输出文件已存在: {args[-1]}")
        raise FFmpegError(f"FFmpeg 退出码 {proc.returncode}\n{stderr_text[:500]}")

    if progress_callback:
        progress_callback(100.0)

    return "".join(stderr_output)


# ---------- 高级 API ----------

def convert_file(
    input_path: str,
    output_path: str,
    preset: Optional[dict] = None,
    progress_callback=None,
    log_callback=None,
    thread_count: int = 0,
) -> str:
    """格式转换 + 压缩"""
    info = get_media_info(input_path)
    args = ["-i", input_path]

    if preset:
        video_opts = preset.get("video_opts", "")
        audio_opts = preset.get("audio_opts", "")
        extra_opts = preset.get("extra_opts", "")
        if video_opts:
            args += video_opts.split()
        if audio_opts:
            args += audio_opts.split()
        if extra_opts:
            args += extra_opts.split()
    else:
        args += ["-c:v", "libx264", "-preset", "medium", "-c:a", "aac"]

    args.append(output_path)
    return _run_ffmpeg(args, info.duration, progress_callback, log_callback, thread_count)


def trim_video(
    input_path: str,
    output_path: str,
    start_time: str,
    duration: Optional[str] = None,
    end_time: Optional[str] = None,
    progress_callback=None,
    log_callback=None,
    thread_count: int = 0,
) -> str:
    """裁剪视频"""
    info = get_media_info(input_path)
    args = ["-i", input_path, "-ss", start_time]

    if duration:
        args += ["-t", duration]
    elif end_time:
        args += ["-to", end_time]

    # 精确裁剪 + 流复制模式
    args += ["-c", "copy", "-avoid_negative_ts", "make_zero"]
    args.append(output_path)

    # 裁剪的进度计算：取实际输出时长
    target_dur = 0.0
    if duration:
        target_dur = _parse_time_str(duration)
    elif end_time:
        target_dur = _parse_time_str(end_time) - _parse_time_str(start_time)
    else:
        target_dur = info.duration - _parse_time_str(start_time)
    if target_dur <= 0:
        target_dur = info.duration

    return _run_ffmpeg(args, target_dur, progress_callback, log_callback, thread_count)


def merge_videos(
    input_paths: list[str],
    output_path: str,
    progress_callback=None,
    log_callback=None,
    thread_count: int = 0,
) -> str:
    """合并多个视频（concat demuxer）"""
    total_duration = 0.0

    # 创建临时文件列表
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        filelist_path = f.name
        for p in input_paths:
            safe_path = Path(p).as_posix().replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")
            try:
                info = get_media_info(p)
                total_duration += info.duration
            except FFprobeError:
                pass

    try:
        args = [
            "-f", "concat",
            "-safe", "0",
            "-i", filelist_path,
            "-c", "copy",
            output_path,
        ]
        return _run_ffmpeg(args, total_duration, progress_callback, log_callback, thread_count)
    finally:
        try:
            os.unlink(filelist_path)
        except OSError:
            pass


def extract_audio(
    input_path: str,
    output_path: str,
    progress_callback=None,
    log_callback=None,
    thread_count: int = 0,
) -> str:
    """提取音频"""
    info = get_media_info(input_path)
    ext = Path(output_path).suffix.lower()
    args = ["-i", input_path, "-vn"]

    if ext == ".mp3":
        args += ["-c:a", "libmp3lame", "-q:a", "2"]
    elif ext == ".wav":
        args += ["-c:a", "pcm_s16le"]
    elif ext == ".aac":
        args += ["-c:a", "aac"]
    elif ext == ".flac":
        args += ["-c:a", "flac"]
    elif ext == ".ogg":
        args += ["-c:a", "libvorbis"]
    else:
        args += ["-c:a", "copy"]

    args.append(output_path)
    return _run_ffmpeg(args, info.duration, progress_callback, log_callback, thread_count)


def extract_frames(
    input_path: str,
    output_dir: str,
    fps: float = 1.0,
    quality: int = 3,
    progress_callback=None,
    log_callback=None,
    thread_count: int = 0,
) -> str:
    """提取帧为图片"""
    info = get_media_info(input_path)
    os.makedirs(output_dir, exist_ok=True)
    output_pattern = os.path.join(output_dir, "frame_%05d.jpg")

    args = [
        "-i", input_path,
        "-vf", f"fps={fps}",
        "-q:v", str(quality),
        output_pattern,
    ]
    return _run_ffmpeg(args, info.duration, progress_callback, log_callback, thread_count)


def change_speed(
    input_path: str,
    output_path: str,
    speed: float = 1.0,
    progress_callback=None,
    log_callback=None,
    thread_count: int = 0,
) -> str:
    """改变视频播放速度"""
    if speed <= 0:
        raise FFmpegError("速度必须大于 0")

    info = get_media_info(input_path)
    atempo = f"atempo={speed:.2f}"
    setpts = f"setpts={1/speed:.4f}*PTS"

    args = [
        "-i", input_path,
        "-vf", setpts,
        "-af", atempo,
        output_path,
    ]
    return _run_ffmpeg(args, info.duration / speed, progress_callback, log_callback, thread_count)


def change_resolution(
    input_path: str,
    output_path: str,
    width: int,
    height: int,
    progress_callback=None,
    log_callback=None,
    thread_count: int = 0,
) -> str:
    """改变分辨率"""
    info = get_media_info(input_path)
    args = [
        "-i", input_path,
        "-vf", f"scale={width}:{height}",
        "-c:a", "copy",
        output_path,
    ]
    return _run_ffmpeg(args, info.duration, progress_callback, log_callback, thread_count)


def compress_video(
    input_path: str,
    output_path: str,
    crf: int = 28,
    progress_callback=None,
    log_callback=None,
    thread_count: int = 0,
) -> str:
    """压缩视频（CRF 模式）"""
    info = get_media_info(input_path)
    args = [
        "-i", input_path,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", str(crf),
        "-c:a", "aac",
        "-b:a", "128k",
        output_path,
    ]
    return _run_ffmpeg(args, info.duration, progress_callback, log_callback, thread_count)


# ---------- 工具函数 ----------

def _parse_time_str(t: str) -> float:
    """解析时间字符串 'HH:MM:SS.mmm' → 秒数"""
    try:
        parts = t.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        else:
            return float(parts[0])
    except (ValueError, IndexError, TypeError):
        return 0.0


def check_ffmpeg_installed() -> tuple[bool, str]:
    """检查 FFmpeg 是否可用"""
    try:
        r = subprocess.run([FFMPEG_PATH, "-version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            version_line = r.stdout.split("\n")[0] if r.stdout else "版本信息未知"
            return True, version_line
        return False, f"ffmpeg 返回错误码 {r.returncode}"
    except FileNotFoundError:
        return False, f"找不到 ffmpeg（已搜索: {FFMPEG_PATH}）"
    except subprocess.TimeoutExpired:
        return False, "ffmpeg 检查超时"
    except Exception as e:
        return False, str(e)


def check_ffprobe_installed() -> tuple[bool, str]:
    """检查 FFprobe 是否可用"""
    try:
        r = subprocess.run([FFPROBE_PATH, "-version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            version_line = r.stdout.split("\n")[0] if r.stdout else "版本信息未知"
            return True, version_line
        return False, f"ffprobe 返回错误码 {r.returncode}"
    except FileNotFoundError:
        return False, f"找不到 ffprobe（已搜索: {FFPROBE_PATH}）"
    except subprocess.TimeoutExpired:
        return False, "ffprobe 检查超时"
    except Exception as e:
        return False, str(e)
