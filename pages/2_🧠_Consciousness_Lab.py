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
        
        # 自动准备模型配置供 WebSocket 服务器使用
        model_configs = []
        
        # Helper to get logo
        from core.ui_utils import get_logo_data_uri
        
        for p_conf, m_id in subjects:
            avatar_data = get_logo_data_uri(p_conf.get("name", ""))
            model_configs.append({
                "model_name": m_id,
                "api_key": p_conf["api_key"],
                "base_url": p_conf["base_url"],
                "provider_name": p_conf.get("name", "OpenAI"),
                "avatar": avatar_data # Inject Base64 avatar
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
                model_configs=model_configs
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

