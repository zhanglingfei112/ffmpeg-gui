"""
FFmpeg 自动下载/安装模块
支持 Windows 自动下载解压，Linux/macOS 提供安装指引。
"""

import os
import sys
import platform
import shutil
import tempfile
import urllib.request
import zipfile
import json
from pathlib import Path
from typing import Optional, Callable


SYSTEM = platform.system().lower()
IS_WINDOWS = SYSTEM == "windows"
IS_MACOS = SYSTEM == "darwin"
IS_LINUX = SYSTEM == "linux"
IS_64BIT = sys.maxsize > 2**32


# 下载地址（Windows）
FFMPEG_WIN_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
FFMPEG_MIRROR_URL = "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip"


def get_app_dir() -> Path:
    """获取应用数据目录"""
    if IS_WINDOWS:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".local" / "share"
    return base / "ffmpeg-gui"


def get_ffmpeg_dir() -> Path:
    """获取 FFmpeg 安装目录"""
    return get_app_dir() / "ffmpeg"


def _progress_callback_download(chunks_done: int, chunk_size: int, total_size: int,
                                 progress_fn: Optional[Callable[[int], None]] = None):
    """下载进度回调"""
    if total_size > 0 and progress_fn:
        downloaded = chunks_done * chunk_size
        pct = min(int(downloaded / total_size * 100), 99)
        progress_fn(pct)


def download_ffmpeg_zip(dest_dir: Path,
                        progress_callback: Optional[Callable[[int], None]] = None,
                        log_callback: Optional[Callable[[str], None]] = None) -> str:
    """下载 FFmpeg zip 包，返回 zip 路径"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / "ffmpeg.zip"

    if log_callback:
        log_callback("正在连接下载服务器...")

    # 尝试主地址 + 备用地址
    urls = [FFMPEG_WIN_URL, FFMPEG_MIRROR_URL]
    last_error = None

    for url in urls:
        try:
            if log_callback:
                log_callback(f"下载: {url}")

            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })

            with urllib.request.urlopen(req, timeout=120) as response:
                total = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 8192

                with open(zip_path, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total > 0:
                            pct = int(downloaded / total * 100)
                            progress_callback(min(pct, 99))

            if zip_path.stat().st_size > 1000000:  # 至少 1MB
                if log_callback:
                    log_callback(f"下载完成: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
                return str(zip_path)
            else:
                last_error = f"文件过小: {zip_path.stat().st_size} bytes"
                zip_path.unlink(missing_ok=True)

        except Exception as e:
            last_error = str(e)
            zip_path.unlink(missing_ok=True)
            if log_callback:
                log_callback(f"下载失败: {e}")
            continue

    raise RuntimeError(f"所有下载地址均失败: {last_error}")


def extract_ffmpeg(zip_path: str, dest_dir: Path,
                   progress_callback: Optional[Callable[[int], None]] = None,
                   log_callback: Optional[Callable[[str], None]] = None) -> tuple[str, str]:
    """解压 FFmpeg zip，返回 (ffmpeg_path, ffprobe_path)"""
    if log_callback:
        log_callback("正在解压...")

    # 清空旧目录
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        total = len(zf.infolist())
        for i, entry in enumerate(zf.infolist()):
            zf.extract(entry, dest_dir)
            if progress_callback and total > 0:
                pct = int((i + 1) / total * 90)  # 解压进度 0-90%
                progress_callback(pct)

    if progress_callback:
        progress_callback(95)

    # 查找 ffmpeg.exe / ffmpeg
    ffmpeg_path = None
    ffprobe_path = None

    for root, dirs, files in os.walk(dest_dir):
        for f in files:
            if f in ("ffmpeg.exe", "ffmpeg") and not ffmpeg_path:
                ffmpeg_path = os.path.join(root, f)
            elif f in ("ffprobe.exe", "ffprobe") and not ffprobe_path:
                ffprobe_path = os.path.join(root, f)

    if not ffmpeg_path or not ffprobe_path:
        raise RuntimeError(f"解压后未找到 FFmpeg 可执行文件 (查找路径: {dest_dir})")

    # 复制到 ffmpeg_dir 根目录
    for src, name in [(ffmpeg_path, "ffmpeg.exe" if IS_WINDOWS else "ffmpeg"),
                      (ffprobe_path, "ffprobe.exe" if IS_WINDOWS else "ffprobe")]:
        dst = dest_dir / name
        shutil.copy2(src, dst)
        # 设置可执行权限
        dst.chmod(dst.stat().st_mode | 0o111)

    if progress_callback:
        progress_callback(100)

    if log_callback:
        log_callback(f"FFmpeg 安装到: {dest_dir}")

    # 返回路径
    ffmpeg_exe = str(dest_dir / ("ffmpeg.exe" if IS_WINDOWS else "ffmpeg"))
    ffprobe_exe = str(dest_dir / ("ffprobe.exe" if IS_WINDOWS else "ffprobe"))
    return ffmpeg_exe, ffprobe_exe


def auto_install_ffmpeg(
    progress_callback: Optional[Callable[[int], None]] = None,
    log_callback: Optional[Callable[[str], None]] = None,
) -> tuple[bool, str, str]:
    """
    自动下载安装 FFmpeg。
    返回: (success, ffmpeg_path, ffprobe_path)
    """
    if not IS_WINDOWS:
        return False, "", ""

    if log_callback:
        log_callback("开始自动安装 FFmpeg...")

    try:
        dest_dir = get_ffmpeg_dir()
        zip_path = download_ffmpeg_zip(dest_dir, progress_callback, log_callback)
        ffmpeg_path, ffprobe_path = extract_ffmpeg(zip_path, dest_dir, progress_callback, log_callback)

        # 清理 zip
        os.unlink(zip_path)

        # 验证
        import subprocess
        r = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            if log_callback:
                version_line = r.stdout.split("\n")[0] if r.stdout else ""
                log_callback(f"安装验证通过: {version_line[:60]}")
            return True, ffmpeg_path, ffprobe_path
        else:
            raise RuntimeError(f"安装后验证失败 (返回码 {r.returncode})")

    except Exception as e:
        if log_callback:
            log_callback(f"安装失败: {e}")
        return False, "", ""


def get_install_instructions() -> str:
    """获取针对当前平台的安装指引"""
    if IS_WINDOWS:
        return "https://ffmpeg.org/download.html"
    elif IS_MACOS:
        return "https://ffmpeg.org/download.html\n或使用 Homebrew: brew install ffmpeg"
    elif IS_LINUX:
        dist = ""
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        dist = line.split("=")[1].strip().strip('"')
                        break
        except Exception:
            dist = "linux"

        cmds = {
            "ubuntu": "sudo apt install ffmpeg",
            "debian": "sudo apt install ffmpeg",
            "centos": "sudo yum install ffmpeg",
            "rhel": "sudo yum install ffmpeg",
            "fedora": "sudo dnf install ffmpeg",
            "arch": "sudo pacman -S ffmpeg",
            "manjaro": "sudo pacman -S ffmpeg",
            "opensuse": "sudo zypper install ffmpeg",
        }
        cmd = cmds.get(dist, "使用系统包管理器安装 ffmpeg")
        return f"https://ffmpeg.org/download.html\n\n或使用包管理器安装:\n{cmd}"
    return "https://ffmpeg.org/download.html"
