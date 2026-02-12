import streamlit as st
import pandas as pd
from openai import OpenAI
import plotly.express as px
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI 数据看板 Pro | 旗舰版", page_icon="💎", layout="wide")

# 初始化所有状态
for key in ["logged_in", "messages", "df_cleaned", "history_log", "current_file"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ([] if key in ["messages", "history_log"] else None)

# --- 2. 登录系统 ---
if not st.session_state["logged_in"]:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("🛡️ 商业版安全登录")
        invite = st.text_input("请输入邀请码", type="password")
        if st.button("解锁进入"):
            if invite == "VIP888":
                st.session_state["logged_in"] = True
                st.rerun()
    st.stop()

# 获取 Secrets
OFFICIAL_KEY = st.secrets.get("DEEPSEEK_API_KEY")

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 控制中心")
    st.success("✅ AI 引擎已就绪")
    uploaded_file = st.file_uploader("📂 上传任意表格", type=["xlsx", "csv"])
    
    # ✨ 核心修复：文件切换即清理旧记忆
    if uploaded_file and uploaded_file.name != st.session_state["current_file"]:
        st.session_state["df_cleaned"] = None
        st.session_state["messages"] = []
        st.session_state["current_file"] = uploaded_file.name

    if st.button("🚪 退出并清理"):
        st.session_state.clear()
        st.rerun()

# --- 4. 主看板 ---
st.title("📊 AI 自动化办公看板 V8.2")

if uploaded_file:
    if st.session_state["df_cleaned"] is None:
        try:
            file_type = uploaded_file.name.split(".")[-1].lower()
            df = pd.read_csv(uploaded_file) if file_type == "csv" else pd.read_excel(uploaded_file)
            st.session_state["df_cleaned"] = df
            st.session_state["history_log"].insert(0, {"时间": datetime.now().strftime("%H:%M:%S"), "文件名": uploaded_file.name})
        except Exception as e:
            st.error(f"解析失败: {e}")
            st.stop()

    df = st.session_state["df_cleaned"]
    st.info(f"📁 已加载：{uploaded_file.name} | 数据量：{len(df)} 行")

    tab_chart, tab_data, tab_ai = st.tabs(["📈 动态分布", "💎 数据明细", "🤖 AI 深度审计"])
    
    with tab_chart:
        # ✨ 健壮绘图逻辑：自动适配任何表格的分类列
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        if cat_cols:
            target = st.selectbox("请选择要分析的维度", cat_cols)
            # 使用更通用的绘图方式，避开 labels 命名陷阱
            plot_data = df[target].value_counts().reset_index()
            plot_data.columns = [target, '数量']
            fig = px.bar(plot_data, x=target, y='数量', color='数量', title=f"{target} 数据分布")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("表格中没有可供分析的文字列。")

    with tab_data:
        st.dataframe(df, use_container_width=True)

    with tab_ai:
        st.write("🤖 AI 专家已入驻，请针对当前表格提问：")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if user_input := st.chat_input("帮我统计一下 2月9号 预产期的人名单"):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.write(user_input)
            
            client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com")
            with st.chat_message("assistant"):
                # ✨ 核心修复：确保数据摘要被正确喂给 AI
                context = df.to_string(max_rows=15, max_cols=10) 
                response = st.write_stream(client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"你是一个数据专家。当前表格内容摘要如下：\n{context}\n请基于此回答。"},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                ))
            st.session_state.messages.append({"role": "assistant", "content": response})
else:
    st.info("👋 请在左侧上传您的业务报表开始工作。")