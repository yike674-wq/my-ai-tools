import streamlit as st
import pandas as pd
from openai import OpenAI
import plotly.express as px
from datetime import datetime

# --- 1. 商业品牌配置 ---
st.set_page_config(page_title="AI 智能审计终端 | 商业演示版", page_icon="🏆", layout="wide")

# 初始化状态
for key in ["logged_in", "df_cleaned", "messages", "history_log", "current_file"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ([] if key in ["messages", "history_log"] else None)

def load_demo_data():
    return pd.DataFrame({
        "姓名": ["张伟", "王芳", "李娜", "刘洋", "陈静"],
        "科室": ["内科", "外科", "内科", "儿科", "外科"],
        "预产期": ["2025-02-09", "2025-03-15", "2025-02-09", "2025-05-20", "2025-02-12"],
        "联系电话": ["13800138000", "13912345678", "13799998888", "13511112222", "18666667777"]
    })

# --- 2. 登录系统 ---
if not st.session_state["logged_in"]:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("🛡️ 商业授权访问")
        invite = st.text_input("授权密钥 (VIP888)", type="password")
        if st.button("解锁完整商业功能", use_container_width=True):
            if invite == "VIP888":
                st.session_state["logged_in"] = True
                st.rerun()
    st.stop()

OFFICIAL_KEY = st.secrets.get("DEEPSEEK_API_KEY")

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 演示控制面板")
    privacy_mode = st.toggle("🔒 开启隐私脱敏保护", value=True)
    st.divider()
    
    if st.button("✨ 一键加载预设演示数据", use_container_width=True):
        st.session_state["df_cleaned"] = load_demo_data()
        st.session_state["current_file"] = "演示样本_预产期表.xlsx"
        st.session_state["messages"] = []
        st.session_state["history_log"].insert(0, {"时间": datetime.now().strftime("%H:%M:%S"), "文件名": "演示样本.xlsx"})
        st.toast("演示数据已就绪！")

    uploaded_file = st.file_uploader("📂 上传自有业务报表", type=["xlsx", "csv"])
    if uploaded_file and uploaded_file.name != st.session_state["current_file"]:
        st.session_state.update({"df_cleaned": None, "messages": [], "current_file": uploaded_file.name})

    if st.button("🚪 安全退出"):
        st.session_state.clear()
        st.rerun()

# --- 4. 主程序 ---
st.title("📊 AI 自动化办公看板 V10.1")

if st.session_state["df_cleaned"] is not None:
    # 确保文件被读取
    if uploaded_file and st.session_state["df_cleaned"] is None:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        st.session_state["df_cleaned"] = pd.read_csv(uploaded_file) if file_ext == "csv" else pd.read_excel(uploaded_file)

    df = st.session_state["df_cleaned"]
    
    tab_chart, tab_data, tab_ai, tab_history = st.tabs(["📈 数据分布", "💎 明细看板", "🤖 AI 审计", "📜 流水线"])
    
    with tab_chart:
        cols = df.select_dtypes(include=['object']).columns.tolist()
        if cols:
            target = st.selectbox("选择统计维度", cols)
            plot_df = df[target].value_counts().reset_index()
            plot_df.columns = [target, '数量']
            fig = px.bar(plot_df, x=target, y='数量', color=target, text_auto=True)
            st.plotly_chart(fig, use_container_width=True)

    with tab_data:
        display_df = df.copy()
        if privacy_mode:
            for col in display_df.columns:
                if any(x in str(col) for x in ["姓名", "电话", "联系"]):
                    display_df[col] = display_df[col].astype(str).apply(lambda x: x[0] + "*" + x[-1] if len(x)>1 else x)
        st.dataframe(display_df, use_container_width=True)

    with tab_ai:
        # --- 👇 这里就是报错的地方，已经严格对齐 ---
        st.write("### 🤖 首席 AI 审计官")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if user_input := st.chat_input("询问关于这份数据的问题..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.write(user_input)client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com")
            with st.chat_message("assistant"):
                context = display_df.head(15).to_string()
                summary = f"列名: {list(df.columns)}\n空值: {df.isnull().sum().to_dict()}"
                response = st.write_stream(client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"专家身份。样本：\n{context}\n统计：\n{summary}"},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                ))
            st.session_state.messages.append({"role": "assistant", "content": response})

    with tab_history:
        if st.session_state["history_log"]:
            st.table(pd.DataFrame(st.session_state["history_log"]))
else:
    st.info("👋 演示就绪。请在侧边栏加载演示数据或上传文件。")