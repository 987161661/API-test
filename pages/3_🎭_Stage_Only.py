import streamlit as st
import json
import os
import sys

# 设置页面布局为宽屏，并尽量隐藏无关元素
st.set_page_config(page_title="Stage View", layout="wide", initial_sidebar_state="collapsed")

# 尝试导入组件
try:
    # 添加项目根目录到 sys.path，以便能找到 components
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
        
    from components.websocket_chat import render_websocket_chat
except ImportError as e:
    st.error(f"组件加载失败: {e}")
    st.stop()

# 尝试读取后端保存的配置
config_path = os.path.join(root_dir, "chat_config_consciousness_lab.json")
model_configs = []
scenario_config = {}

if os.path.exists(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 恢复 model_configs 列表
            raw_members = data.get("member_configs", {})
            for m_name, m_conf in raw_members.items():
                model_configs.append({
                    "model_name": m_name,
                    "avatar": m_conf.get("avatar", ""),
                    "is_manager": m_conf.get("is_manager", False),
                    "custom_prompt": m_conf.get("custom_prompt", ""),
                    "memory": m_conf.get("memory", "")
                })
            
            # 尝试恢复 scenario_config (如果有保存的话，目前 chat_server 好像没有把 scenario 保存到 json 根节点，或者是分开处理的)
            # chat_server load_config 并没有读取 scenario，save_config 也没保存 scenario。
            # scenario 是在内存中维护的。
            # 但 websocket 连接后会通过 status 消息同步 scenario 状态。
            # 所以这里不需要太担心 scenario_config 的初始值，只要连接上，状态就会同步。
                
    except Exception as e:
        st.warning(f"无法加载同步配置: {e}")

# 隐藏 Streamlit 默认的汉堡菜单和页脚，让界面更干净
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 渲染组件
render_websocket_chat(
    room_id="consciousness_lab", 
    ws_url="ws://localhost:8000", 
    member_count=len(model_configs) + 1,
    model_configs=model_configs,
    scenario_config={},
    is_stage_view=True
)
