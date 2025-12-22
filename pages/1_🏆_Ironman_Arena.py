import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import time
from core.benchmarks import BENCHMARK_SUITE, BenchmarkType, BenchmarkDifficulty, BenchmarkCase, save_benchmarks
from core.schema import ChatMessage, TestResult
from core.ui_utils import get_provider_logo
from providers.openai_compatible import OpenAICompatibleProvider

st.set_page_config(page_title="铁人三项赛场", page_icon="🏆", layout="wide")

st.title("🏆 铁人三项综合竞技场")
st.markdown("在这里，模型将接受涵盖数学、代码、工具调用、指令遵循及创意写作的全方位测试。")

# --- Initialize Benchmarks in Session State ---
if "benchmarks" not in st.session_state:
    st.session_state.benchmarks = BENCHMARK_SUITE

# --- 0. Load Data from Main App ---
if "providers" not in st.session_state:
    st.warning("⚠️ 请先在主页配置服务商！")
    st.stop()
if "prep_pool" not in st.session_state or not st.session_state.prep_pool:
    st.warning("⚠️ 备战池为空，请先在主页选择参赛模型！")
    st.stop()

# --- 1. Prepare Contenders ---
selected_contenders = []
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
        selected_contenders.append((provider_conf, m_id))

# --- Sidebar Config ---
with st.sidebar:
    st.header("⚙️ 比赛设置")
    
    # Initialize config if not present
    if "inference_config" not in st.session_state:
        st.session_state.inference_config = {
            "temperature": 0.7,
            "max_tokens": 6000,
            "top_p": 1.0
        }
    
    st.subheader("1. 难度选择")
    difficulty_level = st.selectbox(
        "选择题目难度",
        ["Easy", "Medium", "Hard"],
        index=1,
        help="不同难度对应不同复杂度的题目"
    )
    
    st.divider()
    st.subheader("2. 统一推理参数")
    st.info("所有参赛模型将使用相同的参数，以确保公平性。")
    
    temp = st.slider(
        "Temperature (随机性)", 
        0.0, 2.0, 
        st.session_state.inference_config["temperature"],
        help="值越高越随机，值越低越确定"
    )
    
    max_tokens = st.number_input(
        "Max Tokens (最大输出长度)", 
        min_value=128, max_value=32000, 
        value=st.session_state.inference_config["max_tokens"],
        step=128,
        help="默认 6000。如果模型不支持该长度，可能会报错。"
    )
    
    top_p = st.slider(
        "Top P (核采样)", 
        0.0, 1.0, 
        st.session_state.inference_config["top_p"],
        help="控制输出的多样性"
    )
    
    # Update state
    st.session_state.inference_config.update({
        "temperature": temp,
        "max_tokens": max_tokens,
        "top_p": top_p
    })
    
    st.divider()
    st.subheader("参赛选手")
    if selected_contenders:
        st.success(f"当前备战池: {len(selected_contenders)} 位选手")
        with st.expander("查看选手名单"):
            for p_conf, m_id in selected_contenders:
                cols = st.columns([1, 5])
                logo = get_provider_logo(p_conf["name"])
                if logo:
                    cols[0].image(logo, width=30)
                else:
                    cols[0].write("🤖")
                cols[1].caption(f"{m_id}\n@{p_conf['name']}")
    else:
        st.warning("备战池为空！请先去主页添加模型。")

# --- Tabs ---
tab_arena, tab_manager = st.tabs(["🏟️ 比赛现场", "📝 题库管理"])

with tab_arena:
    # --- Filter Benchmarks by Difficulty ---
    current_difficulty_enum = BenchmarkDifficulty(difficulty_level)
    filtered_suite = [c for c in st.session_state.benchmarks if c.difficulty == current_difficulty_enum]

    if not filtered_suite:
        st.error(f"该难度 ({difficulty_level}) 下暂无题目！请联系管理员补充题库。")
        # Don't stop here, just show error in tab
    else:
        # --- 2. Race Execution ---
        st.header("🏁 比赛控制台")

        start_btn = st.button("🔥 开启新一轮比赛", type="primary", disabled=len(selected_contenders) == 0)

        if start_btn:
            
            # Reset previous results
            st.session_state.ironman_results = []
            
            # Async Runner
            async def run_single_case(provider_conf, model_id, case):
                provider = OpenAICompatibleProvider(provider_conf["api_key"], provider_conf["base_url"])
                messages = [ChatMessage(role="user", content=case.prompt)]
                
                # Run Inference with Global Config
                try:
                    res = await provider.run_benchmark(
                        model_id, 
                        messages,
                        config=st.session_state.inference_config
                    )
                except Exception as e:
                    res = TestResult(
                        provider=provider_conf["name"],
                        model=model_id,
                        success=False,
                        error_message=f"Request failed: {str(e)}"
                    )

                # Run Evaluation
                if res.success:
                    try:
                        eval_res = case.evaluate(res.response_content)
                        res.score = eval_res["score"]
                        res.evaluation_reason = eval_res["reason"]
                    except Exception as e:
                        res.score = 0.0
                        res.evaluation_reason = f"Evaluation Error: {str(e)}"
                else:
                    res.score = 0.0
                    res.evaluation_reason = res.error_message
                    
                # Add metadata
                res.category = case.category
                res.case_name = case.name
                res.case_type = case.bm_type.value # Store as string for easy filtering
                
                return res

            # Progress bar
            total_steps = len(filtered_suite)
            progress_bar = st.progress(0)
            
            st.subheader("比赛实况")
            
            results_container = st.container()

            async def run_race():
                all_results = []
                
                for i, case in enumerate(filtered_suite):
                    progress_bar.progress((i) / total_steps, text=f"Round {i+1}/{total_steps}: {case.category} - {case.name}")
                    
                    # --- SHOW PROMPT ---
                    st.markdown(f"### 📝 Round {i+1}: {case.name} ({case.category})")
                    st.info(f"**题目**: {case.prompt}")
                    
                    # Create tasks for all contenders
                    tasks = []
                    for p_conf, m_id in selected_contenders:
                        tasks.append(run_single_case(p_conf, m_id, case))
                    
                    # Run batch
                    batch_results = await asyncio.gather(*tasks)
                    all_results.extend(batch_results)
                    
                    # --- SHOW RESULTS (Collapsible) ---
                    cols = st.columns(len(batch_results)) if len(batch_results) <= 4 else [st.container() for _ in range(len(batch_results))]
                    
                    for res in batch_results:
                        # Determine icon and label
                        status_icon = "✅" if res.success else "❌"
                        if res.case_type == "subjective":
                            score_display = "待评分"
                            status_icon = "⚖️"
                        else:
                            score_display = f"{res.score:.1f}分"
                        
                        label = f"{status_icon} **{res.model}** | {score_display} | TPS: {res.tps:.1f}"
                        
                        with st.expander(label, expanded=False):
                            c1, c2 = st.columns([1, 15])
                            logo = get_provider_logo(res.provider)
                            if logo:
                                c1.image(logo, width=25)
                            c2.caption(f"Provider: {res.provider}")
                            
                            if res.success:
                                st.markdown("**回答:**")
                                st.markdown(res.response_content)
                                st.markdown("---")
                                st.markdown(f"**评测详情:** {res.evaluation_reason}")
                            else:
                                st.error(f"Error: {res.error_message}")
                    
                    st.divider()
                    
                progress_bar.progress(1.0, text="比赛结束！")
                return all_results

            # Run the race
            st.session_state.ironman_results = asyncio.run(run_race())
            st.success("本轮测试完成！请进行后续评分或查看结果。")


    # --- 3. Results & Human Grading ---
    if "ironman_results" in st.session_state and st.session_state.ironman_results:
        results_data = [r.dict() for r in st.session_state.ironman_results]
        results_df = pd.DataFrame(results_data)
        
        st.header("3. 👨‍⚖️ 人类判官打分")
        
        # Filter subjective tasks
        subjective_df = results_df[results_df["case_type"] == "subjective"]
        
        if not subjective_df.empty:
            st.warning("以下题目为主观题，必须由您手动打分才能生成最终排名！")
            
            # Get unique subjective cases
            subj_cases = subjective_df["case_name"].unique()
            
            # Dictionary to store user scores
            user_scores = {} 
            
            for case_name in subj_cases:
                st.subheader(f"📝 {case_name}")
                
                # Get the case object to show criteria
                case_obj = next((c for c in filtered_suite if c.name == case_name), None)
                if case_obj:
                    st.caption(f"评分标准: {case_obj.scoring_criteria}")
                    st.info(f"题目: {case_obj.prompt}")
                
                # Get rows for this case
                case_rows = subjective_df[subjective_df["case_name"] == case_name]
                
                cols = st.columns(len(case_rows)) if len(case_rows) <= 3 else [st.container() for _ in range(len(case_rows))]
                
                for idx, (_, row) in enumerate(case_rows.iterrows()):
                    col_idx = idx % 3
                    with cols[col_idx]:
                        with st.expander(f"📄 {row['model']} 的回答", expanded=True):
                            st.markdown(row['response_content'])
                        
                        # Slider for score
                        score_key = f"score_{row['model']}_{case_name}"
                        new_score = st.slider(
                            f"给 {row['model']} 打分", 
                            0, 100, 50, 
                            key=score_key
                        )
                        user_scores[(row['model'], case_name)] = new_score
                st.divider()
            
            if st.button("✅ 提交评分并生成榜单", type="primary"):
                # Update scores in session state
                for res in st.session_state.ironman_results:
                    if res.case_type == "subjective":
                        key = (res.model, res.case_name)
                        if key in user_scores:
                            res.score = float(user_scores[key])
                            res.evaluation_reason = f"Human Graded: {res.score}"
                
                st.session_state.scores_submitted = True
                st.rerun()
                
        else:
            st.session_state.scores_submitted = True

        # --- 4. Final Leaderboard ---
        if st.session_state.get("scores_submitted", False):
            st.header("4. 🏆 最终排行榜")
            
            # Recalculate dataframe from updated session state
            final_data = [r.dict() for r in st.session_state.ironman_results]
            final_df = pd.DataFrame(final_data)
            
            # Pivot table: Models vs Categories
            pivot_df = final_df.pivot_table(
                index="model", 
                columns="category", 
                values="score", 
                aggfunc="mean"
            ).fillna(0)
            
            pivot_df["总分"] = pivot_df.sum(axis=1)
            pivot_df = pivot_df.sort_values("总分", ascending=False)
            
            # Display Leaderboard
            st.dataframe(
                pivot_df.style.highlight_max(axis=0, color="lightgreen"), 
                use_container_width=True
            )
            
            # Radar Chart
            st.subheader("能力雷达图")
            if not pivot_df.empty:
                # Melt for plotly
                radar_df = pivot_df.reset_index().melt(
                    id_vars=["model", "总分"], 
                    var_name="能力维度", 
                    value_name="得分"
                )
                # Remove "总分" from radar
                radar_df = radar_df[radar_df["能力维度"] != "总分"]
                
                fig = px.line_polar(
                    radar_df, 
                    r="得分", 
                    theta="能力维度", 
                    color="model", 
                    line_close=True,
                    range_r=[0, 100]
                )
                st.plotly_chart(fig, use_container_width=True)
                
        elif not subjective_df.empty:
            st.info("请完成上方的主观题打分以查看最终榜单。")
        else:
            # If no subjective questions, show results immediately
            st.session_state.scores_submitted = True
            st.rerun()

with tab_manager:
    st.header("📝 题库管理")
    
    # Display current benchmarks
    st.subheader("现有题目")
    
    # Convert to DataFrame for display
    bm_data = []
    for i, case in enumerate(st.session_state.benchmarks):
        bm_data.append({
            "Index": i,
            "Name": case.name,
            "Category": case.category,
            "Type": case.bm_type.value,
            "Difficulty": case.difficulty.value,
            "Prompt": case.prompt[:50] + "..."
        })
    
    st.dataframe(pd.DataFrame(bm_data), use_container_width=True)
    
    st.divider()
    
    # Add New Case
    with st.expander("➕ 添加新题目"):
        with st.form("add_case_form"):
            new_name = st.text_input("题目名称 (Name)")
            new_cat = st.text_input("分类 (Category)", value="通用能力")
            new_prompt = st.text_area("题目内容 (Prompt)")
            
            c1, c2 = st.columns(2)
            new_type = c1.selectbox("类型 (Type)", [t.value for t in BenchmarkType])
            new_diff = c2.selectbox("难度 (Difficulty)", [d.value for d in BenchmarkDifficulty])
            
            new_criteria = st.text_area("评分标准 (Scoring Criteria)")
            
            # Type specific fields
            new_ref = st.text_area("参考答案/JSON Schema (Reference) - Optional")
            new_test_code = st.text_area("测试代码 (Test Code) - Optional")
            new_keywords = st.text_input("关键词 (Keywords, comma separated) - Optional")
            
            submitted = st.form_submit_button("添加")
            
            if submitted:
                if not new_name or not new_prompt:
                    st.error("名称和题目内容不能为空！")
                else:
                    # Create object
                    try:
                        # Parse reference if it looks like JSON
                        ref_val = new_ref
                        if new_ref.strip().startswith("{") or new_ref.strip().startswith("["):
                            import json
                            try:
                                ref_val = json.loads(new_ref)
                            except:
                                pass # Keep as string
                        
                        kw_list = [k.strip() for k in new_keywords.split(",")] if new_keywords else []
                        
                        new_case = BenchmarkCase(
                            name=new_name,
                            category=new_cat,
                            prompt=new_prompt,
                            bm_type=BenchmarkType(new_type),
                            difficulty=BenchmarkDifficulty(new_diff),
                            scoring_criteria=new_criteria,
                            reference=ref_val if ref_val else None,
                            test_code=new_test_code if new_test_code else None,
                            keywords=kw_list
                        )
                        st.session_state.benchmarks.append(new_case)
                        save_benchmarks(st.session_state.benchmarks)
                        st.success("添加成功！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"添加失败: {e}")

    # Edit/Delete Case
    with st.expander("🛠️ 编辑/删除 题目"):
        edit_idx = st.selectbox("选择题目编辑", options=range(len(st.session_state.benchmarks)), format_func=lambda x: f"{x}: {st.session_state.benchmarks[x].name}")
        
        if edit_idx is not None:
            case_to_edit = st.session_state.benchmarks[edit_idx]
            
            with st.form("edit_case_form"):
                e_name = st.text_input("名称", value=case_to_edit.name)
                e_cat = st.text_input("分类", value=case_to_edit.category)
                e_prompt = st.text_area("题目", value=case_to_edit.prompt)
                
                # We need to find index of current type/difficulty
                type_opts = [t.value for t in BenchmarkType]
                diff_opts = [d.value for d in BenchmarkDifficulty]
                
                c1, c2 = st.columns(2)
                e_type = c1.selectbox("类型", type_opts, index=type_opts.index(case_to_edit.bm_type.value))
                e_diff = c2.selectbox("难度", diff_opts, index=diff_opts.index(case_to_edit.difficulty.value))
                
                e_criteria = st.text_area("评分标准", value=case_to_edit.scoring_criteria)
                
                # Reference handling
                ref_str = ""
                if case_to_edit.reference:
                    if isinstance(case_to_edit.reference, (dict, list)):
                        import json
                        ref_str = json.dumps(case_to_edit.reference, indent=2, ensure_ascii=False)
                    else:
                        ref_str = str(case_to_edit.reference)
                
                e_ref = st.text_area("参考答案/JSON Schema", value=ref_str)
                e_test_code = st.text_area("测试代码", value=case_to_edit.test_code or "")
                
                kw_str = ", ".join(case_to_edit.keywords) if case_to_edit.keywords else ""
                e_keywords = st.text_input("关键词", value=kw_str)
                
                save_edit = st.form_submit_button("保存修改")
                
                if save_edit:
                    try:
                        # Parse reference
                        ref_val = e_ref
                        if e_ref.strip().startswith("{") or e_ref.strip().startswith("["):
                            import json
                            try:
                                ref_val = json.loads(e_ref)
                            except:
                                pass
                        
                        kw_list = [k.strip() for k in e_keywords.split(",")] if e_keywords else []
                        
                        # Update object
                        case_to_edit.name = e_name
                        case_to_edit.category = e_cat
                        case_to_edit.prompt = e_prompt
                        case_to_edit.bm_type = BenchmarkType(e_type)
                        case_to_edit.difficulty = BenchmarkDifficulty(e_diff)
                        case_to_edit.scoring_criteria = e_criteria
                        case_to_edit.reference = ref_val if ref_val else None
                        case_to_edit.test_code = e_test_code if e_test_code else None
                        case_to_edit.keywords = kw_list
                        
                        save_benchmarks(st.session_state.benchmarks)
                        st.success("修改保存成功！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"保存失败: {e}")
            
            if st.button("🗑️ 删除此题目", key="del_btn"):
                st.session_state.benchmarks.pop(edit_idx)
                save_benchmarks(st.session_state.benchmarks)
                st.success("删除成功！")
                st.rerun()

