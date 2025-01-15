import tkinter as tk
from tkinter import messagebox

class SystemPromptManager:
    def __init__(self, root, prompts_manager, main_app=None):
        self.root = root
        self.prompts_manager = prompts_manager
        self.main_app = main_app  # Store reference to main application
        self.system_prompt = ""
        self.system_prompt_window = None
        self.system_prompt_text = None

    def open_system_prompt_editor(self):
        """打开系统提示词编辑窗口"""
        # 如果窗口已存在，先销毁并清理
        if self.system_prompt_window and self.system_prompt_window.winfo_exists():
            self.system_prompt_window.destroy()
            self.system_prompt_window = None
            self.system_prompt_text = None

        self.system_prompt_window = tk.Toplevel(self.root)
        self.system_prompt_window.title("系统提示词")
        self.system_prompt_window.geometry("600x400")
        
        # 绑定窗口关闭事件
        self.system_prompt_window.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # 创建文本框
        self.system_prompt_text = tk.Text(self.system_prompt_window, wrap=tk.WORD, height=10)
        self.system_prompt_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.system_prompt_text.insert(tk.END, self.main_app.system_prompt)  # 显示当前系统提示词

        # 创建保存按钮
        save_button = tk.Button(self.system_prompt_window, text="保存", command=self.save_system_prompt)
        save_button.pack(pady=10)

    def on_window_close(self):
        """处理窗口关闭事件"""
        if self.system_prompt_window:
            self.system_prompt_window.destroy()
            self.system_prompt_window = None
            self.system_prompt_text = None

    def save_system_prompt(self):
        """保存系统提示词"""
        new_system_prompt = self.system_prompt_text.get("1.0", tk.END).strip()
        self.main_app.system_prompt = new_system_prompt

        # 检查对话历史中是否包含 system 消息
        system_message_index = -1
        for i, message in enumerate(self.main_app.conversation_history):
            if message["role"] == "system":
                system_message_index = i
                break

        if system_message_index != -1:
            # 如果存在 system 消息，更新其内容
            self.main_app.conversation_history[system_message_index]["content"] = new_system_prompt
        else:
            # 如果不存在 system 消息，插入到对话历史的最前面
            self.main_app.conversation_history.insert(0, {"role": "system", "content": new_system_prompt})

        messagebox.showinfo("成功", "系统提示词已更新并立即生效")
        self.system_prompt_window.destroy()

    def update_system_prompt_display(self):
        """更新系统提示词窗口显示"""
        self.system_prompt = self.main_app.system_prompt
        if (self.system_prompt_window and 
            self.system_prompt_text and
            self.system_prompt_window.winfo_exists()):
            self.system_prompt_text.config(state=tk.NORMAL)
            self.system_prompt_text.delete("1.0", tk.END)
            self.system_prompt_text.insert(tk.END, self.system_prompt)
            self.system_prompt_text.config(state=tk.NORMAL)
