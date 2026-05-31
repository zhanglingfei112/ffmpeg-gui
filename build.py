#!/usr/bin/env python3
"""
FFmpeg GUI 构建脚本 (PyInstaller)
用于打包 Windows 可执行文件。
"""

import os
import sys
import shutil
import subprocess


def build():
    """运行 PyInstaller 打包"""
    # 确保 PyInstaller 已安装
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("请先安装 PyInstaller: pip install pyinstaller")
        sys.exit(1)

    # 清理旧的构建
    for d in ["build", "dist"]:
        if os.path.isdir(d):
            shutil.rmtree(d)

    print("=== 开始打包 FFmpeg GUI ===")

    # 切换到项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    # 构建参数
    args = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "--name", "FFmpegGUI",
        "--windowed",
        "--icon", "NONE",
        "--add-data", f"src{os.pathsep}src",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "PySide6.QtGui",
        "src/main.py",
    ]

    cmd = " ".join(args)
    print(f"执行: {cmd}")
    try:
        ret = subprocess.run(cmd, shell=True, check=False)
        ret.check_returncode()
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败 (返回码 {e.returncode})")
        sys.exit(e.returncode)

    print("\n✅ 打包成功!")
    print(f"📁 输出目录: {os.path.join(project_root, 'dist', 'FFmpegGUI')}")
    print(f"📦 可执行文件: {os.path.join(project_root, 'dist', 'FFmpegGUI', 'FFmpegGUI.exe')}")


if __name__ == "__main__":
    build()
