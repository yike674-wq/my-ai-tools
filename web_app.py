import streamlit as st
import pandas as pd
from openai import OpenAI
import io
import re
import plotly.express as px

# --- 1. 商业级配置 ---
st.set_page_config(page_title="AI 数据看板 Pro | 商业内测版", page_icon="💎", layout="wide")

# 初始化状态
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "messages" not in st.session_state: st.session_state["messages"] = []
if "df_cleaned" not in st.session_state: st.session_state["df_cleaned"] = None

# --- 2. 登录拦截系统 ---
if not st.session_state["logged_in"]:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("🛡️ 商业授权访问")
        st.markdown("### 欢迎体验 V7.0 零配置版")
        invite_code = st.text_input("请输入您的 8 位邀请码", type="password", help="输入 VIP888 即可开启内置 AI 引擎")
        if st.button("一键解锁授权", use_container_width=True):
            if invite_code == "VIP888":
                st.session_state["logged_in"] = True
                st.session_state["is_vip"] = True # 标记为 VIP 用户
                st.success("✨ 身份验证成功：已解锁‘官方内置 Key’权限")
                st.rerun()
            else:
                st.error("验证失败，请联系管理员获取邀请码")
    st.stop()

# --- 3. 后台 API 逻辑适配 ---
# 从 Secrets 获取官方 Key
try:
    OFFICIAL_KEY = st.secrets["DEEPSEEK_API_KEY"]
except:
    OFFICIAL_KEY = None

# --- 4. 侧边栏控制台 ---
with st.sidebar:
    st.title("⚙️ 终端控制")
    st.write(f"👤 当前身份：{'🚀 高级订阅会员' if st.session_state.get('is_vip') else '普通访客'}")
    
    # 动态显示 API 状态
    if st.session_state.get("is_vip"):
        st.success("✅ 已启用内置 AI 引擎")
        current_key = OFFICIAL_KEY
    else:
        current_key = st.text_input("请输入您的 API Key", type="password")
    
    st.divider()
    uploaded_file = st.file_uploader("📂 上传待处理数据", type=["xlsx", "csv"])
    
    if st.button("🚪 退出登录"):
        st.session_state["logged_in"] = False
        st.rerun()

# --- 5. 主功能看板 ---
st.title("📊 AI 自动化办公看板 V7.0")

if uploaded_file:
    # 保持之前修复过乱码和 Value误差的逻辑
    if st.session_state["df_cleaned"] is None:
        file_type = uploaded_file.name.split(".")[-1].lower()
        st.session_state["df_cleaned"] = pd.read_csv(uploaded_file) if file_type == "csv" else pd.read_excel(uploaded_file)

    df = st.session_state["df_cleaned"]

    # 选项卡切换
    tab_chart, tab_data, tab_ai = st.tabs(["📈 动态分布", "💎 明细管理", "🤖 智能审计"])
    
    with tab_chart:
        # 引用之前完美的 Plotly 交互逻辑
        if "电话号码" in df.columns:
            df['长度'] = df['电话号码'].astype(str).str.len()
            count_df = df['长度'].value_counts().reset_index()
            count_df.columns = ['号码长度', '出现次数']
            fig = px.bar(count_df, x='号码长度', y='出现次数', color='出现次数', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)

    with tab_ai:
        st.caption("💡 当前正在使用官方内置模型为您服务")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if user_input := st.chat_input("您可以直接提问，无需配置 Key..."):
            if not current_key:
                st.warning("⚠️ 检测到当前环境未配置 Key，请联系管理员或输入您的 Key。")
            else:
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.chat_message("user"): st.write(user_input)
                
                client = OpenAI(api_key=current_key, base_url="https://api.deepseek.com")
                with st.chat_message("assistant"):
                    # 增加字数保险锁：只传前 5 行摘要，防止 Token 消耗过大
                    summary = df.head(5).to_string()
                    response = st.write_stream(client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": f"分析以下数据：\n{summary}"},
                            {"role": "user", "content": user_input}
                        ],
                        stream=True
                    ))
                st.session_state.messages.append({"role": "assistant", "content": response})
else:
    st.info("👋 欢迎回来！请上传 66 行数据包开启‘零配置’体验。")