import streamlit as st
import pandas as pd
from openai import OpenAI
import io
import re
import plotly.express as px

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI 自动化办公终端 | 商业版", page_icon="🔑", layout="wide")

# --- 2. 核心：商业授权逻辑 ---
# 在真正的商业版中，这些账号会存在数据库里。现在我们先做一个“内测邀请码”逻辑。
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        # 居中显示的登录界面
        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.title("🔐 商业授权登录")
            st.info("欢迎使用内测版，请输入您的专属邀请码开启终端")
            user_code = st.text_input("内测邀请码", type="password")
            if st.button("立即进入终端"):
                if user_code == "VIP888":  # 这里是你设置的第一个“收钱码”
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("邀请码无效，请联系管理员获取")
        return False
    return True

# --- 3. 如果通过登录，展示主程序 ---
if check_login():
    # 初始化
    if "messages" not in st.session_state: st.session_state["messages"] = []
    if "df_cleaned" not in st.session_state: st.session_state["df_cleaned"] = None

    # 侧边栏
    with st.sidebar:
        st.title("⚙️ 终端控制台")
        st.write(f"👤 当前状态：高级订阅会员")
        if st.button("退出登录"):
            st.session_state["logged_in"] = False
            st.rerun()
        
        st.divider()
        api_key = st.text_input("API Key (开发者模式)", type="password")
        uploaded_file = st.file_uploader("上传 Excel/CSV", type=["xlsx", "csv"])
        
        if st.session_state["df_cleaned"] is not None:
            if st.button("🚀 强制规范号码格式"):
                df = st.session_state["df_cleaned"]
                if "电话号码" in df.columns:
                    df["电话号码"] = df["电话号码"].astype(str).apply(lambda x: re.sub(r'\D', '', x))
                    st.session_state["df_cleaned"] = df
                    st.toast("格式修复成功！")

    # 主看板界面 (保持之前的完美 V5.2 逻辑)
    st.title("📊 AI 自动化办公看板 V6.0")
    
    if uploaded_file:
        if st.session_state["df_cleaned"] is None:
            file_type = uploaded_file.name.split(".")[-1].lower()
            st.session_state["df_cleaned"] = pd.read_csv(uploaded_file) if file_type == "csv" else pd.read_excel(uploaded_file)

        df = st.session_state["df_cleaned"]

        # 指标卡与选项卡逻辑...
        c1, c2, c3 = st.columns(3)
        c1.metric("记录总数", f"{len(df)} 行")
        bad_count = len(df[df["电话号码"].astype(str).str.len() != 11]) if "电话号码" in df.columns else 0
        c2.metric("异常监测", f"{bad_count} 项", delta=f"-{bad_count}" if bad_count > 0 else "已达标")
        c3.metric("处理引擎", "DeepSeek-V3 (已授权)")

        tab_chart, tab_data, tab_ai = st.tabs(["📈 动态分布分析", "💎 数据明细管理", "🤖 AI 专家解读"])
        
        with tab_chart:
            if "电话号码" in df.columns:
                df['长度'] = df['电话号码'].astype(str).str.len()
                count_df = df['长度'].value_counts().reset_index()
                count_df.columns = ['号码长度', '出现次数']
                fig = px.bar(count_df, x='号码长度', y='出现次数', color='出现次数', text_auto=True)
                st.plotly_chart(fig, use_container_width=True)

        with tab_data:
            st.dataframe(df, use_container_width=True)
            # 这里可以加个“商业水印”导出
            st.download_button("📥 导出审计后的数据", data=io.BytesIO().getvalue(), file_name="Pro_Data.xlsx")

        with tab_ai:
            for msg in st.session_state["messages"]:
                with st.chat_message(msg["role"]): st.write(msg["content"])
            if user_input := st.chat_input("作为 VIP 会员，您可以无限次询问..."):
                if not api_key: st.warning("请配置 API Key")
                else:
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    with st.chat_message("user"): st.write(user_input)
                    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                    with st.chat_message("assistant"):
                        response = st.write_stream(client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "system", "content": "数据专家"}, {"role": "user", "content": user_input}],
                            stream=True
                        ))
                    st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.info("👋 欢迎进入商业版！请在左侧上传数据开始工作。")