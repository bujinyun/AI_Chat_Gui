# DeepSeek Chat GUI

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![GUI](https://img.shields.io/badge/GUI-Tkinter-orange)

**DeepSeek Chat GUI** 是一个基于 Python 和 Tkinter 的桌面应用程序，用于与 DeepSeek API 进行交互。它提供了一个用户友好的界面，支持按使用场景设置 `temperature`、对话管理、Prompt 管理等功能。

## 功能特性

- **对话管理**：
  - 支持与 DeepSeek API 进行多轮对话。
  - 可清空对话历史。
  - 支持多行输入和快捷键发送消息（`Enter` 发送，`Shift+Enter` 换行）。

- **Prompt 管理**：
  - 支持保存、加载和删除 Prompt。
  - 支持覆盖保存同名 Prompt。
  - 提供筛选功能，方便快速查找 Prompt。
  - 支持将 Prompt 内容插入到输入框中。

- **API 配置**：
  - 支持自定义 DeepSeek API 密钥和模型选择。
  - 提供温度参数调节，适用于不同场景（如代码生成、创意写作等）。

- **用户界面**：
  - 使用 Tkinter 构建，界面简洁易用。
  - 支持弹出窗口显示最新回复，并提供复制和保存功能。

## 安装与运行

### 环境要求

- Python 3.8 或更高版本。
- 安装所需的依赖库：

```bash
pip install requests
```

### 运行步骤

1. 克隆本仓库：

```bash
git clone https://github.com/bujinyun/AI_Chat_Gui.git
cd AI_Chat_Gui
```

2. 修改 `API_KEY`：
   - 打开 `deepseek.py` 文件，将 `API_KEY` 替换为你的 DeepSeek API 密钥。

3. 运行程序：

```bash
python deepseek.py
```

## 使用说明

1. **主界面**：
   - 在输入框中输入消息，按 `Enter` 发送，或按 `Shift+Enter` 换行。
   - 使用右侧的按钮清空对话历史或管理 Prompts。

2. **Prompts 管理**：
   - 点击“管理 Prompts”按钮打开 Prompts 管理界面。
   - 在 Prompts 管理界面中，可以保存、删除、筛选和加载 Prompts。
   - 支持通过搜索框快速查找 Prompts。

3. **API 配置**：
   - 在控制面板中选择模型和温度参数，以适配不同的使用场景。

4. **保存与复制**：
   - 在弹出窗口中，可以将 AI 的回复复制到剪贴板或保存为 Markdown 文件。

## 项目结构

```
AI_Chat_Gui/
├── deepseek.py       # 主程序文件
├── prompts/                   # Prompts 存储目录
├── README.md                  # 项目说明文件
```

## 贡献指南

欢迎贡献代码！如果你有任何改进建议或发现问题，请提交 Issue 或 Pull Request。

1. Fork 本仓库。
2. 创建你的分支：`git checkout -b feature/your-feature`。
3. 提交更改：`git commit -m 'Add some feature'`。
4. 推送到分支：`git push origin feature/your-feature`。
5. 提交 Pull Request。

## 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

## 截图

### 主界面

![image-20250104143059218](C:\Users\57368\AppData\Roaming\Typora\typora-user-images\image-20250104143059218.png)

### Prompts 管理界面

![image-20250104143219050](C:\Users\57368\AppData\Roaming\Typora\typora-user-images\image-20250104143219050.png)



---

