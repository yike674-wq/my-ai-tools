import streamlit as st
import pandas as pd

from PyPDF2 import PdfReader

from openai import OpenAI

import io
# --- 1. 页面高级配置 ---
st.set_page_config(
    page_title="AI 数据看板 Pro", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 样式，让界面更有质感
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_index=True)

# --- 2. 初始化记忆 ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --- 3. 侧边栏（精简版） ---
with st.sidebar:
    st.title("🚀 控制中心")
    api_key = st.text_input("DeepSeek API Key", type="password", help="在此输入您的密钥以启用 AI")
    
    st.divider()
    st.subheader("📁 上传区域")
    uploaded_file = st.file_uploader("选择 Excel, CSV 或 PDF", type=["pdf", "xlsx", "csv"])
    
    if uploaded_file:
        st.success(f"已加载: {uploaded_file.name}")
    
    st.divider()
    st.info("💡 提示：今日已开启“高级看板”布局模式。")

# --- 4. 主界面：顶部标题与指标 ---
st.title("📊 AI 智能数据分析看板")
st.caption("专业的 AI 数据审计与可视化分析平台")

file_content = ""
df = None

if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()
    try:
        if file_type == "pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                text = page.extract_text()
                if text: file_content += text + "\n"
        elif file_type in ["xlsx", "xls", "csv"]:
            df = pd.read_csv(uploaded_file) if file_type == "csv" else pd.read_excel(uploaded_file)
            file_content = df.to_string()

        # --- ✨ 亮点：指标卡展示区 ---
        if df is not None:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总记录数", f"{len(df)} 行")
            with col2:
                # 简单逻辑模拟异常数（比如检查号码长度不为11位的）
                anomalies = 0
                if "电话号码" in df.columns:
                    anomalies = len(df[df["电话号码"].astype(str).str.len() != 11])
                st.metric("疑似异常", f"{anomalies} 项", delta="-1" if anomalies > 0 else "0", delta_color="inverse")
            with col3:
                st.metric("分析状态", "就绪", delta="Ready")

            # --- ✨ 亮点：选项卡展示区 ---
            tab1, tab2 = st.tabs(["📄 数据预览与下载", "📈 数据分布图"])
            
            with tab1:
                st.dataframe(df, use_container_width=True, height=250)
                # 下载按钮（昨天掌握的神技）
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(
                    label="📥 导出当前分析结果",
                    data=buffer.getvalue(),
                    file_name=f"processed_{uploaded_file.name}",
                    mime="application/vnd.ms-excel"
                )

            with tab2:
                if "电话号码" in df.columns:
                    st.write("号码归属分布（模拟演示）")
                    # 创建一个简单的长度分布图
                    df['len'] = df['电话号码'].astype(str).str.len()
                    len_dist = df['len'].value_counts()
                    st.bar_chart(len_dist)
                else:
                    st.warning("当前表格暂无可生成图表的字段。")

    except Exception as e:
        st.error(f"解析出错: {e}")

# --- 5. 聊天界面（右侧分栏或底部） ---
st.divider()
st.subheader("💬 AI 智能助手对话")

# 展示对话历史
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if not api_key:
    st.warning("👈 请先在侧边栏配置 API Key")
    st.stop()

user_input = st.chat_input("输入分析指令，例如：请给我这份数据的体检报告...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    system_prompt = """
    你是一位资深数据科学家，擅长使用图表和专业术语分析数据。
    你的任务是协助用户发现数据价值。
    请始终以专业、有洞察力的语气回答，并尽量使用 Markdown 表格。
    """
    final_prompt = f"数据内容：\n{file_content[:30000]}\n\n指令：{user_input}" if file_content else user_input

    try:
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": final_prompt}],
                stream=True
            )
            response = st.write_stream(stream)
        st.session_state["messages"].append({"role": "assistant", "content": response})
    except Exception as e:
        st.error(f"AI 连接中断: {e}")