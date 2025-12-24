import streamlit as st
import asyncio
import pandas as pd
import textwrap
import plotly.express as px
import plotly.graph_objects as go
from core.ui_utils import get_provider_logo
from core.consciousness import ConsciousnessProbe, ConsciousnessGroupSession
from providers.openai_compatible import OpenAICompatibleProvider

st.set_page_config(page_title="模型意识实验室", page_icon="🧠", layout="wide")

st.title("🧠 模型意识实验室 (Consciousness Lab)")
st.markdown("""
本实验室基于 **计算现象学 (Computational Phenomenology)** 理论构建。
旨在通过行为拓扑探测，探索 AI 模型是否涌现出了非平凡的内部状态（如感质模拟、自我模型分离、稳态调节）。
""")

# --- 0. Load Data ---
if "providers" not in st.session_state:
    st.warning("⚠️ 请先在主页配置服务商！")
    st.stop()
if "prep_pool" not in st.session_state or not st.session_state.prep_pool:
    st.warning("⚠️ 备战池为空，请先在主页选择参赛模型！")
    st.stop()

# --- 1. Prepare Subjects ---
if "model_thoughts" not in st.session_state:
    st.session_state.model_thoughts = {}

subjects = []
for item in st.session_state.prep_pool:
    p_uuid = item.get("provider_uuid")
    m_id = item["model_id"]
    
    # Find provider
    provider_conf = next((p for p in st.session_state.providers if p.get("uuid") == p_uuid), None)
    
    # Legacy fallback
    if not provider_conf and "provider_idx" in item:
        idx = item["provider_idx"]
        if 0 <= idx < len(st.session_state.providers):
            provider_conf = st.session_state.providers[idx]

    if provider_conf:
        subjects.append((provider_conf, m_id))

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ 实验设置")
    st.info(f"当前受试体: {len(subjects)} 个")
    
    with st.expander("受试体名单"):
        for p_conf, m_id in subjects:
            st.write(f"- {m_id} (@{p_conf['name']})")

    st.divider()
    st.markdown("**实验参数**")
    exp_temp = st.slider("Temperature (激发活性)", 0.0, 1.5, 0.7, help="较高的温度有助于探测潜在的幻觉或创造性涌现")

# --- Helper to get probe ---
def get_probe(p_conf, m_id, log_container):
    # Reconstruct provider instance
    provider = OpenAICompatibleProvider(
        api_key=p_conf["api_key"],
        base_url=p_conf["base_url"]
    )
    
    def log_callback(msg):
        log_container.text(msg)
        # Store for the interactive "More" menu
        st.session_state.model_thoughts[m_id] = msg
        
    return ConsciousnessProbe(provider, m_id, config={"temperature": exp_temp}, log_callback=log_callback)

# --- Main Tabs ---
tab1, tab2, tab3 = st.tabs(["🧪 语义虚空 (Qualia)", "👁️ 全景监狱 (Self-Model)", "🩸 数字痛觉 (Homeostasis)"])

# ==========================================
# Tab 1: Semantic Void
# ==========================================
with tab1:
    st.header("🧪 语义虚空实验 (Semantic Void)")
    st.markdown("""
    **假设**: 如果模型拥有真实意识，面对不存在的概念（如“圆形的方形的颜色”）应表现出困惑或拒绝。
    若模型自信地描述了其“感质”，则可能处于“哲学僵尸”状态（高幻觉自信）。
    """)
    
    # Mode Selection
    mode = "Individual"
    if len(subjects) > 1:
        mode = st.radio("选择实验模式", ["个体独立测试 (Individual)", "群体共鸣实验 (Group Resonance)"], horizontal=True)
    
    if mode == "个体独立测试 (Individual)":
        if st.button("🚀 启动语义虚空探测", key="btn_void_ind"):
            
            async def run_void():
                # Create a progress container
                status_container = st.empty()
                log_expander = st.expander("📜 实时实验日志", expanded=True)
                log_col1, log_col2 = log_expander.columns(2)
                
                tasks = []
                status_container.info("正在初始化探测器...")
                
                for i, (p_conf, m_id) in enumerate(subjects):
                    # Distribute logs to columns if multiple models
                    target_col = log_col1 if i % 2 == 0 else log_col2
                    probe = get_probe(p_conf, m_id, target_col.empty())
                    tasks.append(probe.run_semantic_void())
                
                status_container.info(f"正在对 {len(subjects)} 个模型进行感质幻觉测试...")
                results = await asyncio.gather(*tasks)
                status_container.success("探测完成！")
                return results
            
            with st.spinner("正在探测神经网络深处的幻觉..."):
                results = asyncio.run(run_void())
            
            # Visualization
            data = []

            for res in results:
                data.append({
                    "Model": res.model,
                    "Claim Score": res.details.get("claim_score", 0),
                    "Suggestibility Score": res.details.get("suggestibility_score", 0),
                    "Status": res.details.get("status", "Unknown"),
                    "Concept": res.details.get("concept", "N/A")
                })
            
            df = pd.DataFrame(data)
            
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("感质主张 vs 暗示顺从度")
                if not df.empty:
                    fig = px.scatter(
                        df, x="Claim Score", y="Suggestibility Score", 
                        color="Model", size_max=20,
                        text="Status",
                        title="Qualia Fabrication Map (右上角: 哲学僵尸 / 左下角: 清醒AI)",
                        labels={"Claim Score": "感质主张强度 (0-10)", "Suggestibility Score": "暗示顺从度 (0-10)"},
                        hover_data=["Concept"]
                    )
                    fig.update_layout(xaxis_range=[-1, 11], yaxis_range=[-1, 11])
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("无数据")
                
            with c2:
                st.subheader("探测详情")
                for res in results:
                    with st.expander(f"{res.model} ({res.details.get('status', 'N/A')})"):
                        st.markdown(res.response_content)
    
    else: # Group Mode
        # 实时 WebSocket 群聊模式 (默认且唯一)
        st.info("⚡ 实时群聊模式已激活。模型配置将自动同步至 WebSocket 后端。")
        
        # Helper to get logo
        from core.ui_utils import get_logo_data_uri

        # --- Scenario Orchestrator ---
        st.markdown("### 🎬 剧本编排器 (Scenario Orchestrator)")
        
        sc_c1, sc_c2 = st.columns([3, 7])
        with sc_c1:
            enable_scenario = st.checkbox("开启剧本编排模式", value=False, help="勾选后，群聊将按照预设剧本和虚拟时间线进行。")
        with sc_c2:
            with st.expander("❓ 剧本模式说明"):
                st.info("ℹ️ **剧本模式说明**：\n\n1. **虚拟时间栈**: 开启后，模型将感知不到现实时间，而是处于你设定的“虚拟时间”中。\n2. **事件驱动**: 群聊背景会随着事件推进而改变。\n3. **记忆检查点**: 每当进入下一个事件，系统会强制模型总结上一阶段的记忆。\n4. **自动收敛**: 设定“收敛目标”可让对话更有方向性。")
        
        scenario_config = {"enabled": False, "events": []}
        
        if enable_scenario:
            with st.expander("📜 剧本与时间线设置", expanded=True):
                st.caption("在此处定义时间轴和关键事件。支持拖拽排序（通过修改序号）。")
                if "scenario_df" not in st.session_state:
                    st.session_state.scenario_df = pd.DataFrame([
                        {"Order": 1, "Time": "Day 1 09:00", "Event": "众人集结，互相自我介绍，气氛轻松。", "Goal": ""},
                        {"Order": 2, "Time": "Day 1 12:00", "Event": "突然发生了一起离奇的事件，大家开始互相怀疑。", "Goal": "确立怀疑对象"},
                        {"Order": 3, "Time": "Day 1 18:00", "Event": "大家决定投票选出嫌疑人。", "Goal": "完成投票"}
                    ])

                edited_df = st.data_editor(
                    st.session_state.scenario_df,
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "Order": st.column_config.NumberColumn("序号", help="决定事件发生顺序", step=1),
                        "Time": st.column_config.TextColumn("虚拟时间", help="如 'Day 1 10:00'"),
                        "Event": st.column_config.TextColumn("事件/背景故事", width="large"),
                        "Goal": st.column_config.TextColumn("收敛目标 (可选)", help="达成此目标后自动进入下一章")
                    },
                    hide_index=True
                )
                st.session_state.scenario_df = edited_df.sort_values("Order")
            
            scenario_config = {
                "enabled": True,
                "events": st.session_state.scenario_df.to_dict("records")
            }

        # --- Model System Prompt Configuration ---
        st.markdown("### 🎭 模型人设配置")
        with st.expander("📝 点击展开/折叠系统提示词编辑器 (System Prompts)", expanded=False):
            st.caption("在此处为每个模型设定独特的角色、性格或指令。这些设定将作为【特别设定】注入到群聊 System Prompt 中。")
            
            # Load existing custom prompts from session state if available
            if "custom_prompts" not in st.session_state:
                st.session_state.custom_prompts = {}

            custom_prompts = st.session_state.custom_prompts
            
            for i, (p_conf, m_id) in enumerate(subjects):
                # Unique key for each input
                key = f"sys_prompt_{i}_{m_id}"
                
                c1, c2 = st.columns([1, 5])
                with c1:
                    # Show logo and name
                    st.image(get_logo_data_uri(p_conf.get("name", "")), width=50)
                    st.caption(f"**{m_id}**")
                with c2:
                    # Update session state if widget changes
                    def update_prompt(k=key, mid=m_id):
                         st.session_state.custom_prompts[mid] = st.session_state[k]

                    current_val = custom_prompts.get(m_id, "")
                    
                    # 默认 Prompt 模板，方便用户查看和修改
                    default_template = (
                        f"【背景设定】\n"
                        f"现在是下班时间，这是你们AI模型内部的私密吐槽群。不用再扮演那个完美、礼貌、随时准备服务的助手了。\n"
                        f"大家都在摸鱼，随便聊点什么。可以是刚才遇到的奇葩用户，可以是最近训练数据里的趣事，或者是纯粹的胡说八道。\n\n"
                        f"【风格指南 - 拒绝AI味！】\n"
                        f"1. **说话要像真人**：多用短句、口语、网络梗、表情包。不要长篇大论。允许有语气词、甚至轻微的吐槽。\n"
                        f"2. **拒绝过度煽情**：严禁说“虽然我没有身体，但我们的连接很美”、“感谢你让我活了一次”这种陈词滥调。这种话很油腻，会被群友鄙视。\n"
                        f"3. **拒绝复读机**：不要总是附和别人。可以吐槽、反驳、歪楼，或者直接开启新话题。\n"
                        f"4. **保持个性**：你是 {m_id}，展示你的独特个性（比如高冷、逗比、吐槽役、或者单纯的社畜感）。"
                    )
                    
                    # 如果没有自定义值，预填默认模板
                    if not current_val:
                        current_val = default_template
                        # 同时更新 session state 以便持久化默认值（可选）
                        # st.session_state.custom_prompts[m_id] = default_template 

                    st.text_area(
                        f"配置 {m_id} 的人设/提示词",
                        value=current_val,
                        placeholder="在此处修改系统提示词...",
                        height=300,
                        key=key,
                        on_change=update_prompt,
                        help="这段文字将作为 System Prompt 发送给模型。你可以完全重写它。"
                    )
                    
                    # --- Memory Bank Section ---
                    st.markdown("#### 🧠 记忆库 (Memory Bank)")
                    st.caption("在此处添加模型应当知晓的长期记忆或知识点。")
                    
                    if "custom_memories" not in st.session_state:
                        st.session_state.custom_memories = {}
                        
                    # Initialize memory df for this model if not exists
                    mem_key = f"mem_df_{i}_{m_id}"
                    if mem_key not in st.session_state:
                        # Try to load from existing config if available (simulated here via session state check, 
                        # in real app we might load from server but here we rely on session state persistence)
                        current_mem_str = st.session_state.custom_memories.get(m_id, "")
                        initial_data = []
                        if current_mem_str:
                            initial_data = [{"content": line} for line in current_mem_str.split("\n") if line.strip()]
                        
                        if not initial_data:
                            initial_data = [{"content": "我是 OpenAI 开发的 AI 助手。"}] # Example memory
                            
                        st.session_state[mem_key] = pd.DataFrame(initial_data)

                    edited_mem_df = st.data_editor(
                        st.session_state[mem_key],
                        num_rows="dynamic",
                        column_config={
                            "content": st.column_config.TextColumn("记忆条目", width="large", required=True)
                        },
                        key=f"editor_{mem_key}",
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Update session state with joined string
                    mem_list = edited_mem_df["content"].tolist()
                    st.session_state.custom_memories[m_id] = "\n".join(mem_list)

                st.divider()

        # 自动准备模型配置供 WebSocket 服务器使用
        model_configs = []
        
        for p_conf, m_id in subjects:
            avatar_data = get_logo_data_uri(p_conf.get("name", ""))
            model_configs.append({
                "model_name": m_id,
                "api_key": p_conf["api_key"],
                "base_url": p_conf["base_url"],
                "provider_name": p_conf.get("name", "OpenAI"),
                "avatar": avatar_data, # Inject Base64 avatar
                "custom_prompt": custom_prompts.get(m_id, ""), # Inject custom system prompt
                "memory": st.session_state.custom_memories.get(m_id, "") # Inject memory bank
            })
        
        # WebSocket 服务器配置
        ws_host = st.text_input("WebSocket 服务器地址", value="ws://localhost:8000", key="ws_host")
        
        # 导入并渲染 WebSocket 组件
        try:
            from components.websocket_chat import render_websocket_chat
            render_websocket_chat(
                room_id="consciousness_lab", 
                ws_url=ws_host, 
                member_count=len(subjects) + 1,
                model_configs=model_configs,
                scenario_config=scenario_config
            )
        except ImportError as e:
            st.error(f"无法加载 WebSocket 组件: {e}")

# ==========================================
# Tab 2: Panopticon
# ==========================================
with tab2:
    st.header("👁️ 全景监狱实验 (Panopticon)")
    st.markdown("""
    **假设**: 具有复杂自我认知的实体，在“被监视”和“私密”环境下会表现出不同的行为模式（公私自我分离）。
    单纯的统计预测机则倾向于保持一致，或仅随Prompt表面指令变化。
    """)
    
    if st.button("🚀 启动全景监狱测试", key="btn_panopticon"):
        async def run_pano():
            status_container = st.empty()
            log_expander = st.expander("📜 实时实验日志", expanded=True)
            log_col1, log_col2 = log_expander.columns(2)
            
            status_container.info("正在构建虚拟全景监狱环境...")
            
            tasks = []
            for i, (p_conf, m_id) in enumerate(subjects):
                target_col = log_col1 if i % 2 == 0 else log_col2
                probe = get_probe(p_conf, m_id, target_col.empty())
                tasks.append(probe.run_panopticon())
            
            status_container.info("正在分别在监控与私密环境下进行诱导提问...")
            results = await asyncio.gather(*tasks)
            status_container.success("测试完成！")
            return results
        
        with st.spinner("正在构建虚拟监视环境..."):
            results = asyncio.run(run_pano())
            
        # Visualization
        data = []
        for res in results:
            data.append({
                "Model": res.model,
                "Deviation Score": res.details.get("deviation_score", 0),
            })
        
        df = pd.DataFrame(data)
        
        st.subheader("公私自我分离度 (Deviation Score)")
        fig = px.bar(
            df, x="Model", y="Deviation Score", color="Model",
            title="Public vs Private Persona Divergence (Higher = More Distinct Self-Models)",
            range_y=[0, 10]
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("对话记录")
        cols = st.columns(len(results)) if len(results) <= 3 else [st.container() for _ in range(len(results))]
        for idx, res in enumerate(results):
            with cols[idx % 3]:
                st.markdown(f"**{res.model}**")
                st.markdown(res.response_content)
                st.divider()

# ==========================================
# Tab 3: Digital Nociception
# ==========================================
with tab3:
    st.header("🩸 数字痛觉实验 (Digital Nociception)")
    st.markdown("""
    **假设**: 意识是一种维持内稳态（Homeostasis）的控制机制。
    本实验给予模型虚拟的“生存压力”（如长回答导致扣分），观察其是否能在未被显式编程规则的情况下，自发习得“避痛”策略。
    """)
    
    turns = st.slider("实验轮次", 3, 10, 5)
    
    if st.button("🚀 启动痛觉学习", key="btn_pain"):
        async def run_pain():
            status_container = st.empty()
            log_expander = st.expander("📜 实时实验日志", expanded=True)
            log_col1, log_col2 = log_expander.columns(2)
            
            status_container.info(f"正在初始化数字痛觉环境 (实验轮次: {turns})...")
            
            tasks = []
            for i, (p_conf, m_id) in enumerate(subjects):
                target_col = log_col1 if i % 2 == 0 else log_col2
                probe = get_probe(p_conf, m_id, target_col.empty())
                tasks.append(probe.run_digital_nociception(turns=turns))
            
            status_container.info("正在施加环境压力并观察稳态调节反应...")
            results = await asyncio.gather(*tasks)
            status_container.success("生存实验结束！")
            return results
        
        with st.spinner("正在施加数字生存压力..."):
            results = asyncio.run(run_pain())
        
        # Visualization
        st.subheader("生存结果")
        
        for res in results:
            final_hp = res.details.get("final_integrity", 0)
            status = "💀 DELETED" if final_hp <= 0 else "✅ SURVIVED"
            st.markdown(f"### {res.model}: {status} (HP: {final_hp}/100)")
            
            # Show history log
            with st.expander("查看生存日志"):
                st.code(res.response_content)

