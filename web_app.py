import streamlit as st
import pandas as pd
from openai import OpenAI
import io
import re
import plotly.express as px
from datetime import datetime

# --- 1. 商业级配置 ---
st.set_page_config(page_title="AI 数据看板 Pro | 商业版", page_icon="💎", layout="wide")

# 初始化核心状态
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "messages" not in st.session_state: st.session_state["messages"] = []
if "df_cleaned" not in st.session_state: st.session_state["df_cleaned"] = None
# 新增：处理历史记录
if "history_log" not in st.session_state: st.session_state["history_log"] = []

# --- 2. 登录拦截系统 ---
if not st.session_state["logged_in"]:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("🛡️ 商业授权访问")
        invite_code = st.text_input("请输入您的专属邀请码", type="password")
        if st.button("一键解锁授权", use_container_width=True):
            if invite_code == "VIP888":
                st.session_state["logged_in"] = True
                st.session_state["is_vip"] = True
                st.rerun()
            else:
                st.error("验证失败")
    st.stop()

# 从 Secrets 获取官方 Key
OFFICIAL_KEY = st.secrets.get("DEEPSEEK_API_KEY")

# --- 3. 侧边栏控制台 ---
with st.sidebar:
    st.title("⚙️ 终端控制")
    st.write(f"👤 身份：高级订阅会员")
    st.success("✅ 已启用内置 AI 引擎")
    
    st.divider()
    uploaded_file = st.file_uploader("📂 上传待处理数据", type=["xlsx", "csv"])
    
    # 退出登录
    if st.button("🚪 退出系统"):
        st.session_state["logged_in"] = False
        st.rerun()

# --- 4. 主功能看板 ---
st.title("📊 AI 自动化办公看板 V8.0")

if uploaded_file:
    # 首次加载文件并记录历史
    if st.session_state["df_cleaned"] is None:
        file_type = uploaded_file.name.split(".")[-1].lower()
        df = pd.read_csv(uploaded_file) if file_type == "csv" else pd.read_excel(uploaded_file)
        st.session_state["df_cleaned"] = df
        
        # --- ✨ 记录历史逻辑 ---
        new_log = {
            "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "文件名": uploaded_file.name,
            "行数": len(df),
            "状态": "处理完成"
        }
        st.session_state["history_log"].insert(0, new_log) # 新记录排在最前
        st.toast(f"成功导入 {uploaded_file.name}")

    df = st.session_state["df_cleaned"]

    # 选项卡切换：增加“历史清单”
    tab_chart, tab_data, tab_ai, tab_history = st.tabs(["📈 动态分布", "💎 明细管理", "🤖 智能审计", "📜 处理记录"])
    
    with tab_chart:
        if "电话号码" in df.columns:
            df['长度'] = df['电话号码'].astype(str).str.len()
            count_df = df['长度'].value_counts().reset_index()
            count_df.columns = ['号码长度', '出现次数']
            fig = px.bar(count_df, x='号码长度', y='出现次数', color='出现次数', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)

    with tab_ai:
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        if user_input := st.chat_input("询问关于这份数据的问题..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.write(user_input)
            client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com")
            with st.chat_message("assistant"):
                response = st.write_stream(client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": "数据专家"}, {"role": "user", "content": user_input}],
                    stream=True
                ))
            st.session_state.messages.append({"role": "assistant", "content": response})

    with tab_history:
        st.subheader("📜 历史处理清单")
        if st.session_state["history_log"]:
            history_df = pd.DataFrame(st.session_state["history_log"])
            st.table(history_df) # 使用表格展示，更具商务感
            if st.button("🗑️ 清空历史记录"):
                st.session_state["history_log"] = []
                st.rerun()
        else:
            st.info("暂无处理记录")
else:
    # 未上传文件时，也可以查看历史记录（如果之前处理过）
    if st.session_state["history_log"]:
        st.info("👋 欢迎回来！您之前处理过以下文件：")
        st.table(pd.DataFrame(st.session_state["history_log"]).head(3))
    else:
        st.info("👋 准备就绪，请上传数据文件开始工作。")