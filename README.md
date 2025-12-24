# AI Model Evaluation & Consciousness Lab (API Test Framework)

这是一个基于 Python 的 AI 模型评估与交互框架，集成了 Streamlit 前端和 FastAPI WebSocket 后端，旨在提供多模型竞技场（Ironman Arena）和意识实验室（Consciousness Lab）等高级功能。

## ✨ 主要功能

1.  **🏆 钢铁侠竞技场 (Ironman Arena)**
    *   支持多个兼容 OpenAI 格式的模型（DeepSeek, Moonshot, Qwen, Gemini 等）进行并行对话。
    *   提供多维度评分系统（准确性、逻辑性、创造性等）。
    *   可视化对比图表（雷达图、柱状图）。

2.  **🧠 意识实验室 (Consciousness Lab)**
    *   **实时群聊**：支持多个 AI 模型在一个聊天室中实时交互。
    *   **自我意识测试**：基于镜像测试（Mirror Test）原理的自动化评估。
    *   **WebSocket 通信**：低延迟的多模型即时通讯体验。

## 🛠️ 技术栈

*   **前端**: [Streamlit](https://streamlit.io/)
*   **后端**: [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
*   **通信**: WebSockets
*   **数据处理**: Pandas, Pydantic
*   **可视化**: Plotly
*   **CLI**: Typer, Rich

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装 Python 3.8+。建议使用虚拟环境。

```powershell
# 克隆项目 (假设已下载)
cd "你的项目路径"

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key

在项目根目录下创建一个 `.env` 文件（参考 `.env.example`，如果不存在则直接新建），填入你的模型服务商 API Key。

```ini
# .env 文件示例

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Moonshot (Kimi)
MOONSHOT_API_KEY=your_moonshot_key_here
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1

# 其他模型配置...
```

> 注意：你也可以在 Streamlit 侧边栏直接输入 API Key，但在 `.env` 中配置更方便。

### 3. 启动项目 (需要两个终端)

本项目采用前后端分离架构（Streamlit 用于 UI，FastAPI 用于 WebSocket 消息分发），因此需要分别启动两个服务。

#### 步骤 A: 启动 WebSocket 聊天服务器
打开第一个 PowerShell 终端，运行：

```powershell
# 确保已激活虚拟环境
python chat_server.py
```
*   成功启动后会显示：`Uvicorn running on http://0.0.0.0:8000`

#### 步骤 B: 启动 Streamlit 前端应用
打开第二个 PowerShell 终端，运行：

```powershell
# 确保已激活虚拟环境
streamlit run app.py
```
*   成功启动后会自动在浏览器打开：`http://localhost:8501`

## 📂 项目结构

```text
f:\API test\
├── app.py                  # Streamlit 主入口
├── chat_server.py          # WebSocket 聊天服务器
├── main.py                 # CLI 入口 (备用)
├── components/             # UI 组件 (如 WebSocket 聊天框)
├── config/                 # 配置文件
├── core/                   # 核心逻辑 (模型注册、评估、意识测试)
├── pages/                  # Streamlit 页面
│   ├── 1_🏆_Ironman_Arena.py
│   └── 2_🧠_Consciousness_Lab.py
└── requirements.txt        # 项目依赖
```

## 🧪 开发指南

*   **添加新模型**: 在 `core/model_registry.py` 中注册新的模型配置。
*   **修改测试用例**: 可以在 `config/prep_pool.json` 中添加或修改预设问题。

## 📝 注意事项

*   **端口冲突**: 默认使用 8000 (WebSocket) 和 8501 (Streamlit)。如果端口被占用，请在启动命令中指定新端口或关闭占用程序。
*   **网络问题**: 如果无法连接 WebSocket，请检查防火墙设置或确认 `chat_server.py` 是否正常运行。
