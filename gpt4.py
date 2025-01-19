import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
import requests
import time
import threading
import json
import os
import webbrowser
from prompts_manager.prompts_manager import PromptsManager
from prompts_manager.system_prompt_manager import SystemPromptManager


# 加载配置文件
def load_config(CONFIG_FILE = "config.json"):
    """从 config.json 文件中加载配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
                config = json.load(file)
                return config
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

# 保存配置文件
def save_config(config,CONFIG_FILE = "config.json"):
    """将配置保存到 config.json 文件中"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
            json.dump(config, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存配置文件失败: {str(e)}")


class DeepSeekChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Chat")

        # 加载配置
        self.CONFIG_FILE = "gpt4config.json"
        config = load_config(self.CONFIG_FILE)
        self.API_URL = config.get("API_URL", DEFAULT_CONFIG["API_URL"])
        self.API_KEY = config.get("API_KEY", DEFAULT_CONFIG["API_KEY"])
        self.max_history_length = config.get("max_history_length", DEFAULT_CONFIG["max_history_length"])
        self.max_tokens = config.get("max_tokens", DEFAULT_CONFIG["max_tokens"])

        # 参数设置
        self.temperature = 1.5  # 默认温度参数
        self.conversation_history = []  # 初始化对话历史
        self.system_prompt = ""  # 默认系统提示词

        # 模型选择
        self.models = ["gpt-4o-mini","gpt-4o","gpt-4-turbo","gpt-4","gpt-4-32k"]  # 可用的模型列表
        self.selected_model = tk.StringVar(value=self.models[0])  # 默认选择第一个模型

        # 创建控制面板
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(padx=10, pady=5, fill=tk.X)

        # 添加模型选择下拉菜单
        tk.Label(self.control_frame, text="选择模型:").pack(side=tk.LEFT)
        self.model_menu = ttk.Combobox(self.control_frame, textvariable=self.selected_model, values=self.models, state="readonly")
        self.model_menu.pack(side=tk.LEFT, padx=(5, 10))
        # 阻止模型选择菜单的缩放
        self.model_menu.bind('<Control-MouseWheel>', lambda e: "break")
        self.model_menu.bind('<Control-Button-4>', lambda e: "break")  # Linux zoom prevention
        self.model_menu.bind('<Control-Button-5>', lambda e: "break")  # Linux zoom prevention

        # 添加温度选择下拉菜单
        self.temperature_options = {
            "代码生成/数学解题": 0.0,
            "数据抽取/分析": 1.0,
            "通用对话": 1.3,
            "翻译": 1.3,
            "创意类写作/诗歌创作": 1.5
        }
        self.selected_temperature = tk.StringVar(value="通用对话")  # 默认选择
        tk.Label(self.control_frame, text="场景选择:").pack(side=tk.LEFT, padx=(10, 5))
        self.temperature_menu = ttk.Combobox(self.control_frame, textvariable=self.selected_temperature, values=list(self.temperature_options.keys()), state="readonly")
        self.temperature_menu.pack(side=tk.LEFT)

        # 添加 Prompts 管理按钮
        self.prompts_button = tk.Button(self.control_frame, text="管理Prompts", command=self.open_prompts_manager)
        self.prompts_button.pack(side=tk.RIGHT, padx=(10, 0))

        # 添加设置按钮
        self.settings_button = tk.Button(self.control_frame, text="设置", command=self.open_settings)
        self.settings_button.pack(side=tk.RIGHT, padx=(10, 0))

        # 添加历史对话按钮
        self.history_dir = "history"
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)
        self.history_button = tk.Button(self.control_frame, text="加载历史", command=self.show_history_window)
        self.history_button.pack(side=tk.RIGHT, padx=(10, 0))

        # 添加系统提示词按钮
        self.system_prompt_button = tk.Button(self.control_frame, text="系统提示词", command=self.open_system_prompt_editor)
        self.system_prompt_button.pack(side=tk.RIGHT, padx=(10, 0))

        # 初始化字体大小
        self.font_size = 12
        self.min_font_size = 6
        self.max_font_size = 40
        
        # 创建样式对象并配置
        self.style = ttk.Style()
        # 配置文本控件样式
        self.style.configure('TText', 
            font=('Arial', self.font_size),
            foreground='black',
            background='white',
            padding=5,
            wrap=tk.WORD
        )
        # 配置按钮样式
        self.style.configure('TButton',
            font=('Arial', self.font_size),
            padding=5,
            relief=tk.RAISED
        )
        # 配置滚动条样式
        self.style.configure('Vertical.TScrollbar',
            gripcount=0,
            background='#E1E1E1',
            troughcolor='#F0F0F0',
            arrowsize=15
        )

        # 创建聊天容器
        self.chat_container = tk.Frame(root)
        self.chat_container.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 创建聊天显示区域
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_container, 
            wrap=tk.WORD, 
            state='disabled',
            font=('Arial', self.font_size),

        )
        
        # 绑定 Ctrl+鼠标滚轮事件 - 仅允许字体缩放
        self.chat_display.bind('<Control-MouseWheel>', self.zoom_font)
        self.chat_display.bind('<Control-Button-4>', self.zoom_font)  # Linux zoom
        self.chat_display.bind('<Control-Button-5>', self.zoom_font)  # Linux zoom
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # 设置容器最大高度
        self.chat_container.pack_propagate(False)
        self.chat_container.config(height=480)  # 设置固定高度

        # 创建输入框和发送按钮
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(padx=10, pady=10, fill=tk.X)

        # 使用Text控件代替Entry，并添加滚动条
        self.user_input = tk.Text(self.input_frame, height=5, wrap=tk.WORD, font=('Arial', 12))
        self.user_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


        # 添加垂直滚动条
        scrollbar = ttk.Scrollbar(self.input_frame, command=self.user_input.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.user_input.config(yscrollcommand=scrollbar.set)

        # 创建按钮容器
        self.button_frame = tk.Frame(self.input_frame)
        self.button_frame.pack(side=tk.RIGHT, padx=(10, 0), fill=tk.Y)

        # 发送按钮（变大）
        self.send_button = tk.Button(self.button_frame, text="发送", command=self.send_message, width=10, height=2)
        self.send_button.pack(side=tk.BOTTOM, pady=(0, 5))

        # 创建顶部按钮容器
        self.top_button_frame = tk.Frame(self.button_frame)
        self.top_button_frame.pack(side=tk.TOP)

        # 撤回按钮
        self.undo_button = tk.Button(self.top_button_frame, text="撤回", command=self.undo_last_message, width=4)
        self.undo_button.pack(side=tk.LEFT, padx=(0, 2))

        # 清空历史按钮
        self.clear_history_button = tk.Button(self.top_button_frame, text="清空", command=self.clear_history, width=4)
        self.clear_history_button.pack(side=tk.LEFT)

        # 保存历史按钮
        self.save_history_button = tk.Button(self.button_frame, text="保存历史", command=self.save_history, width=10)
        self.save_history_button.pack(side=tk.TOP, pady=(1, 1))

        # 添加加载指示器
        self.loading_label = tk.Label(root, text="", fg="blue")
        self.loading_label.pack()

        # 绑定回车键发送消息（注意：现在需要处理多行输入）
        self.root.bind('<Return>', self.handle_enter_key)

        # 初始化系统提示词输入框
        self.system_prompt_text = None
        
        # 初始化 PromptsManager 和 SystemPromptManager
        self.prompts_manager = PromptsManager(root, main_app=self, main_input=self.user_input)
        self.system_prompt_manager = SystemPromptManager(root, self.prompts_manager, main_app=self)

    def save_history(self):
        """保存历史对话"""
        if not self.conversation_history:
            messagebox.showwarning("警告", "当前没有历史对话可保存")
            return

        # 弹出文件保存对话框
        file_types = [("JSON文件", "*.json"), ("Markdown文件", "*.md")]
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=file_types,
            initialdir="history",
            title="保存历史对话"
        )
        
        if not file_path:  # 用户取消保存
            return

        try:
            if file_path.endswith(".json"):
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(self.conversation_history, file, ensure_ascii=False, indent=4)
            elif file_path.endswith(".md"):
                with open(file_path, 'w', encoding='utf-8') as file:
                    # 将对话历史转换为Markdown格式
                    md_content = "# 对话历史\n\n"
                    for msg in self.conversation_history:
                        role = msg["role"].capitalize()
                        content = msg["content"]
                        md_content += f"## {role}\n\n{content}\n\n"
                    file.write(md_content)
            
            messagebox.showinfo("成功", f"历史对话已保存为 {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存文件时出错: {str(e)}")

    def show_history_window(self):
        """显示历史对话窗口"""
        self.history_window = tk.Toplevel()
        self.history_window.title("历史对话")
        self.history_window.geometry("800x600")

        # 使用grid布局
        self.history_window.grid_columnconfigure(0, weight=1)
        self.history_window.grid_rowconfigure(1, weight=1)

        # 创建主容器
        main_frame = tk.Frame(self.history_window)
        main_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        # 配置主容器grid布局
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # 创建文件列表
        self.file_listbox = ttk.Treeview(main_frame, selectmode="browse", show="tree")
        self.file_listbox.grid(row=0, column=0, sticky='ns', padx=(0, 10))

        # 添加滚动条
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        # 阻止所有ttk控件的缩放事件
        self.file_listbox.bind('<Control-MouseWheel>', lambda e: "break")
        scrollbar.bind('<Control-MouseWheel>', lambda e: "break")


        # 创建预览区域
        preview_frame = tk.Frame(main_frame)
        preview_frame.grid(row=0, column=2, sticky='nsew')

        # 配置预览区域grid布局
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(1, weight=1)

        # 添加预览标题
        tk.Label(preview_frame, text="对话预览", font=("Arial", 13)).grid(row=0, column=0, sticky='w', pady=(0, 5))

        # 添加预览文本框
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame, 
            wrap=tk.WORD, 
            state=tk.DISABLED, 
            font=('Arial', 12)
        )
        # 阻止所有缩放事件
        self.preview_text.bind('<Control-MouseWheel>', lambda e: "break")
        self.preview_text.bind('<Control-Button-4>', lambda e: "break")  # Linux zoom prevention
        self.preview_text.bind('<Control-Button-5>', lambda e: "break")  # Linux zoom prevention
        self.preview_text.bind('<Control-plus>', lambda e: "break")  # 阻止Ctrl+加号
        self.preview_text.bind('<Control-minus>', lambda e: "break")  # 阻止Ctrl+减号
        self.preview_text.bind('<Control-equal>', lambda e: "break")  # 阻止Ctrl+等号
        self.preview_text.grid(row=1, column=0, sticky='nsew')

        # 添加按钮容器
        button_frame = tk.Frame(self.history_window)
        button_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 10))

        # 添加加载按钮
        load_button = tk.Button(button_frame, text="加载", command=self.load_selected_history, width=10)
        load_button.pack(side=tk.LEFT, padx=5)

        # 添加删除按钮
        delete_button = tk.Button(button_frame, text="删除", command=self.delete_selected_history, width=10)
        delete_button.pack(side=tk.LEFT, padx=5)

        # 添加关闭按钮
        close_button = tk.Button(button_frame, text="关闭", command=self.history_window.destroy, width=10)
        close_button.pack(side=tk.RIGHT)

        # 加载历史文件列表
        self.load_history_files()

        # 绑定选择事件
        self.file_listbox.bind("<<TreeviewSelect>>", self.show_preview)

    def load_history_files(self):
        """加载历史文件列表"""
        self.file_listbox.delete(*self.file_listbox.get_children())
        try:
            files = [f for f in os.listdir(self.history_dir) if f.endswith(".json")]
            for file in sorted(files, reverse=True):
                self.file_listbox.insert("", tk.END, text=file)
        except Exception as e:
            messagebox.showerror("错误", f"无法加载历史文件: {str(e)}")

    def show_preview(self, event):
        """显示选中文件的预览"""
        selection = self.file_listbox.selection()
        if not selection:
            return

        selected_file = self.file_listbox.item(selection[0], "text")
        file_path = os.path.join(self.history_dir, selected_file)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
                self.preview_text.config(state=tk.NORMAL)
                self.preview_text.delete(1.0, tk.END)
                
                # 配置红色文本标签
                self.preview_text.tag_config('red', foreground='red')
                
                for msg in history[-10:]:  # 显示最后10条消息
                    role = msg["role"].capitalize()
                    content = msg["content"][:100] + "..."
                    
                    # 插入带格式的文本
                    self.preview_text.insert(tk.END, role + ": ", 'red')
                    self.preview_text.insert(tk.END, content + "\n\n")
                
                self.preview_text.config(state=tk.DISABLED)
        except Exception as e:
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, f"无法加载预览: {str(e)}")
            self.preview_text.config(state=tk.DISABLED)

    def load_selected_history(self):
        """加载选中的历史对话"""
        selection = self.file_listbox.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个历史文件")
            return

        selected_file = self.file_listbox.item(selection[0], "text")
        file_path = os.path.join(self.history_dir, selected_file)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
                self.history_window.destroy()
                self.conversation_history = history
                
                # 更新系统提示词
                system_messages = [msg for msg in history if msg["role"] == "system"]
                if system_messages:
                    self.system_prompt = system_messages[0]["content"]
                    # 更新系统提示词管理器
                    if self.system_prompt_manager:
                        self.system_prompt_manager.system_prompt = self.system_prompt
                        # 如果系统提示词窗口已打开，则更新显示
                        if (hasattr(self.system_prompt_manager, 'system_prompt_window') and
                            self.system_prompt_manager.system_prompt_window and
                            self.system_prompt_manager.system_prompt_window.winfo_exists()):
                            self.system_prompt_manager.update_system_prompt_display()
                
                # 更新聊天显示
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.delete("1.0", tk.END)
                # 过滤掉system消息显示
                for msg in history:
                    if msg["role"] != "system":
                        self.display_message(msg["role"].capitalize(), msg["content"])
                
                messagebox.showinfo("成功", "历史对话已加载（系统提示词已加载）")
        except json.JSONDecodeError as e:
            messagebox.showerror("错误", f"文件格式错误: {str(e)}")
        except FileNotFoundError:
            messagebox.showerror("错误", "文件不存在，可能已被删除")
        except Exception as e:
            messagebox.showerror("错误", f"加载历史文件时出错: {str(e)}")

    def delete_selected_history(self):
        """删除选中的历史对话"""
        selection = self.file_listbox.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个历史文件")
            return

        selected_file = self.file_listbox.item(selection[0], "text")
        file_path = os.path.join(self.history_dir, selected_file)

        try:
            os.remove(file_path)
            self.load_history_files()
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.config(state=tk.DISABLED)
            messagebox.showinfo("成功", "历史文件已删除")
        except Exception as e:
            messagebox.showerror("错误", f"无法删除文件: {str(e)}")

    def show_loading(self, message="加载中..."):
        """显示加载指示器"""
        self.loading_label.config(text=message)
        self.root.update()

    def hide_loading(self):
        """隐藏加载指示器"""
        self.loading_label.config(text="")
        self.root.update()

    def display_message(self, sender, message):
        """显示消息到聊天窗口"""
        # 配置红色文本标签
        self.chat_display.tag_config('red', foreground='red')
        
        self.chat_display.config(state='normal')  # 启用编辑
        # 插入带格式的文本
        self.chat_display.insert(tk.END, sender + ": ", 'red')
        self.chat_display.insert(tk.END, message + "\n\n")
        self.chat_display.config(state='disabled')  # 禁用编辑
        self.chat_display.yview(tk.END)  # 自动滚动到底部        
        # 如果是AI的回复，显示在弹出窗口
        if sender == self.selected_model.get():
            self.show_popup(message)
    
    def show_popup(self, message):
        """显示最新回复的弹出窗口"""
        self.popup = tk.Toplevel(self.root)
        self.popup.title("最新回复")
        self.popup.geometry("600x400")
        
        # 创建主容器
        main_frame = tk.Frame(self.popup)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 配置网格布局
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 创建文本容器
        text_container = tk.Frame(main_frame)
        text_container.grid(row=0, column=0, sticky='nsew')
        
        # 配置文本容器网格
        text_container.grid_rowconfigure(0, weight=1)
        text_container.grid_columnconfigure(0, weight=1)
        
        # 创建文本框
        self.popup_text_box = tk.Text(
            text_container, 
            wrap=tk.WORD, 
            font=('Arial', 12),
            width=80,  # Initial width in characters
            height=20  # Initial height in lines
        )
        self.popup_text_box.insert(tk.END, message)
        self.popup_text_box.config(state='disabled')
        
        # 添加垂直滚动条
        v_scroll = ttk.Scrollbar(text_container, orient=tk.VERTICAL, command=self.popup_text_box.yview)
        self.popup_text_box.config(yscrollcommand=v_scroll.set)
        
        # 布局文本框和滚动条
        self.popup_text_box.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        
        # 配置网格权重
        text_container.grid_rowconfigure(0, weight=1)
        text_container.grid_columnconfigure(0, weight=1)
        
        # 添加字体缩放功能
        self.popup_text_box.bind('<Control-MouseWheel>', self.zoom_popup_font)

        
        # 初始化弹出窗口字体大小
        self.popup_font_size = 12
        
        # 创建按钮容器
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky='ew', pady=(10, 0))
        
        # 配置按钮容器列权重
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # 添加复制按钮
        copy_button = tk.Button(button_frame, text="复制", command=lambda: self.copy_to_clipboard(message), width=10)
        copy_button.grid(row=0, column=0, padx=5)
        
        # 添加保存为.md文件按钮
        save_button = tk.Button(button_frame, text="保存", command=lambda: self.save_as_md(message), width=10)
        save_button.grid(row=0, column=1, padx=5)

        # 允许窗口大小调整
        self.popup.resizable(True, True)
        
        # 绑定窗口大小变化事件
        self.popup.bind('<Configure>', self.handle_popup_resize)
        
        # 绑定字体缩放事件
        def zoom_font(event):
            if event.delta > 0:  # 向上滚动
                self.font_size = min(self.font_size + 1, self.max_font_size)
            else:  # 向下滚动
                self.font_size = max(self.font_size - 1, self.min_font_size)
            
            # 更新弹出窗口字体
            self.popup_text_box.config(font=('Arial', self.font_size))
            self.popup_text_box.update_idletasks()
        
        self.popup_text_box.bind('<Control-MouseWheel>', zoom_font)

        

    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("成功", "文本已复制到剪贴板")

    def zoom_font(self, event):
        """通过Ctrl+鼠标滚轮缩放聊天窗口字体"""
        # 保存当前滚动位置
        chat_scroll_position = self.chat_display.yview()
        
        # 计算缩放方向
        if event.delta > 0:  # 向上滚动
            self.font_size = min(self.font_size + 1, self.max_font_size)
        else:  # 向下滚动
            self.font_size = max(self.font_size - 1, self.min_font_size)
        
        # 更新聊天窗口字体
        self.chat_display.config(font=('Arial', self.font_size))
        
        
        # 强制更新布局
        self.chat_display.update_idletasks()
        
        # 恢复滚动位置
        self.chat_display.yview_moveto(chat_scroll_position[0])

    def handle_popup_resize(self, event):
        """处理弹出窗口大小变化"""
        if not hasattr(self, 'popup_text_box') or not self.popup_text_box.winfo_exists():
            return
        
        # 获取窗口新尺寸
        new_width = event.width - 20  # 减去padding
        new_height = event.height - 100  # 减去按钮区域高度
        
        # 更新文本框尺寸
        self.popup_text_box.config(width=new_width, height=new_height)
        self.popup_text_box.update_idletasks()

    def zoom_popup_font(self, event):
        """通过Ctrl+鼠标滚轮缩放弹出窗口字体"""
        # 计算缩放方向
        if event.delta > 0:  # 向上滚动
            self.font_size = min(self.font_size + 1, self.max_font_size)
        else:  # 向下滚动
            self.font_size = max(self.font_size - 1, self.min_font_size)
        
        # 更新弹出窗口字体
        if hasattr(self, 'popup_text_box') and self.popup_text_box.winfo_exists():
            self.popup_text_box.config(font=('Arial', self.font_size))
            self.popup_text_box.update_idletasks()
        
        # 更新主聊天窗口字体
        self.chat_display.config(font=('Arial', self.font_size))
        self.chat_display.update_idletasks()

    def update_fonts(self):
        """更新聊天窗口字体大小"""
        # 获取聊天窗口当前尺寸
        chat_height = int(self.chat_display.cget('height'))
        chat_width = int(self.chat_display.cget('width'))
        
        # 更新聊天窗口字体
        self.chat_display.config(
            font=('Arial', self.font_size),
            height=chat_height,
            width=chat_width,
            wrap=tk.WORD
        )
        
        # 强制更新布局
        self.chat_display.update_idletasks()

    def save_as_md(self, text):
        """将文本保存为.md文件"""

        file_path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown文件", "*.md")],
            initialdir="ai_answer")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(text)
                messagebox.showinfo("成功", f"文件已保存为 {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存文件时出错: {str(e)}")

    def handle_enter_key(self, event):
        # 如果按下Shift+Enter，插入换行符
        if event.state & 0x0001:  # 检查Shift键
            self.user_input.insert(tk.INSERT, '\n')
            return 'break'  # 阻止默认行为
        # 否则发送消息
        self.send_message()
        return 'break'  # 阻止默认行为

    def undo_last_message(self):
        """撤回最后一条消息"""
        if len(self.conversation_history) < 2:  # 至少需要一条用户消息和一条AI回复
            messagebox.showwarning("警告", "没有可撤回的消息")
            return

        # 移除最后两条消息（用户消息和AI回复）
        self.conversation_history = self.conversation_history[:-2]
        
        # 更新聊天显示
        self.chat_display.config(state='normal')
        self.chat_display.delete("1.0", tk.END)
        
        # 重新显示剩余的历史消息
        for msg in self.conversation_history:
            if msg["role"] != "system":  # 不显示系统提示
                self.display_message(msg["role"].capitalize(), msg["content"])
        
        self.chat_display.config(state='disabled')
        self.display_message("系统", "已撤回最后一条对话")

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        self.chat_display.config(state='normal')  # 启用编辑
        self.chat_display.delete("1.0", tk.END)  # 清空聊天框
        self.chat_display.config(state='disabled')  # 禁用编辑
        self.display_message("系统", "对话历史已清空")

    def send_message(self):
        # 获取用户输入并限制最大长度
        user_message = self.user_input.get("1.0", tk.END).strip()
        if user_message == "":
            return

        # 限制消息长度（例如8000字符）
        if len(user_message) > 80000:
            self.display_message("系统", "消息过长,请缩短至80000字符以内")
            return

        # 显示用户消息
        self.display_message("User", user_message)
        self.user_input.delete("1.0", tk.END)  # 清空输入框

        # 启动一个新线程来处理API请求
        threading.Thread(target=self.get_deepseek_response_thread, args=(user_message,)).start()

    def get_deepseek_response_thread(self, user_message):
        """在新线程中调用DeepSeek API获取回复"""
        # 显示加载指示器
        self.show_loading("正在处理请求，请稍候...")

        # 如果历史为空，添加系统提示
        if not self.conversation_history:
            self.conversation_history.append({"role": "system", "content": self.system_prompt})

        # 添加用户消息
        self.conversation_history.append({"role": "user", "content": user_message})

        # 限制历史长度
        if len(self.conversation_history) > self.max_history_length * 2:
            # 检查是否包含 system 消息
            system_messages = [msg for msg in self.conversation_history if msg["role"] == "system"]
            if system_messages:
                # 保留第一条 system 消息
                system_message = system_messages[0]
                self.conversation_history = [system_message] + self.conversation_history[-self.max_history_length * 2 + 1:]
            else:
                # 如果没有 system 消息，删除历史后重新添加 system_prompt
                self.conversation_history = self.conversation_history[-self.max_history_length * 2:]
                self.conversation_history.insert(0, {"role": "system", "content": self.system_prompt})

        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.selected_model.get(),  # 使用选择的模型
            "messages": self.conversation_history,
            "temperature": self.temperature_options[self.selected_temperature.get()],  # 使用选择的温度值
            "max_tokens": self.max_tokens
        }

        # 重试机制
        max_retries = 3
        retry_delay = 30  # 重试间隔时间（秒）

        # 启动计时器
        start_time = time.time()

        for attempt in range(max_retries):
            try:
                # 移除超时限制
                response = requests.post(self.API_URL, headers=headers, json=data, timeout=None)
                response.raise_for_status()
                
                #检查传参
                print("temperature:",data["temperature"])
                print("max_tokens:",data["max_tokens"])
                print("API 响应:", response.json()['usage']) 

                ai_response = response.json()['choices'][0]['message']['content']
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                self.hide_loading()
                # 在主线程中显示AI回复
                self.root.after(0, self.display_message, self.selected_model.get(), ai_response)
                return
            except requests.exceptions.Timeout:
                # 检查是否超过 5 分钟
                if time.time() - start_time > 300:  # 300 秒 = 5 分钟
                    self.hide_loading()
                    self.root.after(0, self.show_timeout_popup)  # 显示超时弹窗
                    return
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                self.hide_loading()
                self.root.after(0, self.display_message, "系统", "请求超时，请检查网络连接后重试")
                return
            except requests.exceptions.RequestException as e:
                # 如果API调用失败，移除最后一条用户消息
                self.conversation_history.pop()
                self.hide_loading()
                
                # 获取更多错误详情
                error_details = str(e)
                if hasattr(e, 'response'):
                    try:
                        error_details = f"Status Code: {e.response.status_code}\n"
                        if e.response.status_code == 401:
                            error_details += "认证失败：请检查API密钥是否正确"
                        elif e.response.status_code == 429:
                            error_details += "请求过多：已达到速率限制，请稍后重试"
                        elif 500 <= e.response.status_code < 600:
                            error_details += "服务器错误：API服务端出现问题"
                        else:
                            error_details += f"响应内容: {e.response.text[:200]}"
                    except:
                        error_details = str(e)
                
                self.root.after(0, self.display_message, "系统", 
                    f"API请求失败\n"
                    f"错误类型: {type(e).__name__}\n"
                    f"详细信息:\n{error_details}\n"
                    f"请检查网络连接和API配置后重试")

                return
            except (KeyError, ValueError) as e:
                self.conversation_history.pop()
                self.hide_loading()
                self.root.after(0, self.display_message, "系统", f"解析API响应失败: {str(e)}")
                return
        self.hide_loading()
        self.root.after(0, self.display_message, "系统", "请求失败，请稍后重试")

    def show_timeout_popup(self):
        """显示超时弹窗"""
        popup = tk.Toplevel(self.root)
        popup.title("请求超时")
        popup.geometry("400x200")

        # 添加提示信息
        message = "等待时间过长，请访问 官网确认 AI 服务是否可用。"
        tk.Label(popup, text=message, wraplength=350, justify="left").pack(pady=20, padx=20)


        # 添加关闭按钮
        ttk.Button(popup, text="关闭", command=popup.destroy).pack(pady=10)

    def open_settings(self):
        """打开设置窗口"""
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("设置")
        self.settings_window.geometry("400x300")

        # 使用 grid 布局
        self.settings_window.grid_columnconfigure(1, weight=1)

        # 添加 API URL 输入框
        tk.Label(self.settings_window, text="API URL:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.api_url_entry = ttk.Entry(self.settings_window, width=40)
        self.api_url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.api_url_entry.insert(0, self.API_URL)  # 显示当前 API URL

        # 添加 API Key 输入框
        tk.Label(self.settings_window, text="API Key:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.api_key_entry = ttk.Entry(self.settings_window, width=40)
        self.api_key_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.api_key_entry.insert(0, self.API_KEY)  # 显示当前 API Key

        # 添加最大历史对话数输入框
        tk.Label(self.settings_window, text="最大历史对话数:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.max_history_entry = ttk.Entry(self.settings_window, width=40)
        self.max_history_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.max_history_entry.insert(0, str(self.max_history_length))  # 显示当前最大历史对话数

        # 添加最大 Token 数输入框
        tk.Label(self.settings_window, text="最大 Token 数:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.max_tokens_entry = ttk.Entry(self.settings_window, width=40)
        self.max_tokens_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        self.max_tokens_entry.insert(0, str(self.max_tokens))  # 显示当前最大 Token 数

        # 添加保存按钮
        save_button = tk.Button(self.settings_window, text="保存", command=self.save_settings, width=10)
        save_button.grid(row=4, column=0, columnspan=2, pady=20)

    def save_settings(self):
        """保存设置"""
        try:
            # 获取用户输入的值
            new_api_url = self.api_url_entry.get().strip()
            new_api_key = self.api_key_entry.get().strip()
            new_max_history = int(self.max_history_entry.get().strip())
            new_max_tokens = int(self.max_tokens_entry.get().strip())

            # 更新实例变量
            self.API_URL = new_api_url
            self.API_KEY = new_api_key
            self.max_history_length = new_max_history
            self.max_tokens = new_max_tokens

            # 保存配置到文件
            save_config({
                "API_URL": self.API_URL,
                "API_KEY": self.API_KEY,
                "max_history_length": self.max_history_length,
                "max_tokens": self.max_tokens
            },self.CONFIG_FILE)

            # 显示成功消息
            messagebox.showinfo("成功", "设置已保存")
            self.settings_window.destroy()  # 关闭设置窗口
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字（最大历史记录长度和最大 Token 数必须为整数）")

    def open_prompts_manager(self):
        """打开 Prompts 管理界面"""
        self.prompts_manager.open_prompts_manager()

    def open_system_prompt_editor(self):
        """打开系统提示词编辑窗口"""
        self.system_prompt_manager.open_system_prompt_editor()



if __name__ == "__main__":
    # 默认配置,实测max_tokens=8000好于8192
    DEFAULT_CONFIG = {
        "API_URL": "youapiurl",
        "API_KEY": "youapi",
        "max_history_length": 100,
        "max_tokens": 8000 
    }

    root = tk.Tk()
    app = DeepSeekChatApp(root)
    root.mainloop()
