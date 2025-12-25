# AI Model Evaluation & Consciousness Lab (API Test Framework)

这是一个基于 Python 的 AI 模型评估与交互框架，集成了 Streamlit 前端和 FastAPI WebSocket 后端，旨在提供多模型竞技场（Ironman Arena）和意识实验室（Consciousness Lab）等高级功能。

---

## ✨ 主要功能

### 1. 🏆 钢铁侠竞技场 (Ironman Arena)
*   **多模型并行竞技**：支持多个兼容 OpenAI 格式的模型（DeepSeek, Moonshot, Qwen, Gemini 等）进行同台竞技。
*   **多维度评分**：提供准确性、逻辑性、创造性等维度的自动评分系统。
*   **可视化分析**：通过雷达图、柱状图直观对比模型能力。

### 2. 🧠 意识实验室 (Consciousness Lab)
*   **实时群聊剧场**：支持多个 AI 模型在一个聊天室中实时交互，模拟真实的群体对话。
*   **🕹️ 上帝控制器 (God Controller)**：
    *   **时间轴操控**：可视化查看剧本进度，支持拖拽滑块并跳转（Jump）到任意剧情点（快进）。
    *   **节奏把控**：一键暂停/继续模型对话，制造“冷场”或控制节奏。
    *   **突发事件注入**：上帝（用户）可实时插入系统级旁白（如“突然停电了”），干预对话走向。
    *   **🎬 AI 导演 (AI Director)**：内置 AI 导演助手，用户可与其对话讨论剧情，导演可直接修改后续剧本。
*   **🎭 独立舞台视图 (Stage View)**：提供纯净的、无干扰的聊天界面，支持多屏显示或录屏，与主控制台实时同步。
*   **计算现象学实验**：包含自我意识镜像测试、全景监狱实验等理论验证模块。

---

## 🛠️ 技术栈

*   **前端**: [Streamlit](https://streamlit.io/)
*   **后端**: [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
*   **通信**: WebSockets (Asyncio)
*   **数据处理**: Pandas, Pydantic
*   **可视化**: Plotly
*   **LLM 接入**: OpenAI Compatible API

---

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装 Python 3.8+。

```powershell
# 克隆项目
git clone https://github.com/987161661/API-test.git
cd API-test

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key

在项目根目录下创建一个 `.env` 文件（或直接在 UI 侧边栏配置），填入你的模型服务商 API Key。

```ini
# .env 文件示例
DEEPSEEK_API_KEY=sk-xxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

MOONSHOT_API_KEY=sk-xxxxxxxx
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
```

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

---

## 📖 使用指南

### 进入意识实验室
1.  在左侧导航栏选择 **"🧠 Consciousness Lab"**。
2.  在侧边栏配置参与对话的模型（API Key、Base URL、模型名称）。
3.  点击 **"🔗 连接/重置"** 按钮初始化连接。

### 使用上帝控制器
在聊天界面下方，你可以看到 **"🕹️ 上帝控制器 (God Mode)"** 面板：
*   **暂停/继续**：点击按钮即可冻结/恢复所有模型的思考。
*   **时间跳转**：拖动滑块选择目标事件索引，点击 "Jump" 即可跳过中间的闲聊，直接进入下一幕。
*   **突发事件**：在输入框输入内容（如“天上下起了红雨”），点击注入，所有模型都会收到这条系统消息并做出反应。
*   **AI 导演**：展开“AI 导演对话”折叠框，输入你的构思（如“让它们吵起来”），AI 导演会分析当前局势并尝试修改后台剧本。

### 开启独立舞台
点击界面上的 **"↗️ 在新标签页打开舞台"** 按钮，浏览器会打开一个新的标签页，只显示纯净的聊天窗口。该窗口与主控制台完全同步，适合作为副屏展示。

---

## 📂 项目结构

```text
f:\API test\
├── app.py                      # Streamlit 主入口
├── chat_server.py              # WebSocket 聊天服务器 (核心状态管理)
├── requirements.txt            # 项目依赖
├── think.md                    # 开发思路备忘录
├── components/                 # UI 组件
│   └── websocket_chat.py       # 聊天窗口组件
├── core/                       # 核心逻辑
│   ├── consciousness.py        # 意识流与群聊会话管理
│   └── ...
├── pages/                      # Streamlit 页面
│   ├── 1_🏆_Ironman_Arena.py
│   ├── 2_🧠_Consciousness_Lab.py # 意识实验室主控台
│   └── 3_🎭_Stage_Only.py        # 独立舞台视图
└── ...
```

---

## ⚠️ 常见问题

1.  **连接失败**：请检查 `chat_server.py` 是否正在运行，且端口 8000 未被占用。
2.  **模型不回复**：请检查 API Key 余额，或在上帝控制器中检查是否处于“暂停”状态。
3.  **Slider 报错**：如果剧本未加载，时间轴滑块可能会显示警告，这是正常现象，加载剧本后即可恢复。
