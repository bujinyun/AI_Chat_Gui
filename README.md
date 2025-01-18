# DeepSeek Chat GUI

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![GUI](https://img.shields.io/badge/GUI-Tkinter-orange)

**DeepSeek Chat GUI** 是一个基于 Python 和 Tkinter 的桌面应用程序，用于与 DeepSeek API 进行交互。它提供了一个用户友好的界面，支持按使用场景设置 `temperature`、配置API+max_token、对话管理、系统提示词管理、Prompt 管理、历史对话管理等功能。

## 功能特性

- **对话管理**：
  - 支持与 DeepSeek API 进行多轮对话。
  - 可清空对话历史。
  - 支持多行输入和快捷键发送消息（`Enter` 发送，`Shift+Enter` 换行）。
- **参数配置**：
  - 支持自定义 DeepSeek API 密钥和模型选择。
  - 提供温度参数调节，适用于不同场景（如代码生成、创意写作等）。
  - 更改max_token参数，调整最大输出
  - 更改最大上下文历史的对话数，同时还保留系统提示词
- **Prompt 管理**：
  - 支持保存、加载和删除 Prompt。
  - 支持覆盖保存同名 Prompt。
  - 提供筛选功能，方便快速查找 Prompt。
  - 支持将 Prompt 内容插入到输入框中。
  - 支持将 Prompt 内容插入到系统提示词中。
- **系统提示词管理**：
  - 自定义写入system内容。
  - system部分不会因对话数过长而被删除
- **历史对话**：
  - 支持将历史对话保存为json、与md
  - 可在历史对话界面，预览、加载、删除json保存的历史对话
- **用户界面**：
  - 使用 Tkinter 构建，界面简洁易用。
  - 支持缩放字体大小
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

## 项目结构

```
AI_Chat_Gui/
├── deepseek.py               # 主程序文件
├── ai_answer/                # AI回答相关文档
├── build/                    # 构建输出目录
├── history/                  # 历史对话记录
├── prompts/                  # Prompts 存储目录
├── prompts_manager/          # Prompt管理模块
├── README.md                 # 项目说明文件
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
