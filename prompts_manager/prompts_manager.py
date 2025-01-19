import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from prompts_manager.system_prompt_manager import SystemPromptManager


class PromptsManager:
    def __init__(self, root, main_app=None, main_input=None, system_prompt_input=None, prompts_dir="prompts", show_copysystem_button=True):
        self.root = root
        self.main_app = main_app  # Store reference to main application
        self.show_copysystem_button = show_copysystem_button
        self.prompts_dir = prompts_dir
        self.main_input = main_input
        self.system_prompt_input = system_prompt_input
        self.prompts = []
        self.system_prompt = ""  # Initialize system_prompt attribute
        self.system_prompt_manager = None
        self.load_local_prompts()
        self.system_prompt_manager = SystemPromptManager(root, self, main_app)

    def load_local_prompts(self):
        """自动加载本地 Prompts"""
        self.prompts = []
        if not os.path.exists(self.prompts_dir):
            os.makedirs(self.prompts_dir)
            
        for filename in os.listdir(self.prompts_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.prompts_dir, filename)
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
        self.prompts_manager.geometry("600x500")

        # 使用 grid 布局
        self.prompts_manager.grid_columnconfigure(0, weight=1)
        self.prompts_manager.grid_rowconfigure(1, weight=1)

        # 添加搜索框
        search_frame = tk.Frame(self.prompts_manager)
        search_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        tk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = tk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", self.filter_prompts)

        # 创建 Treeview 显示 Prompts
        self.tree = ttk.Treeview(self.prompts_manager, columns=("Name", "Content"), show="headings")
        self.tree.heading("Name", text="名称")
        self.tree.heading("Content", text="内容")
        self.tree.column("Name", width=200)
        self.tree.column("Content", width=400)
        self.tree.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # 填充 Treeview
        self.update_treeview()

        # 添加 Prompts 名称输入框
        tk.Label(self.prompts_manager, text="Prompts 名称:").grid(row=2, column=0, padx=10, pady=(10, 0), sticky="w")
        self.prompt_name_entry = tk.Entry(self.prompts_manager, width=40)
        self.prompt_name_entry.grid(row=2, column=1, padx=10, pady=(10, 0), sticky="w")

        # 添加 Prompts 内容输入框
        tk.Label(self.prompts_manager, text="Prompts 内容:").grid(row=3, column=0, padx=10, pady=(10, 0), sticky="w")
        self.new_prompt_input = tk.Text(self.prompts_manager, height=5, wrap=tk.WORD, width=40)
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
        if self.show_copysystem_button:
            copy_to_system_prompt_button = tk.Button(button_frame, text="复制到系统提示词", command=self.copy_to_system_prompt, width=15)
            copy_to_system_prompt_button.pack(side=tk.LEFT, padx=5)

        # 添加删除按钮
        delete_button = tk.Button(button_frame, text="删除", command=self.delete_selected_prompt, width=10)
        delete_button.pack(side=tk.RIGHT, padx=5)

        # 配置 Treeview 和输入框的权重
        self.prompts_manager.grid_rowconfigure(1, weight=1)
        self.prompts_manager.grid_rowconfigure(3, weight=1)
        self.prompts_manager.grid_columnconfigure(1, weight=1)

    def copy_to_system_prompt(self):
        """将选定的 Prompts 复制到系统提示词窗口"""
        # 获取选中的 Prompt
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择一个 Prompt")
            return
            
        prompt_name = self.tree.item(selected_item, "values")[0]
        prompt_content = None
        
        # 查找选中的 Prompt 内容
        for prompt in self.prompts:
            if prompt[0] == prompt_name:
                prompt_content = prompt[1]["content"]
                break
                
        if not prompt_content:
            messagebox.showwarning("警告", "未找到选中的 Prompt 内容")
            return
            
        # 打开系统提示词编辑器
        self.system_prompt_manager.open_system_prompt_editor()
        
        # 等待编辑器初始化完成后插入内容
        def insert_content():
            try:
                if hasattr(self.system_prompt_manager, 'system_prompt_text'):
                    self.system_prompt_manager.system_prompt_text.delete("1.0", tk.END)
                    self.system_prompt_manager.system_prompt_text.insert(tk.END, prompt_content)
                else:
                    self.root.after(100, insert_content)  # 继续等待
            except Exception as e:
                messagebox.showerror("错误", f"复制失败: {str(e)}")
                
        self.root.after(100, insert_content)


    def _perform_copy(self):
        """执行实际的复制操作"""
        try:
            # 确保 system_prompt_input 已经初始化且存在
            if self.system_prompt_input is None or not self.system_prompt_input.winfo_exists():
                messagebox.showwarning("警告", "系统提示词编辑器未打开或已关闭")
                return None

            # 获取选中的 Prompt
            selected_item = self.tree.selection()
            if selected_item:
                prompt_name = self.tree.item(selected_item, "values")[0]
                for prompt in self.prompts:
                    if prompt[0] == prompt_name:
                        # 将内容复制到系统提示词输入框
                        try:
                            self.system_prompt_input.delete("1.0", tk.END)
                            self.system_prompt_input.insert(tk.END, prompt[1]["content"])
                            return prompt[1]["content"]
                        except tk.TclError as e:
                            messagebox.showwarning("警告", f"系统提示词编辑器操作失败: {str(e)}")
                            return None
                        except Exception as e:
                            messagebox.showerror("错误", f"复制操作失败: {str(e)}")
                            return None
            return None
        except Exception as e:
            messagebox.showerror("错误", f"执行复制操作失败: {str(e)}")
            return None

    def filter_prompts(self, event=None):
        """根据搜索框内容筛选 Prompts"""
        search_term = self.search_entry.get().strip().lower()
        self.tree.delete(*self.tree.get_children())

        for prompt in self.prompts:
            prompt_name = prompt[0].lower()
            prompt_content = prompt[1]["content"].lower()
            if search_term in prompt_name or search_term in prompt_content:
                self.tree.insert("", tk.END, values=(prompt[0], prompt[1]["content"][:50] + "..."))

    def update_treeview(self):
        """更新 Treeview 显示内容"""
        self.tree.delete(*self.tree.get_children())
        for prompt in self.prompts:
            self.tree.insert("", tk.END, values=(prompt[0], prompt[1]["content"][:50] + "..."))

    def open_selected_prompt(self):
        """打开已加载的 Prompts 文件"""
        selected_item = self.tree.selection()
        if selected_item:
            prompt_name = self.tree.item(selected_item, "values")[0]
            for prompt in self.prompts:
                if prompt[0] == prompt_name:
                    self.new_prompt_input.delete("1.0", tk.END)
                    self.new_prompt_input.insert(tk.END, prompt[1]["content"])
                    self.prompt_name_entry.delete(0, tk.END)
                    self.prompt_name_entry.insert(0, prompt_name.replace(".json", ""))
                    break

    def select_prompt(self):
        """选择 Prompt 并插入到主输入框"""
        selected_item = self.tree.selection()
        if selected_item:
            prompt_name = self.tree.item(selected_item, "values")[0]
            for prompt in self.prompts:
                if prompt[0] == prompt_name:
                    if self.main_input:
                        self.main_input.insert(tk.END, prompt[1]["content"])
                    return prompt[1]["content"]
        return None

    def save_new_prompt(self):
        """保存新的 Prompt"""
        new_prompt_content = self.new_prompt_input.get("1.0", tk.END).strip()
        if new_prompt_content:
            prompt_name = self.prompt_name_entry.get().strip()
            if not prompt_name:
                prompt_name = f"prompt_{len(self.prompts) + 1}.json"
            else:
                if not prompt_name.endswith(".json"):
                    prompt_name += ".json"

            file_path = os.path.join(self.prompts_dir, prompt_name)
            if os.path.exists(file_path):
                confirm = messagebox.askyesno("确认", f"文件 {prompt_name} 已存在，是否覆盖？")
                if not confirm:
                    return

            prompt_data = {"content": new_prompt_content}
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(prompt_data, file, ensure_ascii=False, indent=4)

                self.prompts = [(name, data) for name, data in self.prompts if name != prompt_name]
                self.prompts.append((prompt_name, prompt_data))
                self.update_treeview()
                self.new_prompt_input.delete("1.0", tk.END)
                self.prompt_name_entry.delete(0, tk.END)
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
                    file_path = os.path.join(self.prompts_dir, prompt_name)
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
