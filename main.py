import json
import os
import subprocess
import threading
from queue import Queue
from tkinter import filedialog, BooleanVar
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledText, ScrolledFrame
import darkdetect

CONFIG_FILE = "config.json"
LIGHT_THEME = "flatly"
DARK_THEME = "darkly"

# (key, cli_flag, description, param_type, group)
PARAM_DEFS = [
    ("use-tv-api", "--use-tv-api", "使用TV端解析模式", "switch", "解析选项"),
    ("use-app-api", "--use-app-api", "使用APP端解析模式", "switch", "解析选项"),
    ("use-intl-api", "--use-intl-api", "使用国际版(东南亚视频)解析模式", "switch", "解析选项"),
    ("video-only", "--video-only", "仅下载视频", "switch", "下载控制"),
    ("audio-only", "--audio-only", "仅下载音频", "switch", "下载控制"),
    ("danmaku-only", "--danmaku-only", "仅下载弹幕", "switch", "下载控制"),
    ("sub-only", "--sub-only", "仅下载字幕", "switch", "下载控制"),
    ("cover-only", "--cover-only", "仅下载封面", "switch", "下载控制"),
    ("download-danmaku", "--download-danmaku", "下载弹幕", "switch", "下载控制"),
    ("skip-subtitle", "--skip-subtitle", "跳过字幕下载", "switch", "下载控制"),
    ("skip-cover", "--skip-cover", "跳过封面下载", "switch", "下载控制"),
    ("skip-mux", "--skip-mux", "跳过混流步骤", "switch", "下载控制"),
    ("skip-ai", "--skip-ai", "跳过AI字幕下载(默认开启)", "switch", "下载控制"),
    ("use-aria2c", "--use-aria2c", "调用aria2c进行下载(你需要自行准备好二进制可执行文件)", "switch", "下载优化"),
    ("multi-thread", "--multi-thread", "使用多线程下载(默认开启)", "switch", "下载优化"),
    ("force-http", "--force-http", "下载音视频时强制使用HTTP协议替换HTTPS(默认开启)", "switch", "下载优化"),
    ("force-replace-host", "--force-replace-host", "强制替换下载服务器host(默认开启)", "switch", "下载优化"),
    ("video-ascending", "--video-ascending", "视频升序(最小体积优先)", "switch", "下载优化"),
    ("audio-ascending", "--audio-ascending", "音频升序(最小体积优先)", "switch", "下载优化"),
    ("allow-pcdn", "--allow-pcdn", "不替换PCDN域名, 仅在正常情况与--upos-host均无法下载时使用", "switch", "下载优化"),
    ("hide-streams", "--hide-streams", "不要显示所有可用音视频流", "switch", "下载优化"),
    ("use-mp4box", "--use-mp4box", "使用MP4Box来混流", "switch", "混流与工具"),
    ("ffmpeg-path", "--ffmpeg-path", "设置ffmpeg的路径", "input", "混流与工具"),
    ("mp4box-path", "--mp4box-path", "设置mp4box的路径", "input", "混流与工具"),
    ("only-show-info", "--only-show-info", "仅解析而不进行下载", "switch", "信息显示"),
    ("show-all", "--show-all", "展示所有分P标题", "switch", "信息显示"),
    ("interactive", "--interactive", "交互式选择清晰度", "switch", "信息显示"),
    ("debug", "--debug", "输出调试日志", "switch", "信息显示"),
    ("file-pattern", "--file-pattern", "使用内置变量自定义单P存储文件名, 默认为 videoTitle", "input", "文件与命名"),
    ("multi-file-pattern", "--multi-file-pattern", "使用内置变量自定义多P存储文件名, 默认为 videoTitle[PpageNumberWithZero]pageTitle", "input", "文件与命名"),
    ("save-archives-to-file", "--save-archives-to-file", "将下载过的视频记录到本地文件中, 用于后续跳过下载同个视频", "switch", "文件与命名"),
    ("host", "--host", "指定BiliPlus host(使用BiliPlus需要access_token, 不需要cookie, 解析服务器能够获取你账号的大部分权限!)", "input", "网络与代理"),
    ("ep-host", "--ep-host", "指定BiliPlus EP host(用于代理api.bilibili.compgcviewwebseason, 大部分解析服务器不支持代理该接口)", "input", "网络与代理"),
    ("area", "--area", "(hktwth) 使用BiliPlus时必选, 指定BiliPlus area", "input", "网络与代理"),
    ("upos-host", "--upos-host", "自定义upos服务器", "input", "网络与代理"),
    ("cookie", "--cookie", "设置字符串cookie用以下载网页接口的会员内容", "input", "认证"),
    ("access-token", "--access-token", "设置access_token用以下载TVAPP接口的会员内容", "input", "认证"),
    ("user-agent", "--user-agent", "指定user-agent, 否则使用随机user-agent", "input", "认证"),
    ("encoding-priority", "--encoding-priority", "视频编码的选择优先级, 用逗号分割 例 hevc,av1,avc", "input", "其他参数"),
    ("dfn-priority", "--dfn-priority", "画质优先级,用逗号分隔 例 8K 超高清, 1080P 高码率, HDR 真彩, 杜比视界", "input", "其他参数"),
    ("select-page", "--select-page", "选择指定分p或分p范围 (-p 8 或 -p 1,2 或 -p 3-5 或 -p ALL 或 -p LAST 或 -p 3,5,LATEST)", "input", "其他参数"),
    ("language", "--language", "设置混流的音频语言(代码), 如chi, jpn等", "input", "其他参数"),
    ("aria2c-args", "--aria2c-args", "调用aria2c的附加参数(默认参数包含-x16 -s16 -j16 -k 5M, 使用时注意字符串转义)", "input", "其他参数"),
    ("delay-per-page", "--delay-per-page", "设置下载合集分P之间的下载间隔时间(单位 秒, 默认无间隔)", "input", "其他参数"),
    ("aria2c-path", "--aria2c-path", "设置aria2c的路径", "input", "其他参数"),
    ("config-file", "--config-file", "读取指定的BBDown本地配置文件(默认为 BBDown.config)", "input", "其他参数"),
]

BASIC_KEYS = {"video-only", "audio-only", "danmaku-only", "sub-only", "cover-only"}
BASIC_KEYS_LIST = ["video-only", "audio-only", "danmaku-only", "sub-only", "cover-only"]

DEFAULT_CONFIG = {
    "BinPath": "bin",
    "SavePath": "downloads",
    "theme": "system",
    "basic": {
        "video-only": False,
        "audio-only": False,
        "danmaku-only": False,
        "sub-only": False,
        "cover-only": False,
    },
    "advanced": {
        "use-tv-api": False,
        "use-app-api": False,
        "use-intl-api": False,
        "use-mp4box": False,
        "only-show-info": False,
        "show-all": False,
        "use-aria2c": False,
        "interactive": False,
        "hide-streams": False,
        "multi-thread": True,
        "debug": False,
        "skip-mux": False,
        "skip-subtitle": False,
        "skip-cover": False,
        "force-http": True,
        "download-danmaku": False,
        "skip-ai": True,
        "video-ascending": False,
        "audio-ascending": False,
        "allow-pcdn": False,
        "force-replace-host": True,
        "save-archives-to-file": False,
        "encoding-priority": "",
        "dfn-priority": "",
        "file-pattern": "",
        "multi-file-pattern": "",
        "select-page": "",
        "language": "",
        "user-agent": "",
        "cookie": "",
        "access-token": "",
        "aria2c-args": "",
        "ffmpeg-path": "",
        "mp4box-path": "",
        "aria2c-path": "",
        "upos-host": "",
        "delay-per-page": "",
        "host": "",
        "ep-host": "",
        "area": "",
        "config-file": "",
    }
}


class BBDownLauncher(ttk.Window):
    def __init__(self):
        self.config_data = self._load_config()
        theme = self.config_data.get("theme", "system")
        if theme == "system":
            self.is_dark = darkdetect.theme() == "Dark"
        else:
            self.is_dark = theme == "dark"
        initial_theme = DARK_THEME if self.is_dark else LIGHT_THEME

        super().__init__(
            title="BBDown Launcher",
            themename=initial_theme,
            minsize=(900, 700),
        )
        self.geometry("1000x800")

        self.process = None
        self.output_queue = Queue()
        self.is_running = False

        self.basic_vars = {}
        self.adv_vars = {}
        self.adv_entries = {}

        self._create_widgets()
        self.after(100, self._check_queue)

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(data)
                for k in DEFAULT_CONFIG:
                    if k not in merged:
                        merged[k] = DEFAULT_CONFIG[k]
                    elif isinstance(DEFAULT_CONFIG[k], dict):
                        for subk in DEFAULT_CONFIG[k]:
                            if subk not in merged[k]:
                                merged[k][subk] = DEFAULT_CONFIG[k][subk]
                return merged
            except Exception as e:
                print(f"加载配置失败: {e}")
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._append_log(f"保存配置失败: {e}\n")

    def _create_widgets(self):
        # ===== 标题区域 =====
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=X, padx=15, pady=(15, 0))

        ttk.Label(
            title_frame,
            font=("Microsoft YaHei", 20, "bold"),
        ).pack(anchor=W)
        ttk.Label(
            title_frame,
            text="简易 BBDown 下载启动器",
            font=("Microsoft YaHei", 11),
            foreground="#555555",
        ).pack(anchor=W, pady=(0, 5))

        ttk.Separator(self, bootstyle=SECONDARY).pack(fill=X, padx=15)

        # ===== 导航栏 =====
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=X, padx=15, pady=10)

        nav_left = ttk.Frame(nav_frame)
        nav_left.pack(side=LEFT)

        self.btn_basic = ttk.Button(
            nav_left,
            text="基本配置",
            bootstyle=PRIMARY,
            command=self._show_basic,
            width=12,
        )
        self.btn_basic.pack(side=LEFT, padx=(0, 5))

        self.btn_advanced = ttk.Button(
            nav_left,
            text="参数配置",
            bootstyle=OUTLINE,
            command=self._show_advanced,
            width=12,
        )
        self.btn_advanced.pack(side=LEFT, padx=5)

        nav_right = ttk.Frame(nav_frame)
        nav_right.pack(side=RIGHT)

        self.theme_btn_text = ttk.StringVar(
            value="亮色" if self.is_dark else "暗色"
        )
        ttk.Button(
            nav_right,
            textvariable=self.theme_btn_text,
            command=self._toggle_theme,
            bootstyle=SECONDARY,
            width=10,
        ).pack(side=LEFT, padx=5)

        self.start_btn = ttk.Button(
            nav_right,
            text="▶ 启动",
            command=self._start_download,
            bootstyle=SUCCESS,
            width=10,
        )
        self.start_btn.pack(side=LEFT, padx=5)

        self.stop_btn = ttk.Button(
            nav_right,
            text="停止",
            command=self._stop_process,
            bootstyle=DANGER,
            width=10,
            state=DISABLED,
        )
        self.stop_btn.pack(side=LEFT, padx=5)

        # ===== 内容区域（可切换） =====
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill=BOTH, expand=True, padx=15)

        # ===== 日志区域 =====
        self.log_frame = ttk.LabelFrame(self, text="运行日志")
        log_inner = ttk.Frame(self.log_frame, padding=5)
        log_inner.pack(fill=BOTH, expand=True)

        self.log_text = ScrolledText(
            log_inner,
            autohide=True,
            height=10,
            state=DISABLED,
            wrap="word",
            font=("Consolas", 10),
        )
        self.log_text.pack(fill=BOTH, expand=True)

        # ===== 底部命令区域 =====
        self.bottom_frame = ttk.Frame(self)

        self.cmd_entry = ttk.Entry(
            self.bottom_frame, bootstyle=SECONDARY
        )
        self.cmd_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        self.cmd_entry.bind("<Return>", lambda e: self._send_command())

        ttk.Button(
            self.bottom_frame,
            text="发送",
            command=self._send_command,
            bootstyle=PRIMARY,
            width=8,
        ).pack(side=LEFT, padx=5)

        self._create_basic_frame()
        self._create_advanced_frame()
        self._show_basic()

    def _create_basic_frame(self):
        self.basic_frame = ttk.Frame(self.content_frame)

        # ===== 路径行（左右平分） =====
        path_row = ttk.Frame(self.basic_frame)
        path_row.pack(fill=X, pady=(10, 0))
        path_row.columnconfigure(0, weight=1)
        path_row.columnconfigure(1, weight=1)

        # 左：BBDown 路径
        left_path = ttk.Frame(path_row)
        left_path.grid(row=0, column=0, sticky=EW, padx=(0, 10))
        ttk.Label(
            left_path, text="BBDown 路径", font=("Microsoft YaHei", 10, "bold")
        ).pack(anchor=W)
        row1 = ttk.Frame(left_path)
        row1.pack(fill=X, pady=5)
        self.binpath_entry = ttk.Entry(row1)
        self.binpath_entry.pack(side=LEFT, fill=X, expand=True)
        self.binpath_entry.insert(0, self.config_data.get("BinPath", "bin"))
        ttk.Button(
            row1,
            text="浏览...",
            command=lambda: self._browse_folder(self.binpath_entry),
            width=10,
        ).pack(side=LEFT, padx=(5, 0))

        # 右：保存路径
        right_path = ttk.Frame(path_row)
        right_path.grid(row=0, column=1, sticky=EW, padx=(10, 0))
        ttk.Label(
            right_path, text="保存路径", font=("Microsoft YaHei", 10, "bold")
        ).pack(anchor=W)
        row2 = ttk.Frame(right_path)
        row2.pack(fill=X, pady=5)
        self.savepath_entry = ttk.Entry(row2)
        self.savepath_entry.pack(side=LEFT, fill=X, expand=True)
        self.savepath_entry.insert(0, self.config_data.get("SavePath", "downloads"))
        ttk.Button(
            row2,
            text="浏览...",
            command=lambda: self._browse_folder(self.savepath_entry),
            width=10,
        ).pack(side=LEFT, padx=(5, 0))

        # ===== 内容行：视频链接 + 基本选项（左右平分） =====
        content_row = ttk.Frame(self.basic_frame)
        content_row.pack(fill=BOTH, expand=True, pady=10)
        content_row.columnconfigure(0, weight=1)
        content_row.columnconfigure(1, weight=1)
        content_row.rowconfigure(0, weight=1)

        # 左：视频链接
        left_content = ttk.Frame(content_row)
        left_content.grid(row=0, column=0, sticky=NSEW, padx=(0, 10))
        left_title = ttk.Frame(left_content)
        left_title.pack(fill=X)
        ttk.Label(
            left_title, text="视频链接", font=("Microsoft YaHei", 10, "bold")
        ).pack(side=LEFT)
        ttk.Label(
            left_title,
            text="支持多行，一行一个",
            font=("Microsoft YaHei", 9),
            foreground="#555555",
        ).pack(side=LEFT, padx=(5, 0))
        self.link_text = ttk.Text(left_content, height=5)
        self.link_text.pack(fill=BOTH, expand=True, pady=5)

        # 右：基本选项
        right_content = ttk.Frame(content_row)
        right_content.grid(row=0, column=1, sticky=NSEW, padx=(10, 0))
        right_title = ttk.Frame(right_content)
        right_title.pack(fill=X)
        ttk.Label(
            right_title, text="基本选项", font=("Microsoft YaHei", 10, "bold")
        ).pack(side=LEFT)
        ttk.Label(
            right_title,
            text="仅生效一个，不选则下载全部",
            font=("Microsoft YaHei", 9),
            foreground="#555555",
        ).pack(side=LEFT, padx=(5, 0))
        basic_group = ttk.LabelFrame(right_content, text="")
        basic_group.pack(fill=BOTH, expand=True, pady=5)
        basic_inner = ttk.Frame(basic_group, padding=10)
        basic_inner.pack(fill=BOTH, expand=True)
        basic_inner.columnconfigure(0, weight=1)
        basic_inner.columnconfigure(1, weight=1)

        for i, key in enumerate(BASIC_KEYS_LIST):
            desc = ""
            for p in PARAM_DEFS:
                if p[0] == key:
                    desc = p[2]
                    break
            var = BooleanVar(value=self.config_data["basic"].get(key, False))
            ttk.Checkbutton(
                basic_inner,
                text=desc,
                variable=var,
                bootstyle="round-toggle",
            ).grid(row=i // 2, column=i % 2, sticky=W, pady=4, padx=5)
            self.basic_vars[key] = var

        # 状态
        self.status_var = ttk.StringVar(value="状态: 就绪")
        ttk.Label(
            self.basic_frame,
            textvariable=self.status_var,
            font=("Microsoft YaHei", 9),
            foreground="#555555",
        ).pack(anchor=W, pady=(5, 0))

    def _create_advanced_frame(self):
        self.advanced_frame = ttk.Frame(self.content_frame)

        ttk.Label(
            self.advanced_frame,
            text="提示：开关参数勾选即启用；输入框留空表示不附加该参数。",
            font=("Microsoft YaHei", 9),
            foreground="#555555",
        ).pack(anchor=W, pady=(5, 5))

        scroll = ScrolledFrame(self.advanced_frame, autohide=True)
        scroll.pack(fill=BOTH, expand=True)

        groups = {}
        group_inners = {}
        for key, cli, desc, ptype, group in PARAM_DEFS:
            if key in BASIC_KEYS:
                continue
            if group not in groups:
                groups[group] = ttk.LabelFrame(scroll, text=group)
                groups[group].pack(fill=X, pady=5, padx=5)
                group_inners[group] = ttk.Frame(groups[group], padding=10)
                group_inners[group].pack(fill=X)

            item = ttk.Frame(group_inners[group])
            item.pack(fill=X, pady=4)
            item.columnconfigure(0, minsize=180)
            item.columnconfigure(1, weight=1)
            item.columnconfigure(2, minsize=80)

            # 参数标志
            ttk.Label(
                item,
                text=cli,
                font=("Consolas", 10),
                foreground="#555555",
            ).grid(row=0, column=0, sticky=W, padx=(0, 10), pady=(0, 2))

            if ptype == "switch":
                var = BooleanVar(
                    value=self.config_data["advanced"].get(key, False)
                )
                ttk.Checkbutton(
                    item, text="", variable=var, bootstyle="round-toggle"
                ).grid(row=0, column=2, sticky=E, pady=(0, 2))
                self.adv_vars[key] = var
            else:
                entry = ttk.Entry(item)
                entry.grid(row=0, column=1, columnspan=2, sticky=EW, pady=(0, 2))
                val = self.config_data["advanced"].get(key, "")
                if val:
                    entry.insert(0, str(val))
                self.adv_entries[key] = entry

            # 描述文字统一放在第二行
            ttk.Label(
                item,
                text=desc,
                font=("Microsoft YaHei", 9),
                foreground="#555555",
            ).grid(row=1, column=1, columnspan=2, sticky=W, pady=(2, 0))

    def _show_basic(self):
        self.advanced_frame.pack_forget()
        self.basic_frame.pack(fill=BOTH, expand=True)
        self.btn_basic.configure(bootstyle=PRIMARY)
        self.btn_advanced.configure(bootstyle=OUTLINE)
        self.log_frame.pack(fill=BOTH, expand=True, padx=15, pady=5)
        self.bottom_frame.pack(fill=X, padx=15, pady=(0, 15))

    def _show_advanced(self):
        self.basic_frame.pack_forget()
        self.advanced_frame.pack(fill=BOTH, expand=True)
        self.btn_advanced.configure(bootstyle=PRIMARY)
        self.btn_basic.configure(bootstyle=OUTLINE)
        self.log_frame.pack_forget()
        self.bottom_frame.pack_forget()

    def _browse_folder(self, entry):
        folder = filedialog.askdirectory()
        if folder:
            entry.delete(0, "end")
            entry.insert(0, folder)

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        new_theme = DARK_THEME if self.is_dark else LIGHT_THEME
        self.style.theme_use(new_theme)
        self.theme_btn_text.set("亮色" if self.is_dark else "暗色")
        self.config_data["theme"] = "dark" if self.is_dark else "light"
        self._save_config()

    def _append_log(self, text):
        self.log_text.configure(state=NORMAL)
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state=DISABLED)

    def _check_queue(self):
        while not self.output_queue.empty():
            text = self.output_queue.get()
            self._append_log(text)
        self.after(100, self._check_queue)

    def _collect_config(self):
        self.config_data["BinPath"] = self.binpath_entry.get().strip()
        self.config_data["SavePath"] = self.savepath_entry.get().strip()

        for key, var in self.basic_vars.items():
            self.config_data["basic"][key] = bool(var.get())

        for key, var in self.adv_vars.items():
            self.config_data["advanced"][key] = bool(var.get())

        for key, entry in self.adv_entries.items():
            self.config_data["advanced"][key] = entry.get().strip()

        self._save_config()

    def _build_args(self):
        args = []

        save_path = self.config_data.get("SavePath", "").strip()
        if save_path:
            args.extend(["--work-dir", save_path])

        for key, var in self.basic_vars.items():
            val = var.get()
            default = DEFAULT_CONFIG["basic"].get(key, False)
            if val != default and val:
                for p in PARAM_DEFS:
                    if p[0] == key:
                        args.append(p[1])
                        break

        for key, var in self.adv_vars.items():
            val = var.get()
            default = DEFAULT_CONFIG["advanced"].get(key, False)
            if val != default and val:
                for p in PARAM_DEFS:
                    if p[0] == key:
                        args.append(p[1])
                        break

        for key, entry in self.adv_entries.items():
            val = entry.get().strip()
            if val:
                for p in PARAM_DEFS:
                    if p[0] == key:
                        args.extend([p[1], val])
                        break

        return args

    def _start_download(self):
        if self.is_running:
            return

        self._show_basic()

        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except Exception:
                pass
            self.process = None

        self._collect_config()

        urls = self.link_text.get("1.0", "end").strip().splitlines()
        urls = [u.strip() for u in urls if u.strip()]

        if not urls:
            self._append_log("[错误] 请输入至少一个视频链接\n")
            return

        bin_path = self.config_data.get("BinPath", "bin").strip()
        bbdown_exe = os.path.join(bin_path, "BBDown.exe")
        if not os.path.exists(bbdown_exe):
            self._append_log(f"[错误] 未找到 BBDown.exe: {bbdown_exe}\n")
            return

        args = self._build_args()
        arg_str = " ".join(
            f'"{a}"' if " " in a else a for a in args
        )

        self.is_running = True
        self.start_btn.configure(state=DISABLED)
        self.stop_btn.configure(state=NORMAL)
        self.status_var.set("状态: 运行中")
        self._append_log("=" * 50 + "\n")
        self._append_log(f"开始下载，共 {len(urls)} 个链接\n")
        self._append_log("=" * 50 + "\n")

        try:
            self.process = subprocess.Popen(
                ["powershell.exe", "-NoExit", "-Command", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=bin_path,
            )
        except Exception as e:
            self._append_log(f"[错误] 启动PowerShell失败: {e}\n")
            self.is_running = False
            self.start_btn.configure(state=NORMAL)
            self.stop_btn.configure(state=DISABLED)
            self.status_var.set("状态: 就绪")
            return

        init_cmd = "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8\n"
        try:
            self.process.stdin.write(init_cmd.encode("utf-8"))
            self.process.stdin.flush()
        except Exception as e:
            self._append_log(f"[警告] 设置编码失败: {e}\n")

        for url in urls:
            if not self.is_running:
                break
            cmd = f'./BBDown.exe "{url}" {arg_str}\n'
            self._append_log(f"\n[系统] 正在处理: {url}\n")
            try:
                self.process.stdin.write(cmd.encode("utf-8"))
                self.process.stdin.flush()
            except Exception as e:
                self._append_log(f"[错误] 发送命令失败: {e}\n")
                break

        threading.Thread(target=self._read_output, daemon=True).start()

    def _read_output(self):
        try:
            while self.process and self.process.poll() is None:
                try:
                    line = self.process.stdout.readline()
                    if not line:
                        break
                    try:
                        text = line.decode("utf-8")
                    except UnicodeDecodeError:
                        text = line.decode("gbk", errors="replace")
                    self.output_queue.put(text)
                except Exception:
                    break
        except Exception as e:
            self.output_queue.put(f"\n[错误] 读取输出出错: {e}\n")
        finally:
            self.output_queue.put("\n[系统] 进程已结束\n")
            self.after(0, self._on_process_end)

    def _on_process_end(self):
        self.is_running = False
        self.start_btn.configure(state=NORMAL)
        self.stop_btn.configure(state=DISABLED)
        self.status_var.set("状态: 就绪")
        if self.process:
            try:
                self.process.stdout.close()
            except Exception:
                pass
            try:
                self.process.stdin.close()
            except Exception:
                pass
            self.process = None

    def _stop_process(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self._append_log("\n[系统] 已发送终止信号\n")
            except Exception as e:
                self._append_log(f"\n[错误] 终止进程失败: {e}\n")
        self.is_running = False
        self.start_btn.configure(state=NORMAL)
        self.stop_btn.configure(state=DISABLED)
        self.status_var.set("状态: 就绪")

    def _send_command(self):
        if not self.process or self.process.poll() is not None:
            self._append_log("[错误] PowerShell进程未运行\n")
            return

        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return

        self.cmd_entry.delete(0, "end")
        self._append_log(f"\n[命令] {cmd}\n")
        try:
            self.process.stdin.write((cmd + "\n").encode("utf-8"))
            self.process.stdin.flush()
        except Exception as e:
            self._append_log(f"[错误] 发送命令失败: {e}\n")


if __name__ == "__main__":
    app = BBDownLauncher()
    app.mainloop()
