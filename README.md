# EZ-BBDown-launcher

一个基于 Python + ttkbootstrap 的 BBDown 图形化启动器，将命令行操作封装为简洁的 GUI 界面，简化哔哩哔哩视频下载流程。

## 功能特点

- 图形化界面：直观的操作界面，无需记忆命令行参数
- 主题切换：支持亮色/暗色主题，自动跟随系统设置
- 批量下载：支持多行链接批量下载
- 基本配置：快速设置下载路径、下载类型（视频/音频/弹幕/字幕/封面）
- 高级参数：完整的 BBDown 命令行参数配置
- 配置持久化：所有设置自动保存到 config.json
- 实时日志：显示下载进度和运行状态
- 内置终端：可直接发送 PowerShell 命令

## 环境要求

- Windows 操作系统
- Python 3.8+
- BBDown.exe（放在 bin 目录下）
- ffmpeg.exe（可选，放在 bin 目录下）

## 安装依赖

```bash
pip install ttkbootstrap darkdetect
```

## 使用方法

### 方式一：直接运行 Python 脚本

1. 克隆或下载本项目
2. 将 BBDown.exe 放入 `bin` 目录
3. 运行程序：

```bash
python main.py
```

### 方式二：使用打包版本

1. 下载发布页面的 exe 文件
2. 将 BBDown.exe 放入与启动器同级的 `bin` 目录
3. 双击运行 EZ-BBDown-launcher.exe

### 打包命令

如需自行打包：

```bash
pip install pyinstaller
pyinstaller EZ-BBDown-launcher.spec
```

## 目录结构

```
EZ-BBDown-launcher/
├── main.py                 # 主程序
├── config.json             # 配置文件（自动生成）
├── EZ-BBDown-launcher.spec # PyInstaller 打包配置
├── ico/                    # 图标资源
│   ├── ico.ico
│   └── ico.png
├── LICENSE                 # Apache 2.0 许可证
└── README.md
```

## 配置说明

程序启动后会在同目录下生成 `config.json`，包含以下配置项：

- `BinPath`：BBDown 程序所在目录
- `SavePath`：视频保存目录
- `theme`：主题设置（system/light/dark）
- `basic`：基本下载选项
- `advanced`：高级参数配置

## 相关项目

- [BBDown](https://github.com/nilaoda/BBDown) - 哔哩哔哩命令行下载工具

## 许可证

本项目基于 [Apache License 2.0](LICENSE) 开源。

本README由MiMO攥写。