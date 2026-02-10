import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
from openai import OpenAI
import io
import re  # 用于正则修复号码

# --- 1. 页面高级配置 ---
st.set_page_config(page_title="AI 自动化办公终端", page_icon="🦾", layout="wide")

# 自定义样式
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .success-text { color: #28a745; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 初始化核心存储 ---
if "messages" not in st.session_state: st.session_state["messages"] = []
if "df_cleaned" not in st.session_state: st.session_state["df_cleaned"] = None

# --- 3. 侧边栏：工具箱 ---
with st.sidebar:
    st.title("⚙️ 自动化控制台")
    api_key = st.text_input("DeepSeek API Key", type="password")
    
    st.divider()
    st.subheader("📂 数据上传")
    uploaded_file = st.file_uploader("上传 Excel/CSV", type=["xlsx", "csv"])
    
    # --- ✨ 新增：数据清洗工具箱 ---
    if st.session_state["df_cleaned"] is not None:
        st.divider()
        st.subheader("🧹 自动化修复工具")
        
        if st.button("🚀 一键修复异常格式"):
            df = st.session_state["df_cleaned"]
            # 逻辑：只保留数字，清理掉横杠、空格等
            if "电话号码" in df.columns:
                df["电话号码"] = df["电话号码"].astype(str).apply(lambda x: re.sub(r'\D', '', x))
                st.session_state["df_cleaned"] = df
                st.toast("已完成格式强力修复！", icon="✅")
            else:
                st.error("未找到‘电话号码’列")

        if st.button("🗑️ 快速清理重复行"):
            df = st.session_state["df_cleaned"]
            before_count = len(df)
            df = df.drop_duplicates()
            st.session_state["df_cleaned"] = df
            st.toast(f"清理完成！删除了 {before_count - len(df)} 行重复数据。")

# --- 4. 主界面：看板展示 ---
st.title("🦾 AI 自动化办公终端")
st.caption("已集成：AI 审计 + 自动化修复 + 结果导出")

if uploaded_file:
    # 只有第一次上传时才初始化 df_cleaned
    if st.session_state["df_cleaned"] is None:
        file_type = uploaded_file.name.split(".")[-1].lower()
        if file_type == "csv":
            st.session_state["df_cleaned"] = pd.read_csv(uploaded_file)
        else:
            st.session_state["df_cleaned"] = pd.read_excel(uploaded_file)

    df = st.session_state["df_cleaned"]

    # 指标卡
    col1, col2, col3 = st.columns(3)
    col1.metric("当前总行数", f"{len(df)} 行")
    
    anomalies = 0
    if "电话号码" in df.columns:
        anomalies = len(df[df["电话号码"].astype(str).str.len() != 11])
    col2.metric("疑似异常", f"{anomalies} 项", delta=f"-{anomalies}" if anomalies > 0 else "0", delta_color="inverse")
    col3.metric("处理状态", "已同步更新")

    # 展示与下载
    tab1, tab2 = st.tabs(["💎 处理后的数据", "💬 AI 咨询说明"])
    
    with tab1:
        st.dataframe(df, use_container_width=True, height=300)
        
        # 导出修复后的 Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button(
            label="📥 下载已修复的 Excel 文件",
            data=buffer.getvalue(),
            file_name=f"Fixed_{uploaded_file.name}",
            mime="application/vnd.ms-excel"
        )

    with tab2:
        # AI 对话逻辑 (保持之前的稳定版)
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        user_input = st.chat_input("针对修复后的数据提问...")
        if user_input:
            if not api_key: st.warning("请先配置 API Key"); st.stop()
            st.session_state["messages"].append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.write(user_input)
            
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            try:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "你是数据处理专家"}, {"role": "user", "content": f"数据预览：\n{df.head().to_string()}\n问题：{user_input}"}],
                        stream=True
                    )
                    response = st.write_stream(stream)
                st.session_state["messages"].append({"role": "assistant", "content": response})
            except Exception as e: st.error(f"AI 响应失败: {e}")

else:
    st.info("👋 欢迎！请在左侧上传文件开始自动化旅程。")
    st.session_state["df_cleaned"] = None # 清除旧缓存