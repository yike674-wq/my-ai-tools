import streamlit as st
import pandas as pd
from openai import OpenAI
import plotly.express as px
from datetime import datetime

# --- 1. 核心配置 ---
st.set_page_config(page_title="AI 智能审计终端 V11.4", page_icon="🛡️", layout="wide")

# 初始化所有状态
for key in ["logged_in", "df_cleaned", "messages", "current_file"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ([] if key == "messages" else None)

# --- 2. 自动化审计引擎 ---
def audit_data(df):
    alerts = []
    if df is None or df.empty: return alerts
    
    # 逻辑1：电话校验
    if "联系电话" in df.columns:
        invalid = df[df["联系电话"].astype(str).str.len() != 11]
        if not invalid.empty: alerts.append(f"❌ {len(invalid)} 个电话号码格式异常")
            
    # 逻辑2：过期校验
    if "预产期" in df.columns:
        today = datetime.now().strftime("%Y-%m-%d")
        past = df[df["预产期"].astype(str) < today]
        if not past.empty: alerts.append(f"🚩 提醒：有 {len(past)} 条记录预产期早于今天")
            
    # 逻辑3：重复项校验
    dups = df.duplicated().sum()
    if dups > 0: alerts.append(f"🧬 发现 {dups} 条完全重复的数据记录")
        
    return alerts

# --- 3. 登录与身份校验 ---
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

# 💡 关键修复：提前准备好 AI 连接器，防止 NameError
OFFICIAL_KEY = st.secrets.get("DEEPSEEK_API_KEY")
client = None
if OFFICIAL_KEY:
    client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com")

# --- 4. 侧边栏：功能全家桶 ---
with st.sidebar:
    st.title("⚙️ 审计控制台")
    privacy_mode = st.toggle("🔒 隐私脱敏模式", value=True)
    st.divider()

    # 功能A：演示数据
    if st.button("✨ 加载风险演示数据", use_container_width=True):
        st.session_state.update({
            "df_cleaned": pd.DataFrame({
                "姓名": ["张伟", "王芳", "李娜", "陈静", "赵雷", "张伟"],
                "科室": ["内科", "外科", "内科", "儿科", None, "内科"], 
                "预产期": ["2024-01-10", "2025-06-15", "2024-05-09", "2025-08-20", "2024-02-12", "2024-01-10"],
                "联系电话": ["13800138000", "1391234", "13799998888", "13511112222", "18666667777", "13800138000"]
            }),
            "current_file": "Internal_Demo.xlsx",
            "messages": []
        })
        st.rerun()

    # 功能B：上传自有数据 (回归！)
    uploaded_file = st.file_uploader("📂 上传业务报表 (Excel/CSV)", type=["xlsx", "csv"])
    if uploaded_file and uploaded_file.name != st.session_state["current_file"]:
        try:
            st.session_state["df_cleaned"] = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            st.session_state.update({"current_file": uploaded_file.name, "messages": []})
            st.rerun()
        except Exception as e:
            st.error(f"读取失败: {e}")

    st.divider()
    if st.button("🚪 退出并清空缓存"):
        st.session_state.clear()
        st.rerun()

# --- 5. 主看板 ---
st.title("📊 AI 自动化办公看板 V11.4")

if st.session_state["df_cleaned"] is not None:
    df = st.session_state["df_cleaned"]
    
    # 1. 风险报告展示
    risk_alerts = audit_data(df)
    for alert in risk_alerts: st.error(alert)

    # 2. 功能标签页
    tab_ai, tab_viz, tab_data = st.tabs(["🤖 AI 专家诊断", "📈 维度分析", "💎 明细看板"])
    
    with tab_ai:
        st.write("### 🤖 首席 AI 审计官")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if user_input := st.chat_input("询问数据细节，例如：‘哪几行是重复的？’"):
            if not client:
                st.warning("⚠️ 未检测到 API Key，请检查 Secrets 配置。")
            else:
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.chat_message("user"): st.write(user_input)
                
                with st.chat_message("assistant"):
                    # 增强 AI 的上下文理解
                    dup_info = df[df.duplicated(keep=False)].to_string() if df.duplicated().any() else "无重复"
                    context = f"风险点：{risk_alerts}\n重复行数据：\n{dup_info}\n全表预览：\n{df.head().to_string()}"
                    
                    response = st.write_stream(client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": f"你是资深审计专家。当前数据背景：\n{context}"},
                            {"role": "user", "content": user_input}
                        ],
                        stream=True
                    ))
                st.session_state.messages.append({"role": "assistant", "content": response})

    with tab_viz:
        col_x = st.selectbox("选择统计维度", df.columns, index=0)
        plot_data = df[col_x].fillna("（空）").astype(str).value_counts().reset_index()
        plot_data.columns = ['分类', '数量']
        st.plotly_chart(px.bar(plot_data, x='分类', y='数量', color='数量', text_auto=True), use_container_width=True)

    with tab_data:
        display_df = df.copy()
        if privacy_mode:
            for col in display_df.columns:
                if any(x in str(col) for x in ["姓名", "电话", "联系"]):
                    display_df[col] = display_df[col].astype(str).apply(lambda x: x[0] + "*" + x[-1] if len(x)>1 else x)
        st.dataframe(display_df, use_container_width=True)
else:
    st.info("👋 欢迎回来！请在左侧【上传文件】或加载【演示数据】开始工作。")