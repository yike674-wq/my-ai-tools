import streamlit as st
import PyPDF2
import pandas as pd
from openai import OpenAI

# 1. 页面配置
st.set_page_config(page_title="AI 安全全能助手", page_icon="🛡️")
st.title("🛡️ AI 安全全能分析系统")

# 2. 侧边栏：安全配置区
with st.sidebar:
    st.header("🔑 安全配置")
    # 让用户输入自己的 Key，type="password" 会自动把输入内容变成星号
    api_key_input = st.text_input("请输入您的 DeepSeek API Key", type="password")
    
    st.divider() # 分割线
    
    st.header("📁 文件上传")
    uploaded_file = st.file_uploader("支持 PDF, Excel, CSV", type=["pdf", "xlsx", "csv"])

# 3. 核心功能函数（保持不变）
def get_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    return "".join([page.extract_text() or "" for page in reader.pages])

def get_excel_text(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    return f"数据概览：\n{df.head(50).to_markdown()}"

# 4. 关键逻辑：如果没有 Key，则不执行对话
if not api_key_input:
    st.warning("⚠️ 请先在左侧输入您的 DeepSeek API Key，否则无法与 AI 通讯。")
    st.info("您可以从 DeepSeek 官网获取您的密钥。")
else:
    # 只有输入了 Key，才初始化客户端
    client = OpenAI(api_key=api_key_input, base_url="https://api.deepseek.com")

    if uploaded_file:
        with st.spinner("数据读取中..."):
            if uploaded_file.name.endswith(".pdf"):
                context_text = get_pdf_text(uploaded_file)
            else:
                context_text = get_excel_text(uploaded_file)
        
        st.success(f"✅ {uploaded_file.name} 已就绪")

        # 对话显示逻辑
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("针对此文件提问..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": f"你是一个多文档分析专家。文档内容：\n{context_text[:8000]}"},
                            *st.session_state.messages
                        ]
                    )
                    answer = response.choices[0].message.content
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"❌ 通讯失败：请检查您的 API Key 是否正确或余额是否充足。错误信息：{e}")