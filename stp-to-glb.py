#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: 1173381395@qq.com
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import re
import sys

VERSION = "V0.0.2"


def resource_path(relative_path):
    """ 获取资源绝对路径，兼容开发环境和 Nuitka 打包（--onefile / --standalone）"""
    if hasattr(sys, '_MEIPASS'):
        # 打包模式：资源在临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # 开发模式：资源在脚本所在目录
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def contains_chinese(text):
    """判断字符串中是否包含中文字符"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


class App:
    def __init__(self, root):
        self.root = root
        self.root.iconbitmap(resource_path(r"res/logo.ico"))
        self.root.title(f"STP to GLB    {VERSION}")
        self.root.geometry("600x450")
        self.center_window(self.root, 600, 450)

        # 默认参数
        self.params = {
            "lin_defl": tk.DoubleVar(value=0.1),
            "ang_defl": tk.DoubleVar(value=0.5),
            "rel_defl": tk.BooleanVar(value=False),
            "debug": tk.BooleanVar(value=False),
            "solid_only": tk.BooleanVar(value=False),
            "max_geometry_num": tk.IntVar(value=0),
            "filter_names_include": tk.StringVar(value=""),
            "filter_names_file_include": tk.StringVar(value=""),
            "filter_names_exclude": tk.StringVar(value=""),
            "filter_names_file_exclude": tk.StringVar(value=""),
            "tessellation_timeout": tk.IntVar(value=30),
        }
        self.open_dir = tk.BooleanVar(value=True)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()

        self.create_menu()
        self.create_widgets()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="⚙️ 参数设置", command=self.open_settings)
        settings_menu.add_command(label="❌ 退出", command=self.close)
        menubar.add_cascade(label="🚪 菜单", menu=settings_menu)
        menubar.add_command(label="ℹ️ 关于", command=self.show_about)

    def create_placeholder_entry(self, parent, textvariable, placeholder_text, **kwargs):
        """创建带 placeholder 的 Entry"""
        entry = ttk.Entry(parent, textvariable=textvariable, **kwargs)

        def on_focus_in(event):
            if textvariable.get() == placeholder_text:
                textvariable.set("")
                entry.config(foreground="black")

        def on_focus_out(event):
            if textvariable.get() == "":
                textvariable.set(placeholder_text)
                entry.config(foreground="gray")

        # 初始化状态
        if not textvariable.get():
            textvariable.set(placeholder_text)
            entry.config(foreground="gray")

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        return entry

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 输入路径
        ttk.Label(frame, text="选择stp文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.input_path, width=60).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="浏览...", command=self.browse_input).grid(row=0, column=2, padx=5)

        # 输出路径
        # ttk.Label(frame, text="输出路径:").grid(row=1, column=0, sticky=tk.W, pady=5)
        # ttk.Entry(frame, textvariable=self.output_path, width=60).grid(row=1, column=1, padx=5, pady=5)
        # ttk.Button(frame, text="浏览...", command=self.browse_output).grid(row=1, column=2, padx=5)

        # 转换按钮
        ttk.Checkbutton(frame, text="完成后打开输出目录", variable=self.open_dir, onvalue=True, offvalue=False).grid(
            row=2, column=0, sticky=tk.W, pady=5, columnspan=3)
        self.convert_button = ttk.Button(frame, text="开始转换", command=self.start_conversion)
        self.convert_button.grid(row=3, column=1, pady=10)

        # 日志显示
        # ttk.Label(frame, text="日志:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.log_text = scrolledtext.ScrolledText(frame, width=90, height=20, state='disabled')
        self.log_text.grid(row=4, column=0, columnspan=3, pady=5)

        # 配置 grid 权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def browse_input(self):
        path = filedialog.askopenfilename(filetypes=[("STEP files", "*.step *.stp"), ("All files", "*.*")])
        if path:
            self.input_path.set(path)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_path.set(path)

    def center_window(self, window, width, height):
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')
        window.update_idletasks()
        window.resizable(False, False)

    def close(self):
        self.log("Bye ~")
        self.root.quit()

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.iconbitmap(resource_path(r"res/logo.ico"))
        settings_win.title("参数设置")
        settings_win.geometry("500x400")
        self.center_window(settings_win, 500, 400)  # 居中显示
        # 创建模态对话框
        settings_win.transient(self.root)
        # 防止用户“绕过”设置窗口继续操作主界面
        settings_win.grab_set()

        # 创建 Canvas 和 Scrollable Frame
        canvas = tk.Canvas(settings_win)
        scrollbar = ttk.Scrollbar(settings_win, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 配置 grid 列宽
        for i in range(2):  # 两列：标签和控件
            scrollable_frame.columnconfigure(i, weight=1)

        row = 0

        # --- 线性偏差 ---
        ttk.Label(scrollable_frame, text="线性偏差[0-1]").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        spinbox = ttk.Spinbox(scrollable_frame, from_=0.0, to=1.0, increment=0.01, textvariable=self.params["lin_defl"],
                              width=10)
        spinbox.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        row += 1

        # --- 角度偏差 ---
        ttk.Label(scrollable_frame, text="角度偏差[0-1]").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        spinbox = ttk.Spinbox(scrollable_frame, from_=0.0, to=1.0, increment=0.01, textvariable=self.params["ang_defl"],
                              width=10)
        spinbox.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        row += 1

        # --- 相对偏差 ---
        ttk.Checkbutton(scrollable_frame, text="相对偏差", variable=self.params["rel_defl"]).grid(row=row, column=0,
                                                                                                  sticky=tk.W, padx=10,
                                                                                                  pady=5)
        ttk.Checkbutton(scrollable_frame, text="调试模式", variable=self.params["debug"]).grid(row=row, column=1,
                                                                                               sticky=tk.W, padx=10,
                                                                                               pady=5)
        row += 1
        ttk.Checkbutton(scrollable_frame, text="仅实体", variable=self.params["solid_only"]).grid(row=row, column=0,
                                                                                                  sticky=tk.W, padx=10,
                                                                                                  pady=5)
        row += 1

        # --- 最大几何体数量 ---
        ttk.Label(scrollable_frame, text="最大几何体数量").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        spinbox = ttk.Spinbox(scrollable_frame, from_=0, to=10000, textvariable=self.params["max_geometry_num"],
                              width=10)
        spinbox.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        row += 1

        # --- 包含名称过滤器 ---
        ttk.Label(scrollable_frame, text="包含名称过滤器").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        entry = ttk.Entry(scrollable_frame, textvariable=self.params["filter_names_include"], width=30)
        entry.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        row += 1

        # --- 包含文件过滤器 ---
        ttk.Label(scrollable_frame, text="包含名称过滤器文件").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        file_entry = ttk.Entry(scrollable_frame, textvariable=self.params["filter_names_file_include"], width=30)
        file_entry.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        browse_btn = ttk.Button(scrollable_frame, text="浏览",
                                command=lambda: self.browse_file_for(settings_win, "filter_names_file_include"))
        browse_btn.grid(row=row, column=2, padx=5, pady=5)  # 第三列放按钮
        row += 1

        # --- 排除名称过滤器 ---
        ttk.Label(scrollable_frame, text="排除名称过滤器").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        entry = ttk.Entry(scrollable_frame, textvariable=self.params["filter_names_exclude"], width=30)
        entry.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        row += 1

        # --- 排除文件过滤器 ---
        ttk.Label(scrollable_frame, text="排除名称过滤器文件").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        file_entry = ttk.Entry(scrollable_frame, textvariable=self.params["filter_names_file_exclude"], width=30)
        file_entry.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        browse_btn = ttk.Button(scrollable_frame, text="浏览",
                                command=lambda: self.browse_file_for(settings_win, "filter_names_file_exclude"))
        browse_btn.grid(row=row, column=2, padx=5, pady=5)
        row += 1

        # --- 网格化超时 ---
        ttk.Label(scrollable_frame, text="网格化超时时间 (秒)").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        spinbox = ttk.Spinbox(scrollable_frame, from_=1, to=300, textvariable=self.params["tessellation_timeout"],
                              width=10)
        spinbox.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        row += 1

        # --- 确定按钮 ---
        ttk.Button(scrollable_frame, text="确定", command=settings_win.destroy).grid(row=row, column=0, columnspan=3,
                                                                                     pady=10)

        # 放置 canvas 和 scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 关键：确保 frame 宽度足够
        settings_win.update_idletasks()
        canvas.config(width=480)  # 控制可见宽度

    def browse_file_for(self, window, var_name):
        path = filedialog.askopenfilename(
            parent=window,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            self.params[var_name].set(path)

    def show_about(self):
        messagebox.showinfo("关于", f"STEP 格式转换工具\n版本: {VERSION}\n作者: lorien\nEmail: 1173381395@qq.com\n")

    def log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()

    def start_conversion(self):
        inp = self.input_path.get().strip()
        out = os.path.dirname(inp)
        if contains_chinese(inp):
            messagebox.showerror("错误", "输入输出路径不能包含中文字符！")
            return
        if not inp or not os.path.isfile(inp):
            messagebox.showerror("错误", "请选择有效的输入文件！")
            return
        if not out:
            messagebox.showerror("错误", "请选择有效的输出目录！")
            return

        self.convert_button.config(state='disabled')
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

        # 在新线程中运行转换，避免界面卡死
        thread = threading.Thread(target=self.run_converter, args=(inp, out), daemon=True)
        thread.start()

    def run_converter(self, input_file, output_path):
        output_file = f"{output_path}/output-{time.strftime("%Y%m%d%H%M%S")}.glb"
        try:
            exe_path = resource_path("res/stptoglb.exe")
            cmd = [exe_path]
            cmd += ["--stp", f"{input_file}"]
            cmd += ["--glb", f"{output_file}"]

            # 添加参数
            cmd += ["--lin-defl", str(self.params["lin_defl"].get())]
            cmd += ["--ang-defl", str(self.params["ang_defl"].get())]
            if self.params["rel_defl"].get():
                cmd.append("--rel-defl")
            if self.params["debug"].get():
                cmd.append("--debug")
            if self.params["solid_only"].get():
                cmd.append("--solid-only")
            if self.params["max_geometry_num"].get() > 0:
                cmd += ["--max-geometry-num", str(self.params["max_geometry_num"].get())]
            if self.params["filter_names_include"].get():
                cmd += ["--filter-names-include", self.params["filter_names_include"].get()]
            if self.params["filter_names_file_include"].get():
                cmd += ["--filter-names-file-include", self.params["filter_names_file_include"].get()]
            if self.params["filter_names_exclude"].get():
                cmd += ["--filter-names-exclude", self.params["filter_names_exclude"].get()]
            if self.params["filter_names_file_exclude"].get():
                cmd += ["--filter-names-file-exclude", self.params["filter_names_file_exclude"].get()]
            cmd += ["--tessellation-timeout", str(self.params["tessellation_timeout"].get())]

            # 启动子进程并实时读取输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            for line in iter(process.stdout.readline, ''):
                if line:
                    self.log(line.strip())

            process.wait()
            if process.returncode == 0:
                self.log("✅ 转换完成！")
                # 自动打开输出目录（Windows）
                try:
                    if os.path.isdir(output_path) and self.open_dir.get():
                        os.startfile(os.path.normpath(output_path))
                except Exception as e:
                    self.log(f"⚠️ 无法打开输出目录: {e}")
            else:
                self.log(f"❌ 转换失败，返回码: {process.returncode}")

        except Exception as e:
            self.log(f"⚠️ 异常: {str(e)}")
        finally:
            self.root.after(0, lambda: self.convert_button.config(state='normal'))


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
