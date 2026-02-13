import streamlit as st
import pandas as pd
from openai import OpenAI
import plotly.express as px
from datetime import datetime
import io

# --- 1. 商业品牌配置 ---
st.set_page_config(page_title="AI 智能审计终端 | 商业演示版", page_icon="🏆", layout="wide")

# 初始化全量状态
for key in ["logged_in", "df_cleaned", "messages", "history_log", "current_file"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ([] if key in ["messages", "history_log"] else None)

# --- 2. 演示专用：内置模拟数据 ---
def load_demo_data():
    data = {
        "姓名": ["张伟", "王芳", "李娜", "刘洋", "陈静"],
        "科室": ["内科", "外科", "内科", "儿科", "外科"],
        "预产期": ["2025-02-09", "2025-03-15", "2025-02-09", "2025-05-20", "2025-02-12"],
        "联系电话": ["13800138000", "13912345678", "13799998888", "13511112222", "18666667777"],
        "金额": [1200, 3500, 800, 2100, 5000]
    }
    return pd.DataFrame(data)

# --- 3. 登录逻辑 ---
if not st.session_state["logged_in"]:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("🛡️ 商业授权访问")
        st.info("💡 演示模式：请输入内测邀请码 VIP888")
        invite = st.text_input("授权密钥", type="password")
        if st.button("解锁完整商业功能", use_container_width=True):
            if invite == "VIP888":
                st.session_state["logged_in"] = True
                st.rerun()
    st.stop()

OFFICIAL_KEY = st.secrets.get("DEEPSEEK_API_KEY")

# --- 4. 侧边栏：演示控制 ---
with st.sidebar:
    st.title("⚙️ 演示控制面板")
    st.success("💎 高级商业授权已激活")
    
    # 隐私保护开关
    privacy_mode = st.toggle("🔒 开启隐私脱敏保护", value=True)
    
    st.divider()
    # 演示核心：一键加载
    if st.button("✨ 一键加载预设演示数据", use_container_width=True):
        st.session_state["df_cleaned"] = load_demo_data()
        st.session_state["current_file"] = "演示样本_预产期分布表.xlsx"
        st.session_state["messages"] = []
        st.session_state["history_log"].insert(0, {"时间": datetime.now().strftime("%H:%M:%S"), "文件名": "演示样本.xlsx", "规模": "5行"})
        st.toast("已加载演示数据！")

    uploaded_file = st.file_uploader("📂 或上传自有业务报表", type=["xlsx", "csv"])
    
    if uploaded_file and uploaded_file.name != st.session_state["current_file"]:
        st.session_state.update({"df_cleaned": None, "messages": [], "current_file": uploaded_file.name})

    if st.button("🚪 安全退出并销毁记忆"):
        st.session_state.clear()
        st.rerun()

# --- 5. 主程序界面 ---
st.title("📊 AI 自动化办公看板 V10.0")

if st.session_state["df_cleaned"] is not None:
    # 如果是上传的文件
    if uploaded_file and st.session_state["df_cleaned"] is None:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        st.session_state["df_cleaned"] = pd.read_csv(uploaded_file) if file_ext == "csv" else pd.read_excel(uploaded_file)
        st.session_state["history_log"].insert(0, {"时间": datetime.now().strftime("%H:%M:%S"), "文件名": uploaded_file.name, "规模": f"{len(st.session_state['df_cleaned'])}行"})

    df = st.session_state["df_cleaned"]
    
    # 顶部指标卡
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("当前数据源", st.session_state["current_file"])
    c2.metric("总记录数", f"{len(df)} 条")
    c3.metric("隐私盾状态", "核心加密" if privacy_mode else "明文模式")
    c4.metric("AI 引擎", "DeepSeek-V3")

    # 找回“记忆”：常驻的 4 个功能标签
    tab_chart, tab_data, tab_ai, tab_history = st.tabs(["📈 数据分布", "💎 明细看板", "🤖 AI 深度审计", "📜 审计流水线"])
    
    with tab_chart:
        cols = df.select_dtypes(include=['object']).columns.tolist()
        if cols:
            target = st.selectbox("选择统计维度", cols)
            fig = px.bar(df[target].value_counts().reset_index(), x='index', y=target, color=target, text_auto=True)
            st.plotly_chart(fig, use_container_width=True)

    with tab_data:
        # 脱敏展示
        display_df = df.copy()
        if privacy_mode:
            for col in display_df.columns:
                if any(x in str(col) for x in ["姓名", "电话", "联系", "名"]):
                    display_df[col] = display_df[col].astype(str).apply(lambda x: x[0] + "*" + x[-1] if len(x)>1 else x)
        st.dataframe(display_df, use_container_width=True)
            with tab_ai:
        st.write("### 🤖 首席 AI 审计官")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if user_input := st.chat_input("您可以提问：例如‘分析下预产期在2月9号的人员比例’"):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.write(user_input)
            
            client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com")
            with st.chat_message("assistant"):
                # 投喂脱敏样本 + 统计摘要
                context = display_df.head(15).to_string()
                summary = f"列名: {list(df.columns)}\n统计: {df.describe(include='all').to_dict()}"
                
                response = st.write_stream(client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"你是一个数据专家。当前数据样本：\n{context}\n全表摘要：\n{summary}"},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                ))
            st.session_state.messages.append({"role": "assistant", "content": response})

    with tab_history:
        st.subheader("📜 历史处理流水线")
        if st.session_state["history_log"]:
            st.table(pd.DataFrame(st.session_state["history_log"]))
            if st.button("🗑️ 清空所有审计足迹"):
                st.session_state["history_log"] = []
                st.rerun()
        else:
            st.info("暂无处理记录")
else:
    st.info("👋 演示准备就绪。请在侧边栏【一键加载演示数据】或手动上传文件。")
    if st.session_state["history_log"]:
        st.write("### 🕒 最近访问记录")
        st.table(pd.DataFrame(st.session_state["history_log"]).head(3))