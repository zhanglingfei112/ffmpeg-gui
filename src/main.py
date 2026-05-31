#!/usr/bin/env python3
"""
FFmpeg GUI — 视频处理桌面工具
入口脚本
"""

import sys
import os

# 确保 src 包可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import run

if __name__ == "__main__":
    run()
