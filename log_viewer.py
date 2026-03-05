# -*- coding: utf-8 -*-
"""
日志查看器 - 用于显示 api_server.py 的运行日志
"""
import os
import tkinter as tk
from tkinter import scrolledtext
import threading
import time

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.log")

class LogViewer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Agent Swarm 日志查看器")
        self.root.geometry("900x600")
        
        # 创建文本框
        self.text_area = scrolledtext.ScrolledText(
            self.root, 
            wrap=tk.WORD, 
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4"
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 底部按钮
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(btn_frame, text="刷新日志", command=self.refresh_log).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="清空显示", command=self.clear_display).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="自动刷新(开/关)", command=self.toggle_auto_refresh).pack(side=tk.LEFT, padx=5)
        
        self.auto_refresh = False
        self.last_size = 0
        
        self.refresh_log()
        
        if self.auto_refresh:
            self.auto_refresh_loop()
    
    def refresh_log(self):
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(0, 2)  # 跳到文件末尾
                    file_size = f.tell()
                    
                    if file_size < self.last_size:
                        # 文件被重置，从头读取
                        f.seek(0)
                    else:
                        # 只读取新增内容
                        f.seek(self.last_size)
                    
                    new_content = f.read()
                    self.last_size = file_size
                    
                    if new_content:
                        self.text_area.insert(tk.END, new_content)
                        self.text_area.see(tk.END)
        except Exception as e:
            print(f"读取日志失败: {e}")
    
    def clear_display(self):
        self.text_area.delete(1.0, tk.END)
    
    def toggle_auto_refresh(self):
        self.auto_refresh = not self.auto_refresh
        if self.auto_refresh:
            self.auto_refresh_loop()
    
    def auto_refresh_loop(self):
        if self.auto_refresh:
            self.refresh_log()
            self.root.after(1000, self.auto_refresh_loop)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    viewer = LogViewer()
    viewer.run()
