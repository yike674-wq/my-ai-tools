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
        # 匹配手机号/电话列
        if "电话" in col_str or "手机" in col_str or "联系方式" in col_str:
            df_masked[col] = df_masked[col].astype(str).apply(lambda x: x[:3] + "****" + x[-4:] if len(x) >= 7 else x)
        # 匹配姓名列
        elif "姓名" in col_str or "客户名" in col_str:
            df_masked[col] = df_masked[col].astype(str).apply(lambda x: x[0] + "*" + x[-1] if len(x) >= 2 else x)
    return df_masked

# --- 4. 侧边栏：安全与文件控制 ---
with st.sidebar:
    st.title("🛡️ 安全控制台")
    st.success("✅ AI 官方引擎已托管")
    
    # 核心商业功能：脱敏开关
    privacy_mode = st.toggle("🔒 开启 AI 隐私保护模式", value=True, help="开启后，发往 AI 的数据将自动脱敏，防止泄露姓名和电话。")
    
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
    
    # 顶部指标：增加“脱敏状态”标识
    c1, c2, c3 = st.columns(3)
    c1.metric("数据规模", f"{len(df_raw)} 行")
    c2.metric("隐私保护", "已强化" if privacy_mode else "未开启")
    c3.metric("处理引擎", "DeepSeek-V3")

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
        # 明细页展示脱敏后的效果给用户预览
        display_df = mask_sensitive_data(df_raw) if privacy_mode else df_raw
        st.dataframe(display_df, use_container_width=True)
        st.download_button("📥 导出原始数据报告", data=df_raw.to_csv(index=False), file_name=f"Cleaned_{uploaded_file.name}")

    with tab_ai:
        st.caption("🛡️ 当前已启用隐私围栏，AI 专家无法看到您的完整敏感信息。")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
            if user_input := st.chat_input("您可以询问：这份数据有什么潜在风险？"):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.write(user_input)
            
            client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com")
            with st.chat_message("assistant"):
                # ✨ AI 智力升级：全表统计摘要 + 脱敏样本
                masked_context = mask_sensitive_data(df_raw).head(15).to_string()
                stats_summary = f"列名: {list(df_raw.columns)}\n空值情况: {df_raw.isnull().sum().to_dict()}\n数值概览: {df_raw.describe().to_dict()}"
                
                response = st.write_stream(client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"你是一个数据专家。这是脱敏后的样本数据：\n{masked_context}\n表格统计摘要：\n{stats_summary}"},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                ))
            st.session_state.messages.append({"role": "assistant", "content": response})
else:
    # 商业展示：历史足迹
    if st.session_state["history_log"]:
        st.write("### 📜 近期处理记录")
        st.table(pd.DataFrame(st.session_state["history_log"]).head(5))
    st.info("👋 欢迎使用 V9.0 商业版。请上传报表，开启安全、高效的数据审计之旅。")