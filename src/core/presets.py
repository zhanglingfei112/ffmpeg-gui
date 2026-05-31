"""
格式预设配置模块
定义常用输出格式、设备预设和压缩配置。
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FormatPreset:
    """格式预设"""
    name: str                # 显示名称
    extension: str           # 文件扩展名
    video_opts: str = ""     # 视频编码选项
    audio_opts: str = ""     # 音频编码选项
    extra_opts: str = ""     # 额外选项
    description: str = ""    # 描述


@dataclass
class QualityPreset:
    """质量预设"""
    name: str
    crf: int                 # H.264 CRF 值 (0-51, 越小质量越高)
    video_bitrate: str = ""  # 视频比特率 (可选, 替代 CRF)
    description: str = ""


# ======== 输出格式预设 ========

FORMAT_PRESETS: list[FormatPreset] = [
    FormatPreset(
        name="MP4 (H.264)",
        extension=".mp4",
        video_opts="-c:v libx264 -preset medium",
        audio_opts="-c:a aac -b:a 128k",
        description="通用兼容格式，适合大多数场景",
    ),
    FormatPreset(
        name="MP4 (H.265/HEVC)",
        extension=".mp4",
        video_opts="-c:v libx265 -preset medium",
        audio_opts="-c:a aac -b:a 128k",
        description="更高压缩率，文件更小，但兼容性略低",
    ),
    FormatPreset(
        name="WebM (VP9)",
        extension=".webm",
        video_opts="-c:v libvpx-vp9 -b:v 0 -crf 30 -pix_fmt yuv420p",
        audio_opts="-c:a libopus -b:a 96k",
        description="开放格式，适合网页播放",
    ),
    FormatPreset(
        name="AVI",
        extension=".avi",
        video_opts="-c:v mpeg4 -q:v 5",
        audio_opts="-c:a mp3 -b:a 192k",
        description="旧版兼容格式，文件较大",
    ),
    FormatPreset(
        name="MKV (H.264)",
        extension=".mkv",
        video_opts="-c:v libx264 -preset medium",
        audio_opts="-c:a aac -b:a 128k",
        description="开源容器格式，支持多音轨/字幕",
    ),
    FormatPreset(
        name="MOV (H.264)",
        extension=".mov",
        video_opts="-c:v libx264 -preset medium",
        audio_opts="-c:a aac -b:a 128k",
        description="Apple 生态兼容格式",
    ),
    FormatPreset(
        name="GIF",
        extension=".gif",
        video_opts="-vf fps=10,scale=480:-1:flags=lanczos",
        audio_opts="-an",
        extra_opts="-f gif",
        description="适合短片段动图",
    ),
]


# ======== 质量/压缩预设 ========

QUALITY_PRESETS: list[QualityPreset] = [
    QualityPreset(
        name="无损 / 最高质量",
        crf=17,
        description="接近无损，文件较大，适合存档",
    ),
    QualityPreset(
        name="高质量",
        crf=22,
        description="视觉无损，适合收藏和分享",
    ),
    QualityPreset(
        name="平衡 (推荐)",
        crf=28,
        description="大小与画质的最佳平衡",
    ),
    QualityPreset(
        name="小体积",
        crf=35,
        description="文件大幅缩小，适合快速网络分享",
    ),
    QualityPreset(
        name="极小体积",
        crf=40,
        description="体积最小，画质有损，适合预览",
    ),
]


# ======== 设备预设 ========

@dataclass
class DevicePreset:
    name: str
    width: int
    height: int
    description: str = ""


DEVICE_PRESETS: list[DevicePreset] = [
    DevicePreset(name="原始分辨率", width=0, height=0, description="保持原始尺寸"),
    DevicePreset(name="4K (3840×2160)", width=3840, height=2160),
    DevicePreset(name="1080p 全高清", width=1920, height=1080),
    DevicePreset(name="720p 高清", width=1280, height=720),
    DevicePreset(name="480p 标清", width=854, height=480),
    DevicePreset(name="360p", width=640, height=360),
    DevicePreset(name="手机竖屏 (1080×1920)", width=1080, height=1920),
    DevicePreset(name="手机竖屏 (720×1280)", width=720, height=1280),
]


def get_format_preset(name: str) -> Optional[FormatPreset]:
    """按名称查找格式预设"""
    for p in FORMAT_PRESETS:
        if p.name == name:
            return p
    return None


def get_quality_preset(name: str) -> Optional[QualityPreset]:
    """按名称查找质量预设"""
    for p in QUALITY_PRESETS:
        if p.name == name:
            return p
    return None
