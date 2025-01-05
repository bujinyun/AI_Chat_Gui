import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
import requests
import time
import threading
import json
import os
import webbrowser

# 默认配置
DEFAULT_CONFIG = {
    "API_URL": "https://api.deepseek.com/chat/completions",
    "API_KEY": "your_api_key",
    "max_history_length": 36,
    "max_tokens": 8000
}

# 配置文件路径
CONFIG_FILE = "config.json"

# Prompts 文件存储目录
PROMPTS_DIR = "prompts"
if not os.path.exists(PROMPTS_DIR):
    os.makedirs(PROMPTS_DIR)

# 加载配置文件
def load_config():
    """从 config.json 文件中加载配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
                config = json.load(file)
                return config
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            return DEFAULT_CONFIG
    else:
        return DEFAULT_CONFIG

# 保存配置文件
def save_config(config):
    """将配置保存到 config.json 文件中"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
            json.dump(config, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存配置文件失败: {str(e)}")

# 加载初始配置
config = load_config()
API_URL = config.get("API_URL", DEFAULT_CONFIG["API_URL"])
API_KEY = config.get("API_KEY", DEFAULT_CONFIG["API_KEY"])

class DeepSeekChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DeepSeek Chat")

        # 加载配置
        self.max_history_length = config.get("max_history_length", DEFAULT_CONFIG["max_history_length"])
        self.max_tokens = config.get("max_tokens", DEFAULT_CONFIG["max_tokens"])

        # 参数设置
        self.temperature = 1.0  # 默认温度参数
        self.conversation_history = []  # 初始化对话历史
        self.system_prompt = ""  # 默认系统提示词

        # 模型选择
        self.models = ["deepseek-chat"]  # 可用的模型列表
        self.selected_model = tk.StringVar(value=self.models[0])  # 默认选择第一个模型

        # 创建控制面板
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(padx=10, pady=5, fill=tk.X)

        # 添加模型选择下拉菜单
        tk.Label(self.control_frame, text="选择模型:").pack(side=tk.LEFT)
        self.model_menu = tk.OptionMenu(self.control_frame, self.selected_model, *self.models)
        self.model_menu.pack(side=tk.LEFT, padx=(5, 10))

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
        self.temperature_menu = tk.OptionMenu(self.control_frame, self.selected_temperature, *self.temperature_options.keys())
        self.temperature_menu.pack(side=tk.LEFT)

        # 添加 Prompts 管理按钮
        self.prompts_button = tk.Button(self.control_frame, text="管理Prompts", command=self.open_prompts_manager)
        self.prompts_button.pack(side=tk.RIGHT, padx=(10, 0))

        # 添加设置按钮
        self.settings_button = tk.Button(self.control_frame, text="设置", command=self.open_settings)
        self.settings_button.pack(side=tk.RIGHT, padx=(10, 0))

        # 添加系统提示词按钮
        self.system_prompt_button = tk.Button(self.control_frame, text="系统提示词", command=self.open_system_prompt_editor)
        self.system_prompt_button.pack(side=tk.RIGHT, padx=(10, 0))

        # 创建聊天显示区域
        self.chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled')
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 创建输入框和发送按钮
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(padx=10, pady=10, fill=tk.X)

        # 使用Text控件代替Entry，并添加滚动条
        self.user_input = tk.Text(self.input_frame, height=5, wrap=tk.WORD)
        self.user_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 添加垂直滚动条
        scrollbar = tk.Scrollbar(self.input_frame, command=self.user_input.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.user_input.config(yscrollcommand=scrollbar.set)

        # 创建按钮容器
        self.button_frame = tk.Frame(self.input_frame)
        self.button_frame.pack(side=tk.RIGHT, padx=(10, 0), fill=tk.Y)

        # 发送按钮（变大）
        self.send_button = tk.Button(self.button_frame, text="发送", command=self.send_message, width=10, height=2)
        self.send_button.pack(side=tk.BOTTOM, pady=(0, 5))

        # 清空历史按钮
        self.clear_history_button = tk.Button(self.button_frame, text="清空历史", command=self.clear_history, width=10)
        self.clear_history_button.pack(side=tk.TOP, pady=(0, 5))

        # 保存历史按钮
        self.save_history_button = tk.Button(self.button_frame, text="保存历史", command=self.save_history_as_md, width=10)
        self.save_history_button.pack(side=tk.TOP)

        # 添加加载指示器
        self.loading_label = tk.Label(root, text="", fg="blue")
        self.loading_label.pack()

        # 绑定回车键发送消息（注意：现在需要处理多行输入）
        self.root.bind('<Return>', self.handle_enter_key)

        # 自动加载本地 Prompts
        self.load_local_prompts()

    def save_history_as_md(self):
        """将当前历史对话保存为 .md 文件"""
        if not self.conversation_history:
            messagebox.showwarning("警告", "当前没有历史对话可保存")
            return

        # 生成 Markdown 格式的对话内容
        md_content = "# 历史对话记录\n\n"
        for message in self.conversation_history:
            role = message["role"]
            content = message["content"]
            md_content += f"**{role.capitalize()}**: {content}\n\n"

        # 弹出文件保存对话框
        file_path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown文件", "*.md")])
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(md_content)
                messagebox.showinfo("成功", f"历史对话已保存为 {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存文件时出错: {str(e)}")

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
        self.chat_display.config(state='normal')  # 启用编辑
        self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_display.config(state='disabled')  # 禁用编辑
        self.chat_display.yview(tk.END)  # 自动滚动到底部        
        # 如果是AI的回复，显示在弹出窗口
        if sender == "DeepSeek":
            self.show_popup(message)
    
    def show_popup(self, message):
        """显示最新回复的弹出窗口"""
        popup = tk.Toplevel(self.root)
        popup.title("最新回复")
        popup.geometry("600x400")
        
        # 创建文本框
        text_box = scrolledtext.ScrolledText(popup, wrap=tk.WORD)
        text_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_box.insert(tk.END, message)
        text_box.config(state='disabled')
        
        # 创建按钮容器
        button_frame = tk.Frame(popup)
        button_frame.pack(side=tk.BOTTOM, pady=10)
        
        # 添加复制按钮
        copy_button = tk.Button(button_frame, text="复制", command=lambda: self.copy_to_clipboard(message), width=10)
        copy_button.pack(side=tk.LEFT, padx=5)
        
        # 添加保存为.md文件按钮
        save_button = tk.Button(button_frame, text="保存", command=lambda: self.save_as_md(message), width=10)
        save_button.pack(side=tk.LEFT, padx=5)

    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("成功", "文本已复制到剪贴板")

    def save_as_md(self, text):
        """将文本保存为.md文件"""
        file_path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown文件", "*.md")])
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
        self.display_message("你", user_message)
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
            "Authorization": f"Bearer {API_KEY}",
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
                response = requests.post(API_URL, headers=headers, json=data, timeout=None)
                response.raise_for_status()

                ai_response = response.json()['choices'][0]['message']['content']
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                self.hide_loading()
                # 在主线程中显示AI回复
                self.root.after(0, self.display_message, "DeepSeek", ai_response)
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
                self.root.after(0, self.display_message, "系统", f"网络连接出现问题，检查api后重试。错误信息：{str(e)}")
                return
            except (KeyError, ValueError) as e:
                self.conversation_history.pop()
                self.hide_loading()
                self.root.after(0, self.display_message, "系统", f"解析API响应失败,请稍后重试。错误信息：{str(e)}")
                return
        self.hide_loading()
        self.root.after(0, self.display_message, "系统", "请求失败，请稍后重试")

    def show_timeout_popup(self):
        """显示超时弹窗"""
        popup = tk.Toplevel(self.root)
        popup.title("请求超时")
        popup.geometry("400x200")

        # 添加提示信息
        message = "等待时间过长，请访问 DeepSeek 官网确认 AI 服务是否可用。"
        tk.Label(popup, text=message, wraplength=350, justify="left").pack(pady=20, padx=20)

        # 添加访问官网按钮
        def open_website():
            webbrowser.open("https://status.deepseek.com/")

        tk.Button(popup, text="访问官网", command=open_website).pack(pady=10)

        # 添加关闭按钮
        tk.Button(popup, text="关闭", command=popup.destroy).pack(pady=10)

    def open_settings(self):
        """打开设置窗口"""
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("设置")
        self.settings_window.geometry("400x300")

        # 使用 grid 布局
        self.settings_window.grid_columnconfigure(1, weight=1)

        # 添加 API URL 输入框
        tk.Label(self.settings_window, text="API URL:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.api_url_entry = tk.Entry(self.settings_window, width=40)
        self.api_url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.api_url_entry.insert(0, API_URL)  # 显示当前 API URL

        # 添加 API Key 输入框
        tk.Label(self.settings_window, text="API Key:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.api_key_entry = tk.Entry(self.settings_window, width=40)
        self.api_key_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.api_key_entry.insert(0, API_KEY)  # 显示当前 API Key

        # 添加最大历史记录长度输入框
        tk.Label(self.settings_window, text="最大历史记录长度:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.max_history_entry = tk.Entry(self.settings_window, width=40)
        self.max_history_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.max_history_entry.insert(0, str(self.max_history_length))  # 显示当前最大历史记录长度

        # 添加最大 Token 数输入框
        tk.Label(self.settings_window, text="最大 Token 数:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.max_tokens_entry = tk.Entry(self.settings_window, width=40)
        self.max_tokens_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        self.max_tokens_entry.insert(0, str(self.max_tokens))  # 显示当前最大 Token 数

        # 添加保存按钮
        save_button = tk.Button(self.settings_window, text="保存", command=self.save_settings)
        save_button.grid(row=4, column=0, columnspan=2, pady=20)

    def save_settings(self):
        """保存设置"""
        try:
            # 获取用户输入的值
            new_api_url = self.api_url_entry.get().strip()
            new_api_key = self.api_key_entry.get().strip()
            new_max_history = int(self.max_history_entry.get().strip())
            new_max_tokens = int(self.max_tokens_entry.get().strip())

            # 更新全局变量
            global API_URL, API_KEY
            API_URL = new_api_url
            API_KEY = new_api_key

            # 更新实例变量
            self.max_history_length = new_max_history
            self.max_tokens = new_max_tokens

            # 保存配置到文件
            save_config({
                "API_URL": API_URL,
                "API_KEY": API_KEY,
                "max_history_length": self.max_history_length,
                "max_tokens": self.max_tokens
            })

            # 显示成功消息
            messagebox.showinfo("成功", "设置已保存")
            self.settings_window.destroy()  # 关闭设置窗口
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字（最大历史记录长度和最大 Token 数必须为整数）")

    def load_local_prompts(self):
        """自动加载本地 Prompts"""
        self.prompts = []
        for filename in os.listdir(PROMPTS_DIR):
            if filename.endswith(".json"):
                file_path = os.path.join(PROMPTS_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        prompt_data = json.load(file)
                        self.prompts.append((filename, prompt_data))
                except Exception as e:
                    print(f"加载 {filename} 失败: {str(e)}")

    def open_prompts_manager(self):
        """打开 Prompts 管理界面"""
        self.prompts_manager = tk.Toplevel(self.root)
        self.prompts_manager.title("Prompts 管理")
        self.prompts_manager.geometry("600x500")  # 增加窗口高度

        # 使用 grid 布局
        self.prompts_manager.grid_columnconfigure(0, weight=1)
        self.prompts_manager.grid_rowconfigure(1, weight=1)

        # 添加搜索框
        search_frame = tk.Frame(self.prompts_manager)
        search_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        tk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = tk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", self.filter_prompts)  # 绑定键盘释放事件

        # 创建 Treeview 显示 Prompts
        self.tree = ttk.Treeview(self.prompts_manager, columns=("Name", "Content"), show="headings")
        self.tree.heading("Name", text="名称")
        self.tree.heading("Content", text="内容")
        self.tree.column("Name", width=200)  # 设置名称列宽度为 200
        self.tree.column("Content", width=400)  # 设置内容列宽度为 400
        self.tree.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # 填充 Treeview
        self.update_treeview()

        # 添加 Prompts 名称输入框
        tk.Label(self.prompts_manager, text="Prompts 名称:").grid(row=2, column=0, padx=10, pady=(10, 0), sticky="w")
        self.prompt_name_entry = tk.Entry(self.prompts_manager, width=40)  # 缩小输入框宽度
        self.prompt_name_entry.grid(row=2, column=1, padx=10, pady=(10, 0), sticky="w")

        # 添加 Prompts 内容输入框
        tk.Label(self.prompts_manager, text="Prompts 内容:").grid(row=3, column=0, padx=10, pady=(10, 0), sticky="w")
        self.new_prompt_input = tk.Text(self.prompts_manager, height=5, wrap=tk.WORD, width=40)  # 缩小输入框宽度
        self.new_prompt_input.grid(row=3, column=1, padx=10, pady=(10, 0), sticky="nsew")

        # 添加按钮容器
        button_frame = tk.Frame(self.prompts_manager)
        button_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # 添加选择按钮
        select_button = tk.Button(button_frame, text="使用", command=self.select_prompt, width=10)
        select_button.pack(side=tk.LEFT, padx=5)

        # 添加保存按钮
        save_button = tk.Button(button_frame, text="保存", command=self.save_new_prompt, width=10)
        save_button.pack(side=tk.RIGHT, padx=5)

        # 添加打开 Prompts 按钮
        open_prompt_button = tk.Button(button_frame, text="预览Prompts", command=self.open_selected_prompt, width=10)
        open_prompt_button.pack(side=tk.LEFT, padx=5)

        # 添加复制到系统提示词按钮
        copy_to_system_prompt_button = tk.Button(button_frame, text="复制到系统提示词", command=self.copy_to_system_prompt, width=15)
        copy_to_system_prompt_button.pack(side=tk.LEFT, padx=5)

        # 添加删除按钮
        delete_button = tk.Button(button_frame, text="删除", command=self.delete_selected_prompt, width=10)
        delete_button.pack(side=tk.RIGHT, padx=5)

        # 配置 Treeview 和输入框的权重
        self.prompts_manager.grid_rowconfigure(1, weight=1)  # Treeview 占据更多空间
        self.prompts_manager.grid_rowconfigure(3, weight=1)  # 内容输入框占据更多空间
        self.prompts_manager.grid_columnconfigure(1, weight=1)  # 输入框和 Treeview 的列占据更多空间

    def copy_to_system_prompt(self):
        """将选定的 Prompts 复制到系统提示词窗口"""
        selected_item = self.tree.selection()
        if selected_item:
            prompt_name = self.tree.item(selected_item, "values")[0]
            for prompt in self.prompts:
                if prompt[0] == prompt_name:
                    # 打开系统提示词窗口
                    self.open_system_prompt_editor()
                    # 将 Prompts 内容复制到系统提示词窗口
                    self.system_prompt_text.delete("1.0", tk.END)
                    self.system_prompt_text.insert(tk.END, prompt[1]["content"])
                    break
        else:
            messagebox.showwarning("警告", "请先选择一个 Prompts")

    def filter_prompts(self, event=None):
        """根据搜索框内容筛选 Prompts"""
        search_term = self.search_entry.get().strip().lower()  # 获取搜索关键词并转换为小写
        self.tree.delete(*self.tree.get_children())  # 清空 Treeview

        # 遍历所有 Prompts，筛选出匹配的记录
        for prompt in self.prompts:
            prompt_name = prompt[0].lower()
            prompt_content = prompt[1]["content"].lower()
            if search_term in prompt_name or search_term in prompt_content:
                self.tree.insert("", tk.END, values=(prompt[0], prompt[1]["content"][:50] + "..."))

    def update_treeview(self):
        """更新 Treeview 显示内容"""
        self.tree.delete(*self.tree.get_children())  # 清空 Treeview
        for prompt in self.prompts:
            self.tree.insert("", tk.END, values=(prompt[0], prompt[1]["content"][:50] + "..."))

    def open_selected_prompt(self):
        """打开已加载的 Prompts 文件"""
        selected_item = self.tree.selection()
        if selected_item:
            prompt_name = self.tree.item(selected_item, "values")[0]
            for prompt in self.prompts:
                if prompt[0] == prompt_name:
                    # 将 Prompts 内容显示在输入框中
                    self.new_prompt_input.delete("1.0", tk.END)  # 清空输入框
                    self.new_prompt_input.insert(tk.END, prompt[1]["content"])
                    self.prompt_name_entry.delete(0, tk.END)  # 清空名称输入框
                    self.prompt_name_entry.insert(0, prompt_name.replace(".json", ""))  # 显示名称（去掉扩展名）
                    break
        else:
            messagebox.showwarning("警告", "请先选择一个 Prompts")

    def select_prompt(self):
        """选择 Prompt 并粘贴到输入框"""
        selected_item = self.tree.selection()
        if selected_item:
            prompt_name = self.tree.item(selected_item, "values")[0]
            for prompt in self.prompts:
                if prompt[0] == prompt_name:
                    # 将 Prompt 内容插入到输入框中
                    self.user_input.insert(tk.END, prompt[1]["content"])
                    self.prompts_manager.destroy()  # 关闭 Prompts 管理界面
                    break

    def save_new_prompt(self):
        """保存新的 Prompt"""
        new_prompt_content = self.new_prompt_input.get("1.0", tk.END).strip()
        if new_prompt_content:
            # 获取用户输入的 Prompts 名称
            prompt_name = self.prompt_name_entry.get().strip()
            if not prompt_name:
                # 如果用户未输入名称，使用默认名称
                prompt_name = f"prompt_{len(self.prompts) + 1}.json"
            else:
                # 确保文件扩展名为 .json
                if not prompt_name.endswith(".json"):
                    prompt_name += ".json"

            # 检查文件是否已存在
            file_path = os.path.join(PROMPTS_DIR, prompt_name)
            if os.path.exists(file_path):
                # 如果文件已存在，弹出确认对话框
                confirm = messagebox.askyesno("确认", f"文件 {prompt_name} 已存在，是否覆盖？")
                if not confirm:
                    return  # 用户选择不覆盖，直接返回

            # 保存 Prompt
            prompt_data = {"content": new_prompt_content}
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(prompt_data, file, ensure_ascii=False, indent=4)

                # 更新 Prompts 列表
                self.prompts = [(name, data) for name, data in self.prompts if name != prompt_name]  # 移除旧记录
                self.prompts.append((prompt_name, prompt_data))

                # 更新 Treeview
                self.update_treeview()

                # 清空输入框
                self.new_prompt_input.delete("1.0", tk.END)
                self.prompt_name_entry.delete(0, tk.END)  # 清空名称输入框
                messagebox.showinfo("成功", "Prompt 已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存 Prompt 失败: {str(e)}")
        else:
            messagebox.showwarning("警告", "请输入 Prompt 内容")

    def delete_selected_prompt(self):
        """删除所选的 Prompt 记录"""
        selected_item = self.tree.selection()
        if selected_item:
            # 获取选中的 Prompt 名称
            prompt_name = self.tree.item(selected_item, "values")[0]

            # 弹出二次确认对话框
            confirm = messagebox.askyesno("确认", f"确定要删除 {prompt_name} 吗？")
            if confirm:
                try:
                    # 删除文件
                    file_path = os.path.join(PROMPTS_DIR, prompt_name)
                    if os.path.exists(file_path):
                        os.remove(file_path)

                    # 从 Prompts 列表中移除
                    self.prompts = [prompt for prompt in self.prompts if prompt[0] != prompt_name]

                    # 更新 Treeview
                    self.update_treeview()

                    messagebox.showinfo("成功", f"Prompt {prompt_name} 已删除")
                except Exception as e:
                    messagebox.showerror("错误", f"删除 Prompt 失败: {str(e)}")
        else:
            messagebox.showwarning("警告", "请先选择一个 Prompts")

    def open_system_prompt_editor(self):
        """打开系统提示词编辑窗口"""
        self.system_prompt_window = tk.Toplevel(self.root)
        self.system_prompt_window.title("系统提示词")
        self.system_prompt_window.geometry("600x400")

        # 创建文本框
        self.system_prompt_text = tk.Text(self.system_prompt_window, wrap=tk.WORD, height=10)
        self.system_prompt_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.system_prompt_text.insert(tk.END, self.system_prompt)  # 显示当前系统提示词

        # 创建保存按钮
        save_button = tk.Button(self.system_prompt_window, text="保存", command=self.save_system_prompt)
        save_button.pack(pady=10)

    def save_system_prompt(self):
        """保存系统提示词"""
        new_system_prompt = self.system_prompt_text.get("1.0", tk.END).strip()
        self.system_prompt = new_system_prompt

        # 检查对话历史中是否包含 system 消息
        system_message_index = -1
        for i, message in enumerate(self.conversation_history):
            if message["role"] == "system":
                system_message_index = i
                break

        if system_message_index != -1:
            # 如果存在 system 消息，更新其内容
            self.conversation_history[system_message_index]["content"] = new_system_prompt
        else:
            # 如果不存在 system 消息，插入到对话历史的最前面
            self.conversation_history.insert(0, {"role": "system", "content": new_system_prompt})

        messagebox.showinfo("成功", "系统提示词已更新并立即生效")
        self.system_prompt_window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = DeepSeekChatApp(root)
    root.mainloop()