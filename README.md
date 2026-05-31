# FFmpeg GUI — 视频处理桌面工具

一个基于 FFmpeg 的本地视频处理桌面客户端，提供友好的图形界面操作。

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![PySide6](https://img.shields.io/badge/PySide6-6.6+-green)
![FFmpeg](https://img.shields.io/badge/FFmpeg-required-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Windows](https://img.shields.io/badge/Platform-Windows-blue)
[![Download](https://img.shields.io/github/v/release/zhanglingfei112/ffmpeg-gui?label=Download)](https://github.com/zhanglingfei112/ffmpeg-gui/releases/latest)
[![Build](https://github.com/zhanglingfei112/ffmpeg-gui/actions/workflows/build-windows.yml/badge.svg)](https://github.com/zhanglingfei112/ffmpeg-gui/actions)

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 🔄 **格式转换** | MP4 / MKV / WebM / AVI / MOV / GIF 互转 |
| ✂️ **视频裁剪** | 按时间起止或时长截取片段 |
| 📎 **视频合并** | 多个视频文件合并为一个（需相同编码） |
| 🎵 **提取音频** | 从视频中提取 MP3 / WAV / AAC / FLAC / OGG 音频 |
| 🖼️ **提取帧** | 按频率提取视频帧为 JPG 图片 |
| 📉 **压缩视频** | CRF 模式控制文件大小（5 级预设） |
| 📐 **调整分辨率** | 内置常见分辨率预设 |
| ⏩ **变速播放** | 调整视频播放速度 |
| ℹ️ **媒体信息** | 查看视频/音频详细编码信息 |
| 📋 **批量处理** | 任务队列 + 并发控制 |

## 📥 安装

### 从 Release 下载（推荐）
前往 [Releases](https://github.com/zhanglingfei112/ffmpeg-gui/releases) 下载最新版 `FFmpegGUI-Windows.zip`，解压运行即可。

> ⚠️ 使用前需安装 FFmpeg：https://ffmpeg.org/download.html
> 或通过 winget 安装：`winget install FFmpeg`

### 从源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/zhanglingfei112/ffmpeg-gui.git
cd ffmpeg-gui

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python src/main.py
```

### 从源码构建 Windows .exe

```bash
pip install pyinstaller
python build.py
```

构建产物在 `dist/FFmpegGUI/` 目录。

## 🚀 使用指南

1. **启动程序**：运行 `FFmpegGUI.exe` 或 `python src/main.py`
2. **左侧导航**：点击功能图标切换到对应工具
3. **拖拽支持**：大部分 Tab 支持将视频文件拖拽到界面
4. **资源管理**：进入「设置」Tab 调整并发数和线程限制

### 转换示例

1. 点击「转换」Tab
2. 选择或拖拽输入文件
3. 选择输出格式（如 MP4 / WebM）
4. 选择压缩质量（建议：平衡）
5. 可选调整分辨率
6. 点击「开始转换」

## ⚙️ 资源调度

本应用注重资源管理，避免像其他 FFmpeg GUI 那样吃满系统资源：

- **并发控制**：默认 1 个任务同时运行，可在设置中调整
- **线程限制**：FFmpeg 线程数可配，避免 CPU 满载
- **任务队列**：排队处理，不抢占系统资源
- **进度反馈**：实时进度条 + 状态提示

## 🛠️ 技术栈

- **Python 3.11+**：核心开发语言
- **PySide6**：Qt for Python 6，跨平台 GUI 框架
- **FFmpeg/FFprobe**：底层视频处理引擎
- **PyInstaller**：打包为 Windows 可执行文件
- **GitHub Actions**：自动构建 + 发布

## 📁 项目结构

```
ffmpeg-gui/
├── src/
│   ├── main.py              # 入口
│   ├── app.py               # 应用配置
│   ├── core/
│   │   ├── ffmpeg_manager   # FFmpeg 核心功能
│   │   ├── task_queue.py    # 任务队列 & 资源调度
│   │   └── presets.py       # 格式预设
│   └── ui/
│       ├── theme.py         # 深色主题
│       ├── main_window.py   # 主窗口
│       └── tabs/            # 功能标签页
├── tests/                   # 单元测试
├── .github/workflows/       # CI 构建
└── build.py                 # 打包脚本
```

## 📄 许可证

本项目基于 MIT 许可证开源。FFmpeg 是其各自所有者的商标。
