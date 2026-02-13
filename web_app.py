import streamlit as st
import pandas as pd
from openai import OpenAI
import plotly.express as px
from datetime import datetime
import re

# --- 1. 商业配置 ---
st.set_page_config(page_title="AI 数据审计终端 V9.0 | 安全版", page_icon="🛡️", layout="wide")

# 初始化所有状态
for key in ["logged_in", "df_cleaned", "messages", "history_log", "current_file"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ([] if key in ["messages", "history_log"] else None)

# --- 2. 登录系统 ---
if not st.session_state["logged_in"]:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("🔐 商业授权登录")
        invite = st.text_input("邀请码 (内测期: VIP888)", type="password")
        if st.button("解锁商业功能", use_container_width=True):
            if invite == "VIP888":
                st.session_state["logged_in"] = True
                st.rerun()
    st.stop()

OFFICIAL_KEY = st.secrets.get("DEEPSEEK_API_KEY")

# --- 3. 脱敏逻辑工具箱 ---
def mask_sensitive_data(df):
    """自动化脱敏算法：保护客户隐私"""
    df_masked = df.copy()
    for col in df_masked.columns:
        col_str = str(col)
        if "电话" in col_str or "手机" in col_str or "联系方式" in col_str:
            df_masked[col] = df_masked[col].astype(str).apply(lambda x: x[:3] + "****" + x[-4:] if len(x) >= 7 else x)
        elif "姓名" in col_str or "客户名" in col_str:
            df_masked[col] = df_masked[col].astype(str).apply(lambda x: x[0] + "*" + x[-1] if len(x) >= 2 else x)
    return df_masked

# --- 4. 侧边栏：安全与文件控制 ---
with st.sidebar:
    st.title("🛡️ 安全控制台")
    st.success("✅ AI 官方引擎已托管")
    
    privacy_mode = st.toggle("🔒 开启 AI 隐私保护模式", value=True)
    
    st.divider()
    uploaded_file = st.file_uploader("📂 上传业务报表", type=["xlsx", "csv"])
    
    if uploaded_file and uploaded_file.name != st.session_state["current_file"]:
        st.session_state.update({"df_cleaned": None, "messages": [], "current_file": uploaded_file.name})

    if st.button("🚪 退出并销毁缓存"):
        st.session_state.clear()
        st.rerun()

# --- 5. 主程序 ---
st.title("📊 AI 自动化办公看板 V9.0")

if uploaded_file:
    if st.session_state["df_cleaned"] is None:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        st.session_state["df_cleaned"] = pd.read_csv(uploaded_file) if file_ext == "csv" else pd.read_excel(uploaded_file)
        st.session_state["history_log"].insert(0, {"时间": datetime.now().strftime("%H:%M:%S"), "文件名": uploaded_file.name, "行数": len(st.session_state["df_cleaned"])})

    df_raw = st.session_state["df_cleaned"]
    
    tab_chart, tab_data, tab_ai = st.tabs(["📈 动态分布", "💎 数据明细", "🤖 AI 专家审计"])
    
    with tab_chart:
        cat_cols = df_raw.select_dtypes(include=['object']).columns.tolist()
        if cat_cols:
            target = st.selectbox("分析维度", cat_cols)
            plot_data = df_raw[target].value_counts().reset_index()
            plot_data.columns = [target, '数量']
            fig = px.bar(plot_data, x=target, y='数量', color='数量', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)

    with tab_data:
        display_df = mask_sensitive_data(df_raw) if privacy_mode else df_raw
        st.dataframe(display_df, use_container_width=True)
        st.download_button("📥 导出数据", data=df_raw.to_csv(index=False), file_name=f"Cleaned_{uploaded_file.name}")

    with tab_ai:
        st.caption("🛡️ 当前已启用隐私保护，样本数据已脱敏。")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        # --- 👇 这里就是截图报错的地方，我已经帮你修好缩进了 ---
        if user_input := st.chat_input("您可以询问关于这份数据的问题..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.write(user_input)
            
            client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com")
            with st.chat_message("assistant"):
                masked_context = mask_sensitive_data(df_raw).head(15).to_string()
                stats_summary = f"列名: {list(df_raw.columns)}\n空值: {df_raw.isnull().sum().to_dict()}"
                
                response = st.write_stream(client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"你是一个数据专家。脱敏样本：\n{masked_context}\n统计摘要：\n{stats_summary}"},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                ))
            st.session_state.messages.append({"role": "assistant", "content": response})
else:
    if st.session_state["history_log"]:
        st.table(pd.DataFrame(st.session_state["history_log"]).head(5))
    st.info("👋 欢迎使用 V9.0 商业版。请在左侧上传报表。")