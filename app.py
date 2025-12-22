import streamlit as st
import asyncio
import httpx
from core.schema import ChatMessage, TestResult
from providers.openai_compatible import OpenAICompatibleProvider
from core.model_registry import get_model_info, MODEL_METADATA, PROVIDER_PRESETS
from core.ui_utils import get_provider_logo, get_logo_data_uri, create_badge_data_uri, TAG_STYLES
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import os
import uuid

CONFIG_FILE = "config/providers.json"
PREP_POOL_FILE = "config/prep_pool.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Migration: Ensure all have UUID
                for p in data:
                    if "uuid" not in p:
                        p["uuid"] = str(uuid.uuid4())
                return data
        except Exception as e:
            st.error(f"Failed to load config: {e}")
    return None

def save_config():
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.providers, f, indent=2, ensure_ascii=False)

def load_prep_pool():
    if os.path.exists(PREP_POOL_FILE):
        try:
            with open(PREP_POOL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_prep_pool():
    os.makedirs(os.path.dirname(PREP_POOL_FILE), exist_ok=True)
    with open(PREP_POOL_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.prep_pool, f, indent=2, ensure_ascii=False)

def update_provider_field(index, field, key):
    st.session_state.providers[index][field] = st.session_state[key]
    save_config()

st.set_page_config(
    page_title="LLM 模型竞技场",
    page_icon="⚔️",
    layout="wide"
)

# 自定义 CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    h1, h2, h3 {
        font-family: 'Microsoft YaHei', sans-serif;
    }
    .provider-box {
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .status-badge-success {
        background-color: #d4edda;
        color: #155724;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8em;
    }
    .status-badge-fail {
        background-color: #f8d7da;
        color: #721c24;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8em;
    }
    /* Pool Styles */
    .pool-container {
        border: 2px dashed #4CAF50;
        padding: 20px;
        border-radius: 10px;
        background-color: #f9fdf9;
        min-height: 100px;
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        align-items: center;
        justify-content: center;
    }
    .pool-item {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 20px;
        padding: 8px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9em;
    }
    .pool-item-remove {
        color: #ff4b4b;
        cursor: pointer;
        font-weight: bold;
    }
    .pool-placeholder {
        color: #888;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚔️ LLM 模型竞技场")
st.markdown("配置服务商，挑选同量级选手，一决高下！")

# --- Helper Functions ---
async def fetch_models(base_url, key):
    headers = {"Authorization": f"Bearer {key}"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{base_url.rstrip('/')}/models", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data:
                    return [m["id"] for m in data["data"]]
                else:
                    return []
            else:
                return None
    except Exception as e:
        return None

# --- Session State 初始化 ---
if "providers" not in st.session_state:
    saved = load_config()
    if saved:
        st.session_state.providers = saved
    else:
        st.session_state.providers = [
            {"id": 0, "uuid": str(uuid.uuid4()), "name": "服务商 #1", "base_url": "https://api.xiaomimimo.com/v1", "api_key": "sk-c6q1kvmdq5kg9mcglxk05dbddiqs8vv3pzf4gfvt9u3guun0", "models": [], "status": "unknown"}
        ]
if "prep_pool" not in st.session_state:
    st.session_state.prep_pool = load_prep_pool() # Load from file

# Global Inference Config
if "inference_config" not in st.session_state:
    st.session_state.inference_config = {
        "temperature": 0.7,
        "max_tokens": 6000,
        "top_p": 1.0
    }

def add_provider(preset=None):
    new_id = len(st.session_state.providers)
    
    name = f"服务商 #{new_id + 1}"
    base_url = ""
    
    if preset:
        name = f"{preset.name} #{new_id + 1}"
        base_url = preset.base_url

    st.session_state.providers.append({
        "id": new_id, 
        "uuid": str(uuid.uuid4()),
        "name": name,
        "base_url": base_url, 
        "api_key": "", 
        "models": [],
        "status": "unknown"
            })
    save_config()

def toggle_model_in_pool(provider_uuid, model_id):
    """Toggle model presence in the prep pool."""
    # Check if already exists
    existing = next((item for item in st.session_state.prep_pool if item["provider_uuid"] == provider_uuid and item["model_id"] == model_id), None)
    
    if existing:
        st.session_state.prep_pool.remove(existing)
    else:
        st.session_state.prep_pool.append({"provider_uuid": provider_uuid, "model_id": model_id})
    save_prep_pool()

# --- Sidebar: 多 Provider 配置 ---
with st.sidebar:
    st.header("⚙️ 接入服务商")
    
    for i, p in enumerate(st.session_state.providers):
        # Ensure UUID exists
        if "uuid" not in p:
            p["uuid"] = str(uuid.uuid4())
            
        with st.expander(f"{p['name']} ({len(p['models'])} 模型)", expanded=True):
            # Delete button
            c1, c2 = st.columns([6, 1])
            with c2:
                if st.button("🗑️", key=f"del_{p['uuid']}", help="删除此配置"):
                    st.session_state.providers.pop(i)
                    save_config()
                    st.rerun()

            # Inputs
            st.text_input(
                f"API 地址", 
                value=p["base_url"], 
                key=f"url_{p['uuid']}", 
                placeholder="https://...",
                on_change=update_provider_field,
                args=(i, "base_url", f"url_{p['uuid']}")
            )
            st.text_input(
                f"API Key", 
                value=p["api_key"], 
                type="password", 
                key=f"key_{p['uuid']}",
                on_change=update_provider_field,
                args=(i, "api_key", f"key_{p['uuid']}")
            )
            
            col_btn, col_status = st.columns([1, 2])
            with col_btn:
                if st.button(f"连接", key=f"btn_conn_{p['uuid']}"):
                    with st.spinner("..."):
                        models = asyncio.run(fetch_models(p["base_url"], p["api_key"]))
                        if models is not None:
                            p["models"] = models
                            p["status"] = "success"
                            save_config()
                            st.rerun()
                        else:
                            p["status"] = "fail"
                            p["models"] = []
                            save_config()
                            st.rerun()
            
            with col_status:
                if p["status"] == "success":
                    st.markdown(f'<span class="status-badge-success">已连接: {len(p["models"])}个模型</span>', unsafe_allow_html=True)
                elif p["status"] == "fail":
                    st.markdown('<span class="status-badge-fail">连接失败</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ➕ 添加服务商")
    
    preset_options = {p.name: p for p in PROVIDER_PRESETS}
    selected_preset_name = st.selectbox("选择配置模板", list(preset_options.keys()), key="preset_sel")
    
    if st.button("添加配置卡片"):
        selected_preset = preset_options[selected_preset_name]
        add_provider(selected_preset)
        st.rerun()

# --- Main Content: 竞技场 ---

# 1. 选手入场 (Model Selection with Dataframe)
st.subheader("1. 🏟️ 选手入场")

# Callback for handling selection changes
def on_model_selection_change():
    """
    Handle changes from the data_editor.
    This runs BEFORE the script body re-executes, using the state from the previous run.
    """
    state = st.session_state
    
    # Check if we have the necessary view state from the previous run
    if "model_view_index" not in state or "model_selector" not in state:
        return

    changes = state["model_selector"].get("edited_rows", {})
    view_index = state["model_view_index"]
    
    for idx_str, change in changes.items():
        # idx is the position in the dataframe from the previous run
        idx = int(idx_str)
        if idx >= len(view_index):
            continue
            
        row_id = view_index[idx]
        
        # We only care about the "Selected" column
        if "Selected" in change:
            is_selected = change["Selected"]
            
            # Parse row_id to get provider_uuid and model_id
            try:
                p_uuid, m_id = row_id.split(":", 1)
            except ValueError:
                continue
                
            # Find in prep_pool
            # Use a list comprehension to find index if exists
            pool_index = -1
            for i, item in enumerate(state.prep_pool):
                if item.get("provider_uuid") == p_uuid and item["model_id"] == m_id:
                    pool_index = i
                    break
                # Legacy fallback
                if pool_index == -1 and "provider_idx" in item:
                     # This is harder to match perfectly without provider list, 
                     # but we rely on UUID primarily now.
                     # We can try to match by model_id and assume it's the right one if only one provider has it?
                     # Or we can skip legacy logic here and assume migration happens on load.
                     pass

            if is_selected and pool_index == -1:
                state.prep_pool.append({"provider_uuid": p_uuid, "model_id": m_id})
            elif not is_selected and pool_index != -1:
                state.prep_pool.pop(pool_index)

# Aggregate all models
all_model_rows = []
for i, p in enumerate(st.session_state.providers):
    if p["status"] == "success" and p["models"]:
        for m in p["models"]:
            info = get_model_info(m)
            # Use UUID for robust selection tracking
            is_selected = any(item.get("provider_uuid") == p["uuid"] and item["model_id"] == m for item in st.session_state.prep_pool)
            # Fallback for old index-based pool items (migration on the fly)
            if not is_selected and any(item.get("provider_idx") == i and item["model_id"] == m for item in st.session_state.prep_pool):
                 is_selected = True

            all_model_rows.append({
                "row_id": f"{p['uuid']}:{m}", # Unique composite key
                "Selected": is_selected,
                "Logo": get_logo_data_uri(p["name"]),
                "Tag": create_badge_data_uri(info.tags), # New Tag Badge
                "RawTags": info.tags, # For filtering
                "Model ID": info.name,
                "Provider": p["name"],
                "Provider_UUID": p["uuid"], # Store UUID for reliable tracking
                "Provider_Idx": i, # Store index for legacy fallback
                "Type": info.type,
                "Context Window": f"{info.context_window/1000:.0f}k" if info.context_window else "N/A",
                "Input Price ($/1M)": f"${info.input_price:.2f}",
                "Output Price ($/1M)": f"${info.output_price:.2f}",
                "Release Date": info.release_date or "Unknown",
                "Description": info.description
            })

if not all_model_rows:
    st.warning("👈 请先在左侧配置并连接至少一个 API 服务商，以获取参赛模型。")
else:
    # Display as Dataframe with selection
    df_models = pd.DataFrame(all_model_rows)
    df_models.set_index("row_id", inplace=True)
    
    # --- Filter Section ---
    available_types = sorted(list(set(df_models["Type"].tolist())))
    
    # Extract unique tags
    all_tags = set()
    for tags in df_models["RawTags"]:
        if tags:
            all_tags.update(tags)
    available_tags = sorted(list(all_tags))
    
    TYPE_MAPPING = {
        "chat": "对话 (Chat)",
        "vision": "视觉 (Vision)",
        "reasoning": "推理 (Reasoning)",
        "code": "代码 (Code)",
        "embedding": "嵌入 (Embedding)",
        "audio": "音频 (Audio)",
        "video": "视频 (Video)",
        "image-generation": "绘图 (Image Gen)",
        "multimodal": "多模态 (Multimodal)"
    }

    with st.expander("🔍 筛选选项 (Filter Options)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            selected_types = st.multiselect(
                "按模型类型筛选",
                options=available_types,
                default=available_types,
                placeholder="选择模型类型...",
                format_func=lambda x: TYPE_MAPPING.get(x, x)
            )
        with c2:
            selected_tags = st.multiselect(
                "按标签筛选",
                options=available_tags,
                default=[],
                placeholder="选择标签 (留空显示所有)...",
                format_func=lambda x: TAG_STYLES.get(x, {}).get("text", x)
            )
    
    # Apply Filters
    df_filtered = df_models
    
    # Type Filter
    if selected_types:
        df_filtered = df_filtered[df_filtered["Type"].isin(selected_types)]
        
    # Tag Filter
    if selected_tags:
        # Filter rows where the model's tags intersect with selected_tags
        # (Show model if it has ANY of the selected tags)
        df_filtered = df_filtered[df_filtered["RawTags"].apply(lambda x: any(tag in selected_tags for tag in x))]


    # Save the current view index for the callback to use in the NEXT run
    st.session_state["model_view_index"] = df_filtered.index.tolist()

    # Configure columns
    column_config = {
        "Selected": st.column_config.CheckboxColumn(
            "选择",
            help="勾选以加入备战池",
            default=False,
            width="small", 
        ),
        "Logo": st.column_config.ImageColumn("图标", width="small"),
        "Model ID": st.column_config.TextColumn("模型名称 (ID)", width="large"), # Merged Concept
        "Tag": st.column_config.ImageColumn("标签", width="small"), # Badge Column
        "Provider": st.column_config.TextColumn("来源", width="small"),
        "Type": st.column_config.TextColumn("类型", width="small"),
        "Context Window": st.column_config.TextColumn("上下文", width="small"),
        "Input Price ($/1M)": st.column_config.TextColumn("输入价格", width="small"),
        "Output Price ($/1M)": st.column_config.TextColumn("输出价格", width="small"),
        "Release Date": st.column_config.TextColumn("发布日期", width="small"),
        "Description": st.column_config.TextColumn("说明", width="large"),
        "Provider_UUID": None, # Hide
        "Provider_Idx": None, # Hide
    }
    
    # Custom CSS to force row height smaller
    st.markdown("""
    <style>
        div[data-testid="stDataEditor"] table {
            font-size: 0.9em;
        }
        div[data-testid="stDataEditor"] td {
            vertical-align: middle !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Custom Row Rendering
    # Since st.data_editor cannot merge Image+Text+Image in one cell, 
    # we use a custom component-like structure using st.columns
    # This replaces st.data_editor for the Model List View
    
    st.markdown("### 选手列表")
    
    # Header
    h1, h2, h3, h4, h5, h6 = st.columns([0.5, 4, 1.5, 1.5, 1.5, 2])
    h1.markdown("**选择**")
    h2.markdown("**模型 (Model)**")
    h3.markdown("**类型**")
    h4.markdown("**上下文**")
    h5.markdown("**价格(In/Out)**")
    h6.markdown("**来源**")
    st.divider()
    
    # Data Rows
    for idx, row in df_filtered.iterrows():
        # Layout: Checkbox | [Logo] Name [Tag] | Type | Context | Price | Provider
        c1, c2, c3, c4, c5, c6 = st.columns([0.5, 4, 1.5, 1.5, 1.5, 2])
        
        # 1. Checkbox
        is_selected = row["Selected"]
        def on_change_wrapper(rid=idx, r=row):
            # Toggle logic
            # Use rid (row_id) to get the real model ID, as r["Model ID"] is the display name
            try:
                p_uuid, m_id = rid.split(":", 1)
                toggle_model_in_pool(p_uuid, m_id)
            except ValueError:
                pass

        c1.checkbox(
            "Select", 
            value=is_selected, 
            key=f"chk_{idx}", 
            label_visibility="collapsed",
            on_change=on_change_wrapper
        )
        
        # 2. Rich Model Name: Logo + Name + Tag
        # Note: 'Logo' and 'Tag' in row are Data URIs
        logo_html = f'<img src="{row["Logo"]}" style="height:20px; vertical-align:middle; margin-right:8px;">' if row["Logo"] else ''
        tag_html = f'<img src="{row["Tag"]}" style="height:20px; vertical-align:middle; margin-left:8px;">' if row["Tag"] else ''
        name_html = f'<span style="font-weight:600; font-size:1em; vertical-align:middle;">{row["Model ID"]}</span>'
        
        c2.markdown(f"""
        <div style="display:flex; align-items:center; height: 100%;">
            {logo_html}
            {name_html}
            {tag_html}
        </div>
        """, unsafe_allow_html=True)
        
        # 3. Type
        c3.markdown(f"<div style='margin-top: 5px;'>{row['Type']}</div>", unsafe_allow_html=True)
        
        # 4. Context
        c4.markdown(f"<div style='margin-top: 5px;'>{row['Context Window']}</div>", unsafe_allow_html=True)
        
        # 5. Price
        c5.markdown(f"<div style='margin-top: 5px; font-size:0.9em;'>{row['Input Price ($/1M)']}<br>{row['Output Price ($/1M)']}</div>", unsafe_allow_html=True)
        
        # 6. Provider
        c6.markdown(f"<div style='margin-top: 5px;'>{row['Provider']}</div>", unsafe_allow_html=True)
        
        # Separator line
        st.markdown("<hr style='margin: 0.2em 0; opacity: 0.2;'>", unsafe_allow_html=True)

    if not df_filtered.empty:
        st.caption(f"共显示 {len(df_filtered)} 个模型")
    else:
        st.info("没有匹配的模型。")


# 2. 备战池 (Prep Pool)
st.subheader("2. 🏊 备战池")

if not st.session_state.prep_pool:
    st.info("👈 请在上方列表中勾选参赛选手...")
else:
    # Interactive Pool with Remove Buttons
    cols = st.columns(4)
    for i, item in enumerate(st.session_state.prep_pool):
        with cols[i % 4]:
            # Resolve provider name
            p_name = "Unknown"
            if "provider_uuid" in item:
                 p_obj = next((p for p in st.session_state.providers if p.get("uuid") == item["provider_uuid"]), None)
                 if p_obj:
                     p_name = p_obj["name"]
            elif "provider_idx" in item:
                 idx = item["provider_idx"]
                 if 0 <= idx < len(st.session_state.providers):
                     p_name = st.session_state.providers[idx]["name"]
            
            m_id = item["model_id"]
            
            container = st.container(border=True)
            
            # Logo
            logo_path = get_provider_logo(p_name)
            if logo_path:
                container.image(logo_path, width=40)
            
            container.caption(f"@{p_name}")
            container.markdown(f"**{m_id}**")
            if container.button("移除", key=f"rem_{i}_{m_id}", use_container_width=True):
                st.session_state.prep_pool.remove(item)
                save_prep_pool()
                st.rerun()


# 3. 全局参数配置 (Global Config)
st.subheader("3. ⚙️ 全局参数配置")
st.info("💡 提示：此处的配置将应用于【铁人三项】等所有竞技场项目。")

with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.session_state.inference_config["temperature"] = st.slider(
            "Temperature (随机性)", 
            min_value=0.0, 
            max_value=2.0, 
            value=float(st.session_state.inference_config.get("temperature", 0.7)),
            step=0.1,
            help="较高的值会使输出更加随机，而较低的值会使其更加集中和确定。"
        )
        
    with c2:
        st.session_state.inference_config["max_tokens"] = st.number_input(
            "Max Tokens (最大长度)", 
            min_value=100, 
            max_value=128000, 
            value=int(st.session_state.inference_config.get("max_tokens", 6000)),
            step=1000,
            help="模型生成的最大 token 数量。"
        )
        
    with c3:
        st.session_state.inference_config["top_p"] = st.slider(
            "Top P (核采样)", 
            min_value=0.0, 
            max_value=1.0, 
            value=float(st.session_state.inference_config.get("top_p", 1.0)),
            step=0.05,
            help="控制模型生成的词汇范围，1.0 表示考虑所有词汇。"
        )

# Add a spacer
st.markdown("<br>", unsafe_allow_html=True)
st.success("✅ 配置已实时生效！请前往左侧【铁人三项综合竞技场】开始比赛。")
