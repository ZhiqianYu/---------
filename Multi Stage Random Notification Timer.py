import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox
import time
import random
import os
import json
import pygame
import threading

class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多阶段随机提醒计时器 @ZhiqianYu")
        self.root.geometry("480x425")
        self.root.resizable(False, False)

        # 定义统一字体，设置所有默认字体为 Segoe UI (win)
        self.default_font = tkfont.Font(family="Segoe UI", size=10)
        self.large_font = tkfont.Font(family="Segoe UI", size=24, weight="bold")
        self.mid_font = tkfont.Font(family="Segoe UI", size=12)
        self.root.option_add("*Font", self.default_font)

        # 初始化pygame用于音频播放
        pygame.mixer.init()
        self.audio_cache = {}  # 缓存音频对象

        
        # 默认设置
        self.config = {
            "total_time": {"hours": 8, "minutes": 0, "seconds": 0},
            "stage_time": {"hours": 1, "minutes": 30, "seconds": 0},
            "random_reminder": {"min": 5, "max": 10},
            "short_break": {"minutes": 0, "seconds": 10},
            "stage_break": {"minutes": 10, "seconds": 20},
            "sounds": {
                "start": "",
                "random": [],
                "stage_break_start": "",
                "total_end": ""
            }
        }
        
        # 初始化控件变量
        self.total_hours = tk.StringVar()
        self.total_minutes = tk.StringVar()
        self.total_seconds = tk.StringVar()
        self.stage_hours = tk.StringVar()
        self.stage_minutes = tk.StringVar()
        self.stage_seconds = tk.StringVar()
        self.random_min = tk.StringVar()
        self.random_max = tk.StringVar()
        self.short_break_minutes = tk.StringVar()
        self.short_break_seconds = tk.StringVar()
        self.stage_break_minutes = tk.StringVar()
        self.stage_break_seconds = tk.StringVar()
        self.main_button_state = "ready"  # 可选值: ready, running, paused
        
        # 初始化计时器状态
        self.timer_running = False
        self.paused = False
        
        # 创建目录
        self.create_directories()
        
        # 设置用户界面
        self.setup_ui()
        
        # 加载配置
        self.load_config()
    
    def create_directories(self):
        """创建音频文件夹"""
        # 创建主 notification 文件夹
        os.makedirs("notification", exist_ok=True)
        
        # 创建子文件夹
        directories = ["notis", "pause"]
        for directory in directories:
            os.makedirs(os.path.join("notification", directory), exist_ok=True)
    
    def load_config(self):
        """加载配置文件"""
        try:
            CONFIG_FILE = "config.json"  # Define the configuration file path
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
        
            # 应用时间设置到界面控件
            self.total_hours.set(self.config["total_time"]["hours"])
            self.total_minutes.set(self.config["total_time"]["minutes"])
            self.total_seconds.set(self.config["total_time"]["seconds"])
            
            self.stage_hours.set(self.config["stage_time"]["hours"])
            self.stage_minutes.set(self.config["stage_time"]["minutes"])
            self.stage_seconds.set(self.config["stage_time"]["seconds"])
            
            self.random_min.set(self.config["random_reminder"]["min"])
            self.random_max.set(self.config["random_reminder"]["max"])
            
            self.short_break_minutes.set(self.config["short_break"]["minutes"])
            self.short_break_seconds.set(self.config["short_break"]["seconds"])
            
            self.stage_break_minutes.set(self.config["stage_break"]["minutes"])
            self.stage_break_seconds.set(self.config["stage_break"]["seconds"])
            
            # 确保音频设置也被加载
            if "sounds" in self.config:
                self.sound_vars = self.config["sounds"]
        except Exception as e:
            messagebox.showerror("错误", f"加载配置文件失败: {str(e)}")
    
    def save_config(self):
        """保存配置到文件（仅当内容变化时）"""
        try:
            CONFIG_FILE = "config.json"
            new_config = json.dumps(self.config, ensure_ascii=False, indent=4)

            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    current = f.read()
                    if current.strip() == new_config.strip():
                        print("配置无变化，跳过保存")
                        return  # 无需保存

            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(new_config)
            print("配置文件已成功保存！")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置文件失败: {str(e)}")

    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架分为上下两部分
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=5, pady=0)
        
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.BOTH, padx=5, pady=0)
        
        # 上半部分：时间设置
        self.setup_time_settings(top_frame)
        
        # 下半部分：计时器和进度条
        self.setup_timer_display(bottom_frame)
        
        # 控制按钮
        self.setup_control_buttons(bottom_frame)
    
    def setup_time_settings(self, parent):
        """设置时间配置部分"""
        settings_frame = ttk.Frame(parent)
        settings_frame.pack(fill=tk.BOTH, pady=5, expand=True)
        
        # 左右布局
        left_frame = ttk.Frame(settings_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        right_frame = ttk.Frame(settings_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # 左边：总时间、阶段时间、随机提醒时间
        total_frame = ttk.LabelFrame(left_frame, text="总时间设置", padding=0, labelanchor="nw")
        total_frame.pack(fill=tk.BOTH, pady=0)
        
        ttk.Label(total_frame).grid(row=0, column=0, padx=5, pady=5)
        ttk.Spinbox(total_frame, from_=0, to=23, width=3, textvariable=self.total_hours).grid(row=0, column=1, padx=2)
        ttk.Label(total_frame, text="小时").grid(row=0, column=2, padx=2)
        ttk.Spinbox(total_frame, from_=0, to=59, width=3, textvariable=self.total_minutes).grid(row=0, column=3, padx=2)
        ttk.Label(total_frame, text="分钟").grid(row=0, column=4, padx=2)
        ttk.Spinbox(total_frame, from_=0, to=59, width=3, textvariable=self.total_seconds).grid(row=0, column=5, padx=2)
        ttk.Label(total_frame, text="秒").grid(row=0, column=6, padx=2)
        
        stage_frame = ttk.LabelFrame(left_frame, text="阶段时间设置", padding=0, labelanchor="nw")
        stage_frame.pack(fill=tk.BOTH, pady=2)
        
        ttk.Label(stage_frame).grid(row=0, column=0, padx=5, pady=5)
        ttk.Spinbox(stage_frame, from_=0, to=23, width=3, textvariable=self.stage_hours).grid(row=0, column=1, padx=2)
        ttk.Label(stage_frame, text="小时").grid(row=0, column=2, padx=2)
        ttk.Spinbox(stage_frame, from_=0, to=59, width=3, textvariable=self.stage_minutes).grid(row=0, column=3, padx=2)
        ttk.Label(stage_frame, text="分钟").grid(row=0, column=4, padx=2)
        ttk.Spinbox(stage_frame, from_=0, to=59, width=3, textvariable=self.stage_seconds).grid(row=0, column=5, padx=2)
        ttk.Label(stage_frame, text="秒").grid(row=0, column=6, padx=2)
        
        random_frame = ttk.LabelFrame(left_frame, text="随机提醒时间", padding=0, labelanchor="nw")
        random_frame.pack(fill=tk.BOTH, pady=2)
        
        ttk.Label(random_frame).grid(row=0, column=0, padx=5, pady=5)
        ttk.Spinbox(random_frame, from_=1, to=60, width=3, textvariable=self.random_min).grid(row=0, column=1, padx=2)
        ttk.Label(random_frame, text="-").grid(row=0, column=2, padx=2)
        ttk.Spinbox(random_frame, from_=1, to=60, width=3, textvariable=self.random_max).grid(row=0, column=3, padx=2)
        ttk.Label(random_frame, text="分钟").grid(row=0, column=4, padx=2)
        
        # 右边：短休息时间、阶段休息时间、提示音设置按钮
        short_break_frame = ttk.LabelFrame(right_frame, text="短休息时间", padding=0, labelanchor="nw")
        short_break_frame.pack(fill=tk.BOTH, pady=0)
        
        ttk.Label(short_break_frame).grid(row=0, column=0, padx=5, pady=5)
        ttk.Spinbox(short_break_frame, from_=0, to=59, width=3, textvariable=self.short_break_minutes).grid(row=0, column=1, padx=2)
        ttk.Label(short_break_frame, text="分钟").grid(row=0, column=2, padx=2)
        ttk.Spinbox(short_break_frame, from_=0, to=59, width=3, textvariable=self.short_break_seconds).grid(row=0, column=3, padx=2)
        ttk.Label(short_break_frame, text="秒").grid(row=0, column=4, padx=2)
        
        stage_break_frame = ttk.LabelFrame(right_frame, text="阶段休息时间", padding=0, labelanchor="nw")
        stage_break_frame.pack(fill=tk.BOTH, pady=2)
        
        ttk.Label(stage_break_frame).grid(row=0, column=0, padx=5, pady=5)
        ttk.Spinbox(stage_break_frame, from_=0, to=59, width=3, textvariable=self.stage_break_minutes).grid(row=0, column=1, padx=2)
        ttk.Label(stage_break_frame, text="分钟").grid(row=0, column=2, padx=2)
        ttk.Spinbox(stage_break_frame, from_=0, to=59, width=3, textvariable=self.stage_break_seconds).grid(row=0, column=3, padx=2)
        ttk.Label(stage_break_frame, text="秒").grid(row=0, column=4, padx=2)

        self.status_label = ttk.Label(right_frame, text="状态: 就绪", anchor="center", font=self.mid_font)
        self.status_label.pack(pady=20, anchor="center")
    
    def setup_timer_display(self, parent):
        """设置计时器显示部分"""
        # 时间显示框架
        time_display_frame = ttk.Frame(parent)
        time_display_frame.pack(fill=tk.X, pady=0)
        
        # 总时间显示
        total_display_frame = ttk.LabelFrame(time_display_frame, text="总计时")
        total_display_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        
        self.total_time_label = ttk.Label(total_display_frame, text="00:00:00", font=self.large_font)
        self.total_time_label.pack(pady=0)
        
        # 阶段时间显示
        stage_display_frame = ttk.LabelFrame(time_display_frame, text="阶段计时")
        stage_display_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.stage_time_label = ttk.Label(stage_display_frame, text="00:00:00", font=self.large_font)
        self.stage_time_label.pack(pady=0)
        
        # 休息时间显示
        break_display_frame = ttk.LabelFrame(time_display_frame, text="休息时长")
        break_display_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.break_time_label = ttk.Label(break_display_frame, text="00:00:00", font=self.large_font)
        self.break_time_label.pack(pady=0)
        
        # 总时间进度条
        total_progress_frame = ttk.LabelFrame(parent, text="总计时进度")
        total_progress_frame.pack(fill=tk.X, pady=5)
        
        self.total_progress = ttk.Progressbar(total_progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.total_progress.pack(fill=tk.X, pady=5, padx=5)
        
        # 阶段时间/休息时间进度条
        stage_progress_frame = ttk.LabelFrame(parent, text="阶段计时/休息时间进度")
        stage_progress_frame.pack(fill=tk.X, pady=5)
        
        self.stage_progress = ttk.Progressbar(stage_progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.stage_progress.pack(fill=tk.X, pady=5, padx=5)
    
    def setup_control_buttons(self, parent):
        """设置控制按钮"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=5)
        
        # 左侧按钮
        self.main_button = ttk.Button(control_frame, text="开始", command=self.handle_main_button)
        self.main_button.pack(side=tk.LEFT, padx=5)

        
        self.stop_button = ttk.Button(control_frame, text="重置", command=self.stop_timer, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 提示音设置按钮
        self.settings_button = ttk.Button(control_frame, text="设置", command=self.open_settings_window)
        self.settings_button.pack(side=tk.LEFT, padx=5)
    
    def open_settings_window(self):
        # 检查是否有任何可用音频文件
        has_audio = self.check_notification_audio_files()
        if not has_audio:
            messagebox.showinfo(
                "提示音缺失",
                "请将您喜欢的音频文件（支持 .mp3 和 .wav）放入软件根目录的 'notification' 文件夹中。\n\n"
                "📁 notification/\n"
                "├── notis/  （开始音 & 随机提醒音）\n"
                "└── pause/  （阶段结束音 & 总计时结束音）"
            )
            return  # 不打开设置窗口

        # 如果窗口已经存在，就提到前面
        if hasattr(self, 'sound_window') and self.sound_window.winfo_exists():
            self.sound_window.lift()
            return

        self.sound_window = tk.Toplevel(self.root)
        self.sound_window.title("设置和关于")
        self.sound_window.geometry("400x335")
        self.sound_window.resizable(False, False)
        self.sound_window.protocol("WM_DELETE_WINDOW", self.close_sound_settings)

        notebook = ttk.Notebook(self.sound_window)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.sound_vars = {}
        self.refresh_sound_tabs(notebook)

        
        # 添加版权和联系信息页签
        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="关于")

        ttk.Label(about_frame, text="作者：Zhiqian Yu", font=self.mid_font).pack(pady=60)
        email = tk.Label(about_frame, text="📧 yu-zhiqian@outlook.com", fg="blue", cursor="hand2")
        email.pack()
        email.bind("<Button-1>", lambda e: os.system('start mailto:yu-zhiqian@outlook.com'))

        github = tk.Label(about_frame, text="🌐 github.com/ZhiqianYu", fg="blue", cursor="hand2")
        github.pack(pady=5)
        github.bind("<Button-1>", lambda e: os.system('start https://github.com/ZhiqianYu'))

        ttk.Label(about_frame, text="V1.1 版权所有 © 2024", font=self.default_font).pack(pady=10)

        # 添加使用说明
        about_frame = ttk.Frame(notebook)
        instruction_frame = ttk.Frame(notebook)
        notebook.add(instruction_frame, text="使用说明")

        # 创建 Canvas + Scrollbar
        canvas = tk.Canvas(instruction_frame)
        scrollbar = ttk.Scrollbar(instruction_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # 滚动内容区域
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 添加 Label 内容
        label = ttk.Label(scrollable_frame, text=instruction_text, wraplength=300, justify="left", font=self.default_font)
        label.pack(padx=40, pady=10, anchor="w")

        # 按钮区
        button_frame = ttk.Frame(self.sound_window)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        ttk.Button(button_frame, text="保存", command=self.save_sound_settings).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="刷新音频列表", command=lambda: self.refresh_sound_tabs(notebook)).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="关闭", command=self.close_sound_settings).pack(side=tk.LEFT, padx=10)


    def setup_sound_list(self, parent, folder, config_key, multiple=True):
        """设置音频列表"""
        folder_path = os.path.join("notification", folder)
        audio_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.mp3', '.wav'))]

        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=20)

        canvas = tk.Canvas(list_frame, height=200, width=150)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="n")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not hasattr(self, 'sound_vars'):
            self.sound_vars = {}

        selected_files = self.config["sounds"].get(config_key, [] if multiple else "")
        
        for file in audio_files:
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=2)

            # 修正这里：根据配置文件严格选择文件是否勾选
            if multiple:
                is_selected = file in selected_files
            else:
                is_selected = file == selected_files

            var = tk.BooleanVar(value=is_selected)
            chk = ttk.Checkbutton(frame, text=file, variable=var)
            chk.pack(side=tk.LEFT, padx=5)
            self.sound_vars[f"{config_key}_{file}"] = var  # 使用组合key避免冲突

            play_btn = ttk.Button(frame, text="播放",
                                command=lambda f=file, folder=folder: self.play_sound(os.path.join("notification", folder, f)))
            play_btn.pack(side=tk.RIGHT, padx=5)

    def refresh_sound_tabs(self, notebook):
        """刷新音频标签页"""
        # 清除已有的标签页
        for tab in notebook.tabs():
            notebook.forget(tab)

        # 创建并添加标签页
        tabs_info = [
            ("计时开始", "notis", "start", False),
            ("随机提醒", "notis", "random", True),
            ("阶段休息开始", "pause", "stage_break_start", False),
            ("总计时结束", "pause", "total_end", False)
        ]

        for tab_name, folder, config_key, multiple in tabs_info:
            frame = ttk.Frame(notebook, padding=(50, 5))  # 设置左右间距为10，上下间距为5
            notebook.add(frame, text=tab_name)
            self.setup_sound_list(frame, folder, config_key, multiple)

    def play_sound(self, file_path):
        """播放音频预览"""
        try:
            # 停止当前播放的音频
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            
            # 加载并播放新音频
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
        except Exception as e:
            messagebox.showerror("错误", f"无法播放音频: {str(e)}")
    
    def save_sound_settings(self):
        """保存音频设置"""
        new_sound_config = {}

        audio_types = {
            "start": ("notis", False),
            "random": ("notis", True),
            "stage_break_start": ("pause", False),
            "total_end": ("pause", False)
        }

        for key, (folder, multiple) in audio_types.items():
            folder_path = os.path.join("notification", folder)
            audio_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.mp3', '.wav'))]

            if multiple:
                selected_files = [
                    file for file in audio_files
                    if self.sound_vars.get(f"{key}_{file}", tk.BooleanVar()).get()
                ]
                new_sound_config[key] = selected_files
            else:
                selected_file = next((
                    file for file in audio_files
                    if self.sound_vars.get(f"{key}_{file}", tk.BooleanVar()).get()
                ), "")
                new_sound_config[key] = selected_file

        self.config["sounds"] = new_sound_config
        self.save_config()
        messagebox.showinfo("成功", "音频设置已保存")


    def start_timer(self):
        """开始计时"""
        try:
            # 获取所有设置值
            total_h = int(self.total_hours.get())
            total_m = int(self.total_minutes.get())
            total_s = int(self.total_seconds.get())
            
            stage_h = int(self.stage_hours.get())
            stage_m = int(self.stage_minutes.get())
            stage_s = int(self.stage_seconds.get())
            
            random_min = int(self.random_min.get())
            random_max = int(self.random_max.get())
            
            short_break_m = int(self.short_break_minutes.get())
            short_break_s = int(self.short_break_seconds.get())
            
            stage_break_m = int(self.stage_break_minutes.get())
            stage_break_s = int(self.stage_break_seconds.get())
            
            # 检查时间设置是否完整
            if (total_h == 0 and total_m == 0 and total_s == 0) or \
               (stage_h == 0 and stage_m == 0 and stage_s == 0):
                messagebox.showerror("错误", "请完整设置总时间和阶段时间！")
                return
            
            # 更新配置
            self.config["total_time"] = {"hours": total_h, "minutes": total_m, "seconds": total_s}
            self.config["stage_time"] = {"hours": stage_h, "minutes": stage_m, "seconds": stage_s}
            self.config["random_reminder"] = {"min": random_min, "max": random_max}
            self.config["short_break"] = {"minutes": short_break_m, "seconds": short_break_s}
            self.config["stage_break"] = {"minutes": stage_break_m, "seconds": stage_break_s}
            
            # 保存配置
            self.save_config()
            
            # 计算总时间（秒）
            self.total_time_left = total_h * 3600 + total_m * 60 + total_s
            # 计算阶段时间（秒）
            self.stage_time_left = stage_h * 3600 + stage_m * 60 + stage_s
            # 设置初始状态
            self.current_state = "stage"
            # 计算下一次随机提醒时间
            min_seconds = random_min * 60
            max_seconds = random_max * 60
            self.next_reminder = random.randint(min_seconds, max_seconds)
            
            # 如果计时器已经在运行，就不要重新启动
            if not self.timer_running:
                self.timer_running = True
                self.paused = False  # 确保计时器未暂停
                # 播放计时开始音
                self.play_notification("start")
                # 启动计时器线程
                threading.Thread(target=self.timer_loop, daemon=True).start()
                
                # 更新按钮状态
                self.stop_button.config(state=tk.NORMAL)
                
                # 更新状态标签
                self.status_label.config(text="状态: 计时中 - 阶段计时")
        except ValueError as e:
            messagebox.showerror("错误", f"请输入有效的数字: {str(e)}")
    
    def stop_timer(self):
        """停止计时"""
        self.timer_running = False  # 停止计时器线程
        self.paused = False  # 重置暂停状态
        
        # 重置计时器状态和时间变量
        self.total_time_left = 0
        self.stage_time_left = 0
        self.break_time_left = 0
        
        # 停止当前播放的音频
        pygame.mixer.music.stop()
        
        # 重置显示
        self.total_time_label.config(text="00:00:00")
        self.stage_time_label.config(text="00:00:00")
        self.break_time_label.config(text="00:00:00")
        self.total_progress["value"] = 0
        self.stage_progress["value"] = 0
        
        # 更新按钮状态
        self.main_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # 更新状态标签
        self.status_label.config(text="状态: 就绪")
    
    def get_state_label(self):
        """获取当前状态的标签文本"""
        if self.current_state == "stage":
            return "阶段计时"
        elif self.current_state == "short_break":
            return "短休息"
        elif self.current_state == "stage_break":
            return "阶段休息"
        return "就绪"
    
    def play_notification(self, sound_type):
        try:
            # 停止当前播放的音频
            pygame.mixer.music.stop()

            file_path = None
            if sound_type == "random" and self.config["sounds"]["random"]:
                sound_file = random.choice(self.config["sounds"]["random"])
                file_path = os.path.join("notification", "notis", sound_file)
            elif sound_type in self.config["sounds"] and self.config["sounds"][sound_type]:
                sound_file = self.config["sounds"][sound_type]
                folder = "notis" if sound_type in ["start", "random"] else "pause"
                file_path = os.path.join("notification", folder, sound_file)

            if not file_path or not os.path.exists(file_path):
                print(f"音频文件未找到: {file_path}")
                return

            # 使用缓存播放
            if file_path not in self.audio_cache:
                self.audio_cache[file_path] = pygame.mixer.Sound(file_path)

            sound = self.audio_cache[file_path]
            sound.play()

        except Exception as e:
            print(f"播放音频失败: {str(e)}")

    
    def timer_loop(self):
        initial_total_time = self.total_time_left
        initial_stage_time = self.stage_time_left
        initial_short_break_time = self.config["short_break"]["minutes"] * 60 + self.config["short_break"]["seconds"]
        initial_stage_break_time = self.config["stage_break"]["minutes"] * 60 + self.config["stage_break"]["seconds"]

        while self.timer_running:
            if not self.paused:
                # 总时间倒计时
                if self.total_time_left > 0:
                    self.total_time_left -= 1
                    progress = (initial_total_time - self.total_time_left) / initial_total_time * 100
                    self.total_progress["value"] = progress

                # 状态判断与执行
                if self.current_state == "stage":
                    if self.stage_time_left > 0:
                        self.stage_time_left -= 1
                        self.next_reminder -= 1

                        stage_progress = (initial_stage_time - self.stage_time_left) / initial_stage_time * 100
                        self.stage_progress["value"] = stage_progress

                        if self.next_reminder <= 0:
                            self.play_notification("random")
                            self.current_state = "short_break"
                            self.break_time_left = initial_short_break_time
                            # 暂停阶段计时
                            self.stage_progress["value"] = 0

                    if self.stage_time_left <= 0:
                        self.play_notification("stage_break_start")
                        self.current_state = "stage_break"
                        self.break_time_left = initial_stage_break_time
                        self.stage_progress["value"] = 0

                elif self.current_state == "short_break":
                    if self.break_time_left > 0:
                        self.break_time_left -= 1
                        break_progress = (initial_short_break_time - self.break_time_left) / initial_short_break_time * 100
                        self.stage_progress["value"] = break_progress
                    else:
                        self.play_notification("start")
                        self.current_state = "stage"
                        min_seconds = self.config["random_reminder"]["min"] * 60
                        max_seconds = self.config["random_reminder"]["max"] * 60
                        self.next_reminder = random.randint(min_seconds, max_seconds)
                        self.stage_progress["value"] = 0

                elif self.current_state == "stage_break":
                    if self.break_time_left > 0:
                        self.break_time_left -= 1
                        break_progress = (initial_stage_break_time - self.break_time_left) / initial_stage_break_time * 100
                        self.stage_progress["value"] = break_progress
                    else:
                        self.play_notification("start")
                        self.current_state = "stage"
                        self.stage_time_left = initial_stage_time
                        min_seconds = self.config["random_reminder"]["min"] * 60
                        max_seconds = self.config["random_reminder"]["max"] * 60
                        self.next_reminder = random.randint(min_seconds, max_seconds)
                        self.stage_progress["value"] = 0

                # 总计时结束判断
                if self.total_time_left <= 0:
                    self.play_notification("total_end")
                    self.timer_running = False
                    break

                self.update_time_display()

            time.sleep(1)

        self.reset_timer_ui()

    
    def update_time_display(self):
        """更新时间显示"""
        # 更新总时间显示
        total_h = self.total_time_left // 3600
        total_m = (self.total_time_left % 3600) // 60
        total_s = self.total_time_left % 60
        total_time_str = f"{total_h:02d}:{total_m:02d}:{total_s:02d}"

        # 更新阶段时间显示
        if self.current_state == "stage" or self.current_state == "short_break":
            # 在阶段计时和短休息时，阶段计时显示始终为剩余时间
            stage_h = self.stage_time_left // 3600
            stage_m = (self.stage_time_left % 3600) // 60
            stage_s = self.stage_time_left % 60
            stage_time_str = f"{stage_h:02d}:{stage_m:02d}:{stage_s:02d}"
        else:
            # 阶段休息时阶段计时显示00:00:00
            stage_time_str = "00:00:00"

        # 休息时间显示
        if self.current_state in ["short_break", "stage_break"]:
            break_h = self.break_time_left // 3600
            break_m = (self.break_time_left % 3600) // 60
            break_s = self.break_time_left % 60
            break_time_str = f"{break_h:02d}:{break_m:02d}:{break_s:02d}"
        else:
            break_time_str = "00:00:00"

        # 更新到界面
        self.root.after(0, lambda: self.total_time_label.config(text=total_time_str))
        self.root.after(0, lambda: self.stage_time_label.config(text=stage_time_str))
        self.root.after(0, lambda: self.break_time_label.config(text=break_time_str))

    
    def close_sound_settings(self):
        """关闭提示音设置窗口并停止音乐播放"""
        pygame.mixer.music.stop()  # 停止当前播放的音频
        if hasattr(self, 'sound_window') and self.sound_window.winfo_exists():
            self.sound_window.destroy()

    def reset_timer_ui(self):
        """重置计时器结束时的UI状态"""
        self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.main_button.config(text="开始"))
        self.main_button_state = "ready"
        self.status_label.config(text="状态: 就绪")
        self.total_progress["value"] = 0
        self.stage_progress["value"] = 0

    def check_notification_audio_files(self):
        """检查 notification 文件夹中是否有任一音频文件"""
        base_path = os.path.join(os.getcwd(), "notification")
        subfolders = ["notis", "pause"]
        for sub in subfolders:
            folder = os.path.join(base_path, sub)
            if os.path.isdir(folder):
                files = [f for f in os.listdir(folder) if f.lower().endswith(('.mp3', '.wav'))]
                if files:
                    return True  # 有至少一个音频文件
        return False
    
    def handle_main_button(self):
        if self.main_button_state == "ready":
            self.start_timer()
            self.main_button.config(text="暂停")
            self.main_button_state = "running"
        elif self.main_button_state == "running":
            self.paused = True
            pygame.mixer.music.stop()
            self.status_label.config(text=f"状态: 已暂停 - {self.get_state_label()}")
            self.main_button.config(text="继续")
            self.main_button_state = "paused"
        elif self.main_button_state == "paused":
            self.paused = False
            self.status_label.config(text=f"状态: 计时中 - {self.get_state_label()}")
            self.main_button.config(text="暂停")
            self.main_button_state = "running"

# 使用说明内容
instruction_text = """
在阶段式学习中，合理的时间管理和科学的复习方法能够显著提升学习效率和记忆效果。多阶段随机提醒计时器 的设计灵感来源于以下理念：

1. 随机提醒：
    在每个学习阶段中，设置每隔3-5分钟的随机提醒。当提醒响起时，可以闭上眼睛，清空大脑,回顾刚才学习的内容。这一短暂的“复盘”可以帮助大脑快速整理信息，重新激活刚才激活过的神经通路。这种神经通路的激活速度是直接再次阅读知识点的10-20倍。这意味着，10 秒的时间通过这种技巧可以实现相当于3-5分钟高效复习的效果，并且可以保持注意力集中。

2. 阶段时间：
    学习阶段是较长时间的专注学习期。在阶段结束后，建议进行一次较长的休息，彻底放松大脑。这不仅有助于缓解大脑疲劳，还能进一步巩固记忆。

3. 总时间：
    可以根据一天的学习目标，设置多个学习阶段与休息时间的组合，达到科学高效的一天学习计划。

通过这种方法，多阶段随机提醒计时器 不仅是一个简单的时间管理工具，更是一个助力高效学习的好帮手。
"""


if __name__ == "__main__":
    root = tk.Tk()
    app = TimerApp(root)
    root.mainloop()