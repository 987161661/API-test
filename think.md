# 项目开发备忘录 (Project Development Memo)

## 📅 更新时间: 2025-12-25
**当前阶段**: 上帝模式与舞台视图实现 (God Mode & Stage View Implementation)

---

## 🚀 最近更新 (Recent Updates)

### 1. 新增：独立舞台视图 (Stage View)
- **文件**: `pages/3_🎭_Stage_Only.py`
- **功能**: 创建了一个极简的、只有聊天界面的页面。
- **目的**: 方便多屏展示或录屏，支持通过 "在新标签页打开" 按钮从主控制台启动。
- **技术**: 复用了 `components/websocket_chat.py`，与主控制台通过 WebSocket 共享同一个房间 (`consciousness_lab`)，实现实时同步。

### 2. 新增：上帝控制器 (God Controller)
- **位置**: `pages/2_🧠_Consciousness_Lab.py` (位于聊天界面下方)
- **功能**:
    - **时间轴控制 (Timeline)**: 滑块显示当前剧本进度，支持 "Jump" 跳转到任意事件点。
    - **节奏控制 (Pacing)**: 暂停/继续按钮，可随时冻结模型对话（冷场）。
    - **突发事件注入 (Event Injection)**: 允许用户实时插入系统级旁白/事件，干预对话走向。
    - **AI 导演对话 (AI Director)**: 
        - 这是一个与后台 AI (GPT-4等) 对话的接口。
        - 导演可以读取当前对话历史和剧本状态。
        - 导演有权限通过 JSON 指令直接修改后续剧本 (`update_scenario`)。

### 3. 后端架构升级 (Backend Upgrades)
- **文件**: `chat_server.py`, `core/consciousness.py`
- **变更**:
    - **状态管理**: 在 `ConsciousnessGroupSession` 中增加了 `is_paused` 状态。
    - **控制接口**: 新增 FastAPI 路由 `/control/{room_id}/*` (pause, resume, jump, event, update_scenario)。
    - **循环优化**: 模型自主循环 (`run_autonomous_loop`) 中加入了暂停检查点 (`while self.is_paused: await asyncio.sleep(0.5)`)。
    - **Bug修复**: 修复了 Streamlit Slider 在事件数量不足时报错的问题。

---

## 💡 当前开发思路 (Current Thoughts)

项目的核心已从“被动观察 AI 群聊”转变为“主动导演 AI 剧场”。目前的架构非常灵活：
1.  **前后端分离**: Streamlit 仅作为 UI，核心逻辑运行在 FastAPI WebSocket 服务中。这意味着 UI 的刷新或关闭不会中断 AI 的思考。
2.  **动态剧本**: 剧本不再是静态的 JSON，而是可以被 AI 导演或用户实时修改的动态对象。这为“涌现式叙事”提供了基础。
3.  **双层控制**: 用户既可以直接操作时间轴（粗粒度），也可以通过 AI 导演进行剧情微调（细粒度）。

---

## 🗓️ 下一步计划 (Next Steps)

1.  **精细化控制**:
    - 目前突发事件是全局的 (`scope="global"`)。计划支持针对**特定模型**发送私密指令（如：“系统提示 A 模型：你现在感到非常愤怒”）。
    - 实现拖拽式时间轴 UI (目前是 Slider，不够直观)。

2.  **AI 导演能力增强**:
    - 目前导演只能更新 `events` 列表。
    - 未来可以让导演修改模型的 `memory` (记忆库) 或 `personality` (人设)，实现更深层的剧情扭转。

3.  **舞台效果增强**:
    - `Stage View` 目前比较朴素。可以增加不同的 CSS 主题（如：赛博朋克风格、羊皮纸风格）以适配不同的剧本。
    - 增加视觉特效（如：有人被“杀”死时的红屏特效）。

4.  **测试与稳定性**:
    - 在高并发或长剧本下测试 WebSocket 的稳定性。
    - 验证 AI 导演生成的 JSON 格式的鲁棒性。

---

## ⚠️ 注意事项 (Notes for Next Session)
- 启动项目时需要同时运行 Streamlit 前端和 FastAPI 后端。
- `chat_server.py` 是核心状态持有者，修改逻辑时需优先考虑后端。
- 如果遇到 Slider 报错，检查 `total_events` 是否正确获取。
