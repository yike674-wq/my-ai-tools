import streamlit as st
import pandas as pd
from openai import OpenAI
import plotly.express as px
from datetime import datetime

# --- 1. 初始化配置 ---
st.set_page_config(page_title="AI 智能审计终端 V11.0", page_icon="🛡️", layout="wide")

# 确保状态机完整
for key in ["logged_in", "df_cleaned", "messages", "current_file"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ([] if key == "messages" else None)

# --- 2. 【新增】自动化审计逻辑函数 ---
def audit_data(df):
    """这是程序的自动安检机，负责发现硬伤"""
    alerts = []
    
    # 风险1：电话号码长度校验
    if "联系电话" in df.columns:
        # 将非字符串转为字符串，计算长度不等于11位的记录
        invalid_phones = df[df["联系电话"].astype(str).str.len() != 11]
        if not invalid_phones.empty:
            alerts.append(f"❌ 发现 {len(invalid_phones)} 个电话号码格式错误（非11位）")
            
    # 风险2：重复数据校验
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        alerts.append(f"🧬 发现 {dup_count} 条完全重复的记录行")
        
    # 风险3：逻辑漏洞（演示：预产期已过期）
    if "预产期" in df.columns:
        today = datetime.now().strftime("%Y-%m-%d")
        past_due = df[df["预产期"] < today]
        if not past_due.empty:
            alerts.append(f"🚩 提醒：有 {len(past_due)} 条记录预产期早于今天，请确认状态")
            
    return alerts

# --- 3. 登录权限（沿用 V10.3 成功逻辑） ---
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

# --- 4. 侧边栏与数据加载 ---
with st.sidebar:
    st.title("⚙️ 审计控制台")
    privacy_mode = st.toggle("🔒 隐私脱敏开关", value=True)
    
    # 演示数据：特意构造一些错误数据供演示
    if st.button("✨ 加载带风险的演示数据", use_container_width=True):
        st.session_state["df_cleaned"] = pd.DataFrame({
            "姓名": ["张伟", "王芳", "李娜", "陈静", "张伟"], # 故意包含重复人
            "科室": ["内科", "外科", "内科", "儿科", "内科"],
            "预产期": ["2024-01-10", "2025-06-15", "2025-03-09", "2025-08-20", "2024-01-10"], # 包含过期时间
            "联系电话": ["13800138000", "1391234", "13799998888", "13511112222", "13800138000"] # 包含错误长度
        })
        st.session_state["current_file"] = "演示风险样本.xlsx"
        st.session_state["messages"] = []
    
    uploaded_file = st.file_uploader("📂 或上传自有业务表", type=["xlsx", "csv"])
    if st.button("🚪 退出并销毁记忆"):
        st.session_state.clear()
        st.rerun()

# --- 5. 主看板 ---
st.title("📊 AI 自动化办公看板 V11.0")

if st.session_state["df_cleaned"] is not None:
    df = st.session_state["df_cleaned"]
    
    # 🚀 【亮点】自动审计结果展示
    st.markdown("### 🚨 风险自动扫描")
    risk_alerts = audit_data(df)
    if risk_alerts:
        for alert in risk_alerts:
            st.error(alert)
    else:
        st.success("✅ 基础逻辑扫描通过，未发现格式异常")

    # 功能标签页
    tab_ai, tab_viz, tab_data = st.tabs(["🤖 AI 专家诊断", "📈 交叉统计", "💎 脱敏明细"])
    
    with tab_ai:
        st.write("### 🤖 首席 AI 审计官")
        # 显示对话历史
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
            
        if user_input := st.chat_input("您可以追问：‘那几个电话号码错在哪里了？’"):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.write(user_input)
            
            client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com")
            with st.chat_message("assistant"):
                # 把逻辑审计的结果也告诉 AI，增强它的诊断能力
                context_info = f"系统检测到以下风险：{risk_alerts}。数据样本如下：{df.head(10).to_string()}"
                response = st.write_stream(client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"你是一名资深审计专家。当前环境：{context_info}"},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                ))
            st.session_state.messages.append({"role": "assistant", "content": response})

    with tab_viz:
        # 交叉分析逻辑
        col_x = st.selectbox("选择分类维度", df.columns, index=1)
        st.plotly_chart(px.bar(df[col_x].value_counts().reset_index(), x='index', y=col_x, text_auto=True), use_container_width=True)

    with tab_data:
        # 脱敏展示
        display_df = df.copy()
        if privacy_mode:
            for col in display_df.columns:
                if any(x in str(col) for x in ["姓名", "电话"]):
                    display_df[col] = display_df[col].astype(str).apply(lambda x: x[0] + "*" + x[-1] if len(x)>1 else x)
        st.dataframe(display_df, use_container_width=True)
else:
    st.info("👋 请在侧边栏点击【加载带风险的演示数据】或上传文件开始审计。")