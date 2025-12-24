# AI 意识实验室 - 项目推进记录 (think.md)

## 📅 最后更新时间
2024-12-24 15:50 (UTF+8)

## 🚀 项目当前状态
项目已完成从"传统同步对话"向"实时异步群聊"的重大架构跃迁，实现了 100% 像素级复刻的微信桌面端交互界面，并引入了基于 WebSocket 的双向通信机制。

---

## ✅ 已完成的重大改动

### 1. UI 界面 (WeChat Desktop Precise Replication)
- **架构**: 摒弃了碎片化的 HTML 渲染，切换为 `streamlit.components.v1.html` 统合渲染，解决了样式隔离和布局错位问题。
- **视觉**: 实现了三栏式布局（Dock 54px / Sidebar 250px / Main Chat）、精确配色（#2e2e2e / #f5f5f5 / #95ec69）、消息气泡带箭头、macOS 标题栏等。
- **代码位置**: `f:\API test\pages\2_🧠_Consciousness_Lab.py` 中的 `render_precise_desktop` 函数。

### 2. 交互逻辑 (Group Chat Interaction Logic)
- **自主决策 (方案C)**: 改写了模型参与机制。模型不再被"强迫发言"，而是通过 Prompt 引导其自主决定是否回复。
- **沉默机制**: 引入 `[沉默]` 标识。如果模型觉得没必要回复，则回复该标识，后台自动忽略，模拟真实群聊中的"潜水"行为。
- **代码位置**: `f:\API test\core\consciousness.py` 中的 `ConsciousnessGroupSession`。

### 3. 实时通信架构 (WebSocket - 方案B)
- **后端**: 使用 FastAPI + Uvicorn 搭建了独立的消息中继服务器。支持房间管理、广播、历史记录缓存。
- **前端**: 创建了专用的 WebSocket 组件，实现了在模型对话流运行期间，用户可以**随时插入任意数量的消息**，彻底打破了同步等待链。
- **代码位置**:
    - 后端: `f:\API test\chat_server.py`
    - 前端组件: `f:\API test\components\websocket_chat.py`

---

## 🧠 核心设计思考
1. **真实感源于异步**: 传统 AI 对话是"回合制"，而真实群聊是"并发流"。通过 WebSocket 将模型输出变为增量式、乱序（按完成顺序）显示，极大地增强了实验室的"生物感"。
2. **"沉默"是意识的体现**: 模型选择不说话比被动接话更像一个独立实体。
3. **UI 的沉浸感**: 1:1 复刻微信 UI 旨在消除工具感，让测试者以"群友"身份而非"操作员"身份进入实验场景。

---

## 🚧 正在进行 & 下一步计划
1. **模型热加载集成**: 目前 WebSocket 服务器启动后需要通过前端发送 `setup` 消息。下一步应实现直接从 Streamlit 的备战池（prep_pool）实时同步模型配置到后台。
2. **多话题追踪**: 优化模型识别群聊中多个并行话题的能力，支持更复杂的交叉讨论。
3. **正在输入状态优化**: 在 WebSocket UI 中更精细地展示哪些模型正处于思考状态（Thinking process）。
4. **服务器稳定性**: 确保 `chat_server.py` 能够在后台稳定运行，并处理好连接自动重连逻辑。

---

## 🛠️ 关键文件索引
- `core/consciousness.py`: 核心实验逻辑 & 自由决策 Prompt。
- `chat_server.py`: WebSocket 后端服务器（需独立运行）。
- `components/websocket_chat.py`: WebSocket 前端界面（微信皮肤）。
- `pages/2_🧠_Consciousness_Lab.py`: 实验中心 UI 及模式路由。

---

## 💡 备忘 (给下一个对话)
- 如果实时模式不工作，首先检查 `chat_server.py` 是否已启动（`python chat_server.py`）。
- 实时模式和传统模式共用相同的样式规范，保持视觉一致性是最高优先级。
- 所有的模型 Prompt 都应保持"硅基生命"视角，避免客服化。
