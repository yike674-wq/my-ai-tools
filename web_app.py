import streamlit as st
import pandas as pd
from openai import OpenAI
import io
import re
import plotly.express as px  # ✨ 新零件：动态图表

# --- 1. 页面高级配置 ---
st.set_page_config(page_title="AI 自动化办公终端 Pro", page_icon="🦾", layout="wide")

# 强制编码保险
st.markdown('<meta charset="utf-8">', unsafe_allow_html=True)

# 样式美化
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 20px; height: 3em; background: linear-gradient(45deg, #007bff, #00d2ff); color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 状态保持 ---
if "df_cleaned" not in st.session_state: st.session_state["df_cleaned"] = None

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 终端控制台")
    api_key = st.text_input("DeepSeek Key", type="password")
    uploaded_file = st.file_uploader("上传 Excel/CSV", type=["xlsx", "csv"])
    
    if st.session_state["df_cleaned"] is not None:
        st.divider()
        st.subheader("🧹 快速修复功能")
        if st.button("🚀 强制规范号码格式"):
            df = st.session_state["df_cleaned"]
            if "电话号码" in df.columns:
                df["电话号码"] = df["电话号码"].astype(str).apply(lambda x: re.sub(r'\D', '', x))
                st.session_state["df_cleaned"] = df
                st.toast("格式修复成功！", icon="✅")
            else: st.error("未找到‘电话号码’列")
        
        if st.button("🗑️ 剔除重复记录"):
            old_len = len(st.session_state["df_cleaned"])
            st.session_state["df_cleaned"] = st.session_state["df_cleaned"].drop_duplicates()
            st.toast(f"清理完成，删除了 {old_len - len(st.session_state['df_cleaned'])} 行")

# --- 4. 主看板 ---
st.title("📊 AI 自动化办公看板 V5.0")

if uploaded_file:
    if st.session_state["df_cleaned"] is None:
        file_type = uploaded_file.name.split(".")[-1].lower()
        st.session_state["df_cleaned"] = pd.read_csv(uploaded_file) if file_type == "csv" else pd.read_excel(uploaded_file)

    df = st.session_state["df_cleaned"]

    # 顶层数据卡片
    c1, c2, c3 = st.columns(3)
    c1.metric("当前数据规模", f"{len(df)} 行")
    
    bad_count = 0
    if "电话号码" in df.columns:
        bad_count = len(df[df["电话号码"].astype(str).str.len() != 11])
    c2.metric("格式异常监测", f"{bad_count} 项", delta=f"-{bad_count}" if bad_count > 0 else "已达标")
    c3.metric("处理引擎", "DeepSeek-V3", delta="Running")

    # 功能分屏
    tab_chart, tab_data, tab_ai = st.tabs(["📈 动态分布分析", "💎 数据明细管理", "🤖 AI 专家解读"])
    
    with tab_chart:
        if "电话号码" in df.columns:
            st.subheader("号码长度分布（交互式）")
            df['len_check'] = df['电话号码'].astype(str).str.len()
            count_df = df['len_check'].value_counts().reset_index()
            count_df.columns = ['长度', '数量']
            
            # 使用 Plotly 绘制动态条形图
            fig = px.bar(count_df, x='长度', y='数量', color='数量', 
                         color_continuous_scale='Viridis', text_auto=True)
            fig.update_layout(clickmode='event+select')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("上传含有电话号码的表格即可查看动态分布。")

    with tab_data:
        st.dataframe(df, use_container_width=True)
        # 导出按钮
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 导出最终审计版本", data=output.getvalue(), file_name="Audited_Data.xlsx")

    with tab_ai:
        st.write("请在此与数据专家对话...")
        # 保持之前的 AI 对话逻辑（此处略，确保代码简洁）
else:
    st.info("💡 首席设计师，请在左侧上传那份 66 行的挑战数据！")