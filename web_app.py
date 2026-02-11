import streamlit as st
import pandas as pd
from openai import OpenAI
import io
import re
import plotly.express as px

# --- 1. 配置与初始化 ---
st.set_page_config(page_title="AI 自动化办公终端 Pro", page_icon="🦾", layout="wide")
st.markdown('<meta charset="utf-8">', unsafe_allow_html=True)

# 初始化对话记录（如果没有这一行，对话框就不会显示）
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "df_cleaned" not in st.session_state:
    st.session_state["df_cleaned"] = None

# --- 2. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 终端控制台")
    api_key = st.text_input("DeepSeek Key", type="password")
    uploaded_file = st.file_uploader("上传 Excel/CSV", type=["xlsx", "csv"])
    
    if st.session_state["df_cleaned"] is not None:
        st.divider()
        if st.button("🚀 强制规范号码格式"):
            df = st.session_state["df_cleaned"]
            if "电话号码" in df.columns:
                df["电话号码"] = df["电话号码"].astype(str).apply(lambda x: re.sub(r'\D', '', x))
                st.session_state["df_cleaned"] = df
                st.toast("修复成功！")

# --- 3. 主界面 ---
st.title("📊 AI 自动化办公看板 V5.1")

if uploaded_file:
    if st.session_state["df_cleaned"] is None:
        file_type = uploaded_file.name.split(".")[-1].lower()
        st.session_state["df_cleaned"] = pd.read_csv(uploaded_file) if file_type == "csv" else pd.read_excel(uploaded_file)

    df = st.session_state["df_cleaned"]

    # 指标卡
    c1, c2, c3 = st.columns(3)
    c1.metric("数据规模", f"{len(df)} 行")
    bad_count = len(df[df["电话号码"].astype(str).str.len() != 11]) if "电话号码" in df.columns else 0
    c2.metric("异常监测", f"{bad_count} 项", delta=f"-{bad_count}" if bad_count > 0 else "已达标")
    c3.metric("处理引擎", "DeepSeek-V3")

    # --- 核心选项卡 ---
    tab_chart, tab_data, tab_ai = st.tabs(["📈 动态分布分析", "💎 数据明细管理", "🤖 AI 专家解读"])
    
    with tab_chart:
        if "电话号码" in df.columns:
            df['长度'] = df['电话号码'].astype(str).str.len()
            fig = px.bar(df['长度'].value_counts().reset_index(), x='index', y='长度', 
                         labels={'index':'号码长度', '长度':'数量'}, title="号码长度分布（交互式）")
            st.plotly_chart(fig, use_container_width=True)

    with tab_data:
        st.dataframe(df, use_container_width=True)

    # ✨ 重点修复：补全此处的对话逻辑
    with tab_ai:
        st.caption("🤖 我是你的私人数智顾问，你可以问我关于这份数据的任何问题。")
        
        # 1. 展示历史对话
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        # 2. 对话输入框
        if user_input := st.chat_input("例如：请分析一下这份数据的异常原因..."):
            if not api_key:
                st.warning("请在左侧输入 API Key 才能开始对话哦！")
            else:
                # 记录用户输入
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.chat_message("user"):
                    st.write(user_input)
                
                # 调用 AI
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                with st.chat_message("assistant"):
                    # 把数据概况传给 AI，它才能“看懂”你的表
                    data_summary = df.head(5).to_string()
                    stream = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": f"你是一个数据分析专家。当前数据预览：\n{data_summary}"},
                            {"role": "user", "content": user_input}
                        ],
                        stream=True
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.info("💡 请在左侧上传文件以开启 AI 审计模式。")