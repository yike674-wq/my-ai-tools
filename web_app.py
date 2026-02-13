import streamlit as st
import pandas as pd
from openai import OpenAI
import plotly.express as px
from datetime import datetime

# --- 1. 商业配置 ---
st.set_page_config(page_title="AI 审计终端 | 演示版", page_icon="🏆", layout="wide")

for key in ["logged_in", "df_cleaned", "messages", "history_log", "current_file"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ([] if key in ["messages", "history_log"] else None)

# --- 2. 登录逻辑 ---
if not st.session_state["logged_in"]:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("🛡️ 授权访问")
        invite = st.text_input("演示密钥 (VIP888)", type="password")
        if st.button("解锁功能", use_container_width=True):
            if invite == "VIP888":
                st.session_state["logged_in"] = True
                st.rerun()
    st.stop()

OFFICIAL_KEY = st.secrets.get("DEEPSEEK_API_KEY")

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 演示控制")
    privacy_mode = st.toggle("🔒 隐私保护模式", value=True)
    st.divider()
    
    if st.button("✨ 加载演示数据", use_container_width=True):
        st.session_state["df_cleaned"] = pd.DataFrame({
            "姓名": ["张伟", "王芳", "李娜"],
            "预产期": ["2025-02-09", "2025-03-15", "2025-02-09"],
            "联系电话": ["13800138000", "13912345678", "13799998888"]
        })
        st.session_state["current_file"] = "演示样本.xlsx"
        st.session_state["messages"] = []
        st.session_state["history_log"].insert(0, {"时间": datetime.now().strftime("%H:%M"), "记录": "加载演示数据"})
        st.toast("已就绪")

    uploaded_file = st.file_uploader("📂 上传报表", type=["xlsx", "csv"])
    if uploaded_file and uploaded_file.name != st.session_state["current_file"]:
        st.session_state.update({"df_cleaned": None, "messages": [], "current_file": uploaded_file.name})

    if st.button("🚪 安全退出"):
        st.session_state.clear()
        st.rerun()

# --- 4. 主程序 ---
st.title("📊 AI 自动化办公看板 V10.2")

if st.session_state["df_cleaned"] is not None:
    if uploaded_file and st.session_state["df_cleaned"] is None:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        st.session_state["df_cleaned"] = pd.read_csv(uploaded_file) if file_ext == "csv" else pd.read_excel(uploaded_file)

    df = st.session_state["df_cleaned"]
    tab_chart, tab_data, tab_ai = st.tabs(["📈 分布", "💎 明细", "🤖 AI 审计"])
    
    with tab_chart:
        cols = df.select_dtypes(include=['object']).columns.tolist()
        if cols:
            target = st.selectbox("维度", cols)
            st.plotly_chart(px.bar(df[target].value_counts().reset_index(), x='index', y=target, text_auto=True), use_container_width=True)

    with tab_data:
        display_df = df.copy()
        if privacy_mode:
            for col in display_df.columns:
                if any(x in str(col) for x in ["姓名", "电话", "联系"]):
                    display_df[col] = display_df[col].astype(str).apply(lambda x: x[0] + "*" + x[-1] if len(x)>1 else x)
        st.dataframe(display_df, use_container_width=True)

    with tab_ai:
        st.write("### 🤖 首席 AI 审计官")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if user_input := st.chat_input("询问数据风险..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)
            
            # --- 注意这里必须换行 ---
            client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com")
            with st.chat_message("assistant"):
                context = display_df.head(10).to_string()
                summary = f"列名: {list(df.columns)}\n行数: {len(df)}"
                response = st.write_stream(client.chat.completions.create(model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"数据专家。样本：\n{context}\n全表摘要：\n{summary}"},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                ))
            st.session_state.messages.append({"role": "assistant", "content": response})
else:
    st.info("💡 请点击左侧【加载演示数据】开始体验。")