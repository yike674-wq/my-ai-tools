import streamlit as st
import pandas as pd
from openai import OpenAI
import plotly.express as px
from datetime import datetime

# --- 1. 核心配置 ---
st.set_page_config(page_title="AI 审计终端 | 增强版", page_icon="🛡️", layout="wide")

for key in ["logged_in", "df_cleaned", "messages", "history_log", "current_file"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ([] if key in ["messages", "history_log"] else None)

# --- 2. 登录验证 ---
if not st.session_state["logged_in"]:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("🔐 商业授权登录")
        invite = st.text_input("演示密钥 (VIP888)", type="password")
        if st.button("进入终端", use_container_width=True):
            if invite == "VIP888":
                st.session_state["logged_in"] = True
                st.rerun()
    st.stop()

OFFICIAL_KEY = st.secrets.get("DEEPSEEK_API_KEY")

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 终端控制")
    privacy_mode = st.toggle("🔒 隐私脱敏", value=True)
    st.divider()
    
    if st.button("✨ 一键加载演示数据", use_container_width=True):
        st.session_state["df_cleaned"] = pd.DataFrame({
            "姓名": ["张伟", "王芳", "李娜", "陈静", "Unknown"],
            "科室": ["内科", "外科", "内科", "儿科", None], # 模拟空值
            "联系电话": ["13800138000", "13912345678", "13799998888", "13511112222", "18666667777"]
        })
        st.session_state["current_file"] = "演示样本_稳定版.xlsx"
        st.session_state["messages"] = []
        st.toast("演示环境已就绪")

    uploaded_file = st.file_uploader("📂 上传自有数据", type=["xlsx", "csv"])
    if uploaded_file and uploaded_file.name != st.session_state["current_file"]:
        st.session_state.update({"df_cleaned": None, "messages": [], "current_file": uploaded_file.name})

    if st.button("🚪 退出登录"):
        st.session_state.clear()
        st.rerun()

# --- 4. 主看板 ---
st.title("📊 AI 自动化办公看板 V10.3")

if st.session_state["df_cleaned"] is not None:
    if uploaded_file and st.session_state["df_cleaned"] is None:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        st.session_state["df_cleaned"] = pd.read_csv(uploaded_file) if file_ext == "csv" else pd.read_excel(uploaded_file)

    df = st.session_state["df_cleaned"]
    tab_chart, tab_data, tab_ai = st.tabs(["📈 数据统计", "💎 明细看板", "🤖 AI 审计"])
    
    with tab_chart:
        # 优化：只选择列中有数据的对象列
        cols = [c for c in df.columns if df[c].nunique() > 0]
        if cols:
            target = st.selectbox("选择分析维度", cols)
            # 💡 核心修复：绘图前先清理空值并重命名列，避免报错
            plot_df = df[target].value_counts(dropna=True).reset_index()
            plot_df.columns = [target, '计数']
            
            if not plot_df.empty:
                fig = px.bar(plot_df, x=target, y='计数', color='计数', text_auto=True,
                            title=f"{target} 维度分布情况")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("该列没有可展示的有效数据。")

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
            
            client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com")
            with st.chat_message("assistant"):
                # 提供更安全的上下文摘要
                summary = f"列名: {list(df.columns)}\n数据量: {len(df)}行\n空值统计: {df.isnull().sum().to_dict()}"
                response = st.write_stream(client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"数据专家。数据摘要：\n{summary}"},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                ))
            st.session_state.messages.append({"role": "assistant", "content": response})
else:
    st.info("💡 终端已就绪，请加载或上传数据。")