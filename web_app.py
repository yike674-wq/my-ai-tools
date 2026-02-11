import streamlit as st
import pandas as pd
from openai import OpenAI
import io
import re
import plotly.express as px

# --- 1. 配置 ---
st.set_page_config(page_title="AI 自动化办公终端 Pro", page_icon="🦾", layout="wide")
st.markdown('<meta charset="utf-8">', unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state["messages"] = []
if "df_cleaned" not in st.session_state: st.session_state["df_cleaned"] = None

# --- 2. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 终端控制台")
    api_key = st.text_input("API Key", type="password")
    uploaded_file = st.file_uploader("上传 Excel/CSV", type=["xlsx", "csv"])
    
    if st.session_state["df_cleaned"] is not None:
        st.divider()
        if st.button("🚀 强制规范号码格式"):
            df = st.session_state["df_cleaned"]
            if "电话号码" in df.columns:
                df["电话号码"] = df["电话号码"].astype(str).apply(lambda x: re.sub(r'\D', '', x))
                st.session_state["df_cleaned"] = df
                st.toast("格式已优化！")

# --- 3. 主界面 ---
st.title("📊 AI 自动化办公看板 V5.2")

if uploaded_file:
    if st.session_state["df_cleaned"] is None:
        file_type = uploaded_file.name.split(".")[-1].lower()
        st.session_state["df_cleaned"] = pd.read_csv(uploaded_file) if file_type == "csv" else pd.read_excel(uploaded_file)

    df = st.session_state["df_cleaned"]

    # 指标卡
    c1, c2, c3 = st.columns(3)
    c1.metric("记录总数", f"{len(df)} 行")
    bad_count = len(df[df["电话号码"].astype(str).str.len() != 11]) if "电话号码" in df.columns else 0
    c2.metric("异常监测", f"{bad_count} 项", delta=f"-{bad_count}" if bad_count > 0 else "已达标")
    c3.metric("处理引擎", "DeepSeek-V3")

    # 选项卡
    tab_chart, tab_data, tab_ai = st.tabs(["📈 动态分布分析", "💎 数据明细管理", "🤖 AI 专家解读"])
    
    with tab_chart:
        if "电话号码" in df.columns:
            st.subheader("号码长度分布（交互式）")
            # --- ✨ 修复 ValueError 的核心逻辑 ---
            df['长度'] = df['电话号码'].astype(str).str.len()
            # 强制将统计结果转为 DataFrame 并手动命名列名
            count_df = df['长度'].value_counts().reset_index()
            count_df.columns = ['号码长度', '出现次数'] # 统一命名，不让系统乱猜
            
            # 使用我们自己命名的列绘图
            fig = px.bar(count_df, x='号码长度', y='出现次数', color='出现次数', 
                         color_continuous_scale='Viridis', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("表格中缺少‘电话号码’列，无法生成图表。")

    with tab_data:
        st.dataframe(df, use_container_width=True)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 导出审计后的数据", data=buffer.getvalue(), file_name="Audited_Data.xlsx")

    with tab_ai:
        st.caption("🤖 请在此输入问题，AI 将结合上方数据进行回答。")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        # 确保 chat_input 在 tab 内，避免消失
        if user_input := st.chat_input("问问 AI 这一行数据有什么问题？"):
            if not api_key:
                st.warning("请在左侧输入 API Key。")
            else:
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.chat_message("user"): st.write(user_input)
                
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                with st.chat_message("assistant"):
                    response = st.write_stream(client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": f"数据摘要：\n{df.head(10).to_string()}"},
                            {"role": "user", "content": user_input}
                        ],
                        stream=True
                    ))
                st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.info("👋 欢迎回来！请上传文件以恢复分析看板。")