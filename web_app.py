import streamlit as st
import pandas as pd
from openai import OpenAI
import plotly.express as px
from datetime import datetime

# --- 1. 初始化配置 ---
st.set_page_config(page_title="AI 智能审计终端 V11.3", page_icon="🛡️", layout="wide")

# 初始化状态
for key in ["logged_in", "df_cleaned", "messages", "current_file"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ([] if key == "messages" else None)

# --- 2. 自动化审计引擎 ---
def audit_data(df):
    alerts = []
    if df is None or df.empty: return alerts
    
    # 风险1：电话长度
    if "联系电话" in df.columns:
        invalid_phones = df[df["联系电话"].astype(str).str.len() != 11]
        if not invalid_phones.empty:
            alerts.append(f"❌ {len(invalid_phones)} 个电话号码格式异常")
            
    # 风险2：日期过期
    if "预产期" in df.columns:
        today = datetime.now().strftime("%Y-%m-%d")
        past_due = df[df["预产期"].astype(str) < today]
        if not past_due.empty:
            alerts.append(f"🚩 提醒：有 {len(past_due)} 条记录预产期早于今天")
            
    # 风险3：重复项
    dups = df.duplicated().sum()
    if dups > 0:
        alerts.append(f"🧬 发现 {dups} 条完全重复的数据记录")
        
    return alerts

# --- 3. 登录权限控制 ---
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

# --- 4. 侧边栏：功能回归 ---
with st.sidebar:
    st.title("⚙️ 审计控制台")
    privacy_mode = st.toggle("🔒 隐私脱敏", value=True)
    st.divider()

    # 选项A：加载演示数据
    if st.button("✨ 加载风险演示数据", use_container_width=True):
        st.session_state["df_cleaned"] = pd.DataFrame({
            "姓名": ["张伟", "王芳", "李娜", "陈静", "赵雷", "张伟"],
            "科室": ["内科", "外科", "内科", "儿科", None, "内科"], 
            "预产期": ["2024-01-10", "2025-06-15", "2024-05-09", "2025-08-20", "2024-02-12", "2024-01-10"],
            "联系电话": ["13800138000", "1391234", "13799998888", "13511112222", "18666667777", "13800138000"]
        })
        st.session_state["current_file"] = "Internal_Demo.xlsx"
        st.session_state["messages"] = []
        st.rerun()

    # 选项B：上传自有数据（功能回归！）
    uploaded_file = st.file_uploader("📂 上传业务报表", type=["xlsx", "csv"])
    if uploaded_file and uploaded_file.name != st.session_state["current_file"]:
        # 根据后缀读取数据
        if uploaded_file.name.endswith('.csv'):
            st.session_state["df_cleaned"] = pd.read_csv(uploaded_file)
        else:
            st.session_state["df_cleaned"] = pd.read_excel(uploaded_file)
        st.session_state["current_file"] = uploaded_file.name
        st.session_state["messages"] = []
        st.rerun()

    st.divider()
    if st.button("🚪 退出并销毁记忆"):
        st.session_state.clear()
        st.rerun()

# --- 5. 主看板展示 ---
st.title("📊 AI 自动化办公看板 V11.3")

if st.session_state["df_cleaned"] is not None:
    df = st.session_state["df_cleaned"]
    
    # 自动化审计报告区
    risk_alerts = audit_data(df)
    if risk_alerts:
        for alert in risk_alerts: st.error(alert)
    else:
        st.success("✅ 逻辑扫描未发现明显格式异常")

    tab_ai, tab_viz, tab_data = st.tabs(["🤖 AI 专家诊断", "📈 维度分析", "💎 明细看板"])
    
    with tab_ai:
        st.write("### 🤖 首席 AI 审计官")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if user_input := st.chat_input("您可以追问关于数据的细节..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.write(user_input)
            
            with st.chat_message("assistant"):
                context = f"检测到风险：{risk_alerts}\n数据摘要：{df.describe().to_string()}"
                response = st.write_stream(client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"你是审计专家。{context}"},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                ))
            st.session_state.messages.append({"role": "assistant", "content": response})