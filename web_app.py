import streamlit as st
import pandas as pd
from openai import OpenAI
import plotly.express as px
from datetime import datetime

# --- 1. 初始化 ---
st.set_page_config(page_title="AI 智能审计终端 V11.1", page_icon="🛡️", layout="wide")

for key in ["logged_in", "df_cleaned", "messages", "current_file"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ([] if key == "messages" else None)

# --- 2. 自动审计逻辑 (已验证有效) ---
def audit_data(df):
    alerts = []
    if "联系电话" in df.columns:
        invalid_phones = df[df["联系电话"].astype(str).str.len() != 11]
        if not invalid_phones.empty:
            alerts.append(f"❌ {len(invalid_phones)} 个电话号码格式异常")
    if "预产期" in df.columns:
        today = datetime.now().strftime("%Y-%m-%d")
        past_due = df[df["预产期"].astype(str) < today]
        if not past_due.empty:
            alerts.append(f"🚩 提醒：有 {len(past_due)} 条记录预产期早于今天")
    return alerts

# --- 3. 登录逻辑 ---
if not st.session_state["logged_in"]:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("🛡️ 审计系统授权")
        invite = st.text_input("演示密钥 (VIP888)", type="password")
        if st.button("解锁进入", use_container_width=True):
            if invite == "VIP888":
                st.session_state["logged_in"] = True
                st.rerun()
    st.stop()

OFFICIAL_KEY = st.secrets.get("DEEPSEEK_API_KEY")

# --- 4. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 审计控制台")
    privacy_mode = st.toggle("🔒 隐私脱敏", value=True)
    if st.button("✨ 加载风险演示数据", use_container_width=True):
        st.session_state["df_cleaned"] = pd.DataFrame({
            "姓名": ["张伟", "王芳", "李娜", "陈静", "赵雷"],
            "科室": ["内科", "外科", "内科", "儿科", None], # 包含空值
            "预产期": ["2024-01-10", "2025-06-15", "2024-05-09", "2025-08-20", "2024-02-12"],
            "联系电话": ["13800138000", "1391234", "13799998888", "13511112222", "18666667777"]
        })
        st.session_state["current_file"] = "风险样本.xlsx"
        st.session_state["messages"] = []
        st.rerun()

    if st.button("🚪 退出系统"):
        st.session_state.clear()
        st.rerun()

# --- 5. 主看板 ---
st.title("📊 AI 自动化办公看板 V11.1")

if st.session_state["df_cleaned"] is not None:
    df = st.session_state["df_cleaned"]
    
    # 风险扫描展示
    risk_alerts = audit_data(df)
    for alert in risk_alerts:
        st.error(alert)

    tab_ai, tab_viz, tab_data = st.tabs(["🤖 AI 专家诊断", "📈 交叉统计", "💎 脱敏明细"])
    
    with tab_ai:
        st.write("### 🤖 首席 AI 审计官")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if user_input := st.chat_input("询问更多细节..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.write(user_input)
            client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com")
            with st.chat_message("assistant"):
                context = f"风险列表：{risk_alerts}\n数据摘要：{df.describe().to_string()}"
                response = st.write_stream(client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"你是审计专家。{context}"},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                ))
            st.session_state.messages.append({"role": "assistant", "content": response})

    with tab_viz:
        st.subheader("📊 维度分布分析")
        col_x = st.selectbox("选择分析维度", df.columns, index=1)
        
        # 💡 核心修复：安全绘图逻辑
        # 1. 剔除空值 2. 统计频次 3. 强制重命名列名防止冲突
        plot_data = df[col_x].value_counts(dropna=True).reset_index()
        plot_data.columns = ['维度', '计数'] 
        
        if not plot_data.empty:
            fig = px.bar(plot_data, x='维度', y='计数', color='计数', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("所选维度没有有效数据可供显示。") 
    with tab_data:
        display_df = df.copy()
        if privacy_mode:
            for col in display_df.columns:
                if any(x in str(col) for x in ["姓名", "电话"]):
                    display_df[col] = display_df[col].astype(str).apply(lambda x: x[0] + "*" + x[-1] if len(x)>1 else x)
        st.dataframe(display_df, use_container_width=True)
        else:
            st.info("💡 请在左侧加载演示数据。")
   