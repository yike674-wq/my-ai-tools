import streamlit as st
import pandas as pd
from openai import OpenAI
import io
import plotly.express as px
from datetime import datetime

# --- 1. 商业配置 ---
st.set_page_config(page_title="AI 数据看板 Pro | 全能版", page_icon="💎", layout="wide")

# 初始化状态
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "messages" not in st.session_state: st.session_state["messages"] = []
if "df_cleaned" not in st.session_state: st.session_state["df_cleaned"] = None
if "history_log" not in st.session_state: st.session_state["history_log"] = []
if "current_file_name" not in st.session_state: st.session_state["current_file_name"] = ""

# --- 2. 登录拦截 ---
if not st.session_state["logged_in"]:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("🛡️ 商业授权访问")
        invite_code = st.text_input("请输入专属邀请码", type="password")
        if st.button("进入系统", use_container_width=True):
            if invite_code == "VIP888":
                st.session_state["logged_in"] = True
                st.rerun()
    st.stop()

# 从 Secrets 获取官方 Key
OFFICIAL_KEY = st.secrets.get("DEEPSEEK_API_KEY")

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 控制中心")
    st.success("✅ AI 引擎已就绪")
    
    uploaded_file = st.file_uploader("📂 上传任意 Excel/CSV", type=["xlsx", "csv"])
    
    # ✨ 核心修复：检测到新文件则清空旧状态
    if uploaded_file and uploaded_file.name != st.session_state["current_file_name"]:
        st.session_state["df_cleaned"] = None
        st.session_state["messages"] = []
        st.session_state["current_file_name"] = uploaded_file.name

    if st.button("🚪 退出并清理"):
        st.session_state.clear()
        st.rerun()

# --- 4. 主程序 ---
st.title("📊 AI 自动化办公看板 V8.1")

if uploaded_file:
    if st.session_state["df_cleaned"] is None:
        file_type = uploaded_file.name.split(".")[-1].lower()
        df = pd.read_csv(uploaded_file) if file_type == "csv" else pd.read_excel(uploaded_file)
        st.session_state["df_cleaned"] = df
        
        # 记录历史
        st.session_state["history_log"].insert(0, {
            "时间": datetime.now().strftime("%H:%M:%S"),
            "文件名": uploaded_file.name,
            "行数": len(df)
        })

    df = st.session_state["df_cleaned"]
    
    # 顶部指标
    st.info(f"📁 当前处理：{uploaded_file.name} | 共 {len(df)} 行数据")

    tab_chart, tab_data, tab_ai = st.tabs(["📈 数据智能分布", "💎 明细预览", "🤖 AI 深度对话"])
    
    with tab_chart:
        # ✨ 自动适配：不再只查电话，而是显示前两个分类列的分布
        cat_cols = df.select_dtypes(include=['object']).columns
        if len(cat_cols) > 0:
            target_col = st.selectbox("选择要分析的维度", cat_cols)
            fig = px.bar(df[target_col].value_counts().reset_index(), x='index', y=target_col, 
                         labels={'index':target_col, target_col:'数量'}, title=f"{target_col} 分布图")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("未检测到可分类的数据列。")

    with tab_data:
        st.dataframe(df, use_container_width=True)

    with tab_ai:
        st.caption("🤖 AI 已加载此表格，您可以询问任何关于预产期、姓名或金额的问题。")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if user_input := st.chat_input("例如：帮我找出 2025/2/9 预产期的名单"):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.write(user_input)
            
            client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com")
            with st.chat_message("assistant"):
                # ✨ 核心修复：把完整的表格数据（前 20 行）作为背景知识传给 AI
                data_context = df.head(20).to_string()
                response = st.write_stream(client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"你是一个数据专家。这是用户上传的表格前20行数据：\n{data_context}\n请基于此回答用户。"},
                        {"role": "user", "content": user_input}
                    ],
                    stream=True
                ))
            st.session_state.messages.append({"role": "assistant", "content": response})
else:
    st.info("👋 请上传您的业务报表（支持预产期、财务、考勤等多种表格）")